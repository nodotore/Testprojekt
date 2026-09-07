"""Secret-Management für API-Schlüssel (Auftrag §2, §12; siehe DECISIONS.md ADR-5).

Zwei Implementierungen hinter einer gemeinsamen Schnittstelle:

- ``KeyringSecretStore``: primärer Weg, nutzt das Betriebssystem-Keyring
  (unter Windows: Windows Credential Manager über das ``keyring``-Paket).
- ``EncryptedFileSecretStore``: Fallback, falls kein OS-Keyring verfügbar
  ist (z. B. manche Server-/CI-Umgebungen). Der Verschlüsselungsschlüssel
  wird per PBKDF2HMAC aus einem vom Nutzer gesetzten Master-Passwort
  abgeleitet; weder Master-Passwort noch abgeleiteter Schlüssel werden
  jemals im Klartext auf Platte gespeichert.

Secrets werden NIE geloggt. Aufrufer dürfen Rückgabewerte dieses Moduls
nicht an das Logging-System übergeben (siehe ``investment_analyzer.audit``
für den Redaction-Filter, der dies zusätzlich absichert).
"""

from __future__ import annotations

import base64
import contextlib
import json
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict

if TYPE_CHECKING:
    from cryptography.fernet import Fernet


class _SecretContainer(TypedDict):
    """Struktur der verschlüsselten Secrets-Datei (Klartext-Hülle, Werte selbst verschlüsselt)."""

    salt: str
    secrets: dict[str, str]


class SecretStoreUnavailableError(RuntimeError):
    """Ausgelöst, wenn ein Secret-Store-Backend nicht nutzbar ist (z. B. kein OS-Keyring)."""


class KeyringModuleProtocol(Protocol):
    """Minimale Schnittstelle des ``keyring``-Pakets, zum Testen austauschbar."""

    def get_password(self, service_name: str, username: str) -> str | None: ...

    def set_password(self, service_name: str, username: str, password: str) -> None: ...

    def delete_password(self, service_name: str, username: str) -> None: ...


class SecretStore(ABC):
    """Abstrakte Schnittstelle für die Speicherung von API-Schlüsseln u. Ä."""

    @abstractmethod
    def get_secret(self, name: str) -> str | None:
        """Liefert das Secret oder ``None``, falls nicht vorhanden."""

    @abstractmethod
    def set_secret(self, name: str, value: str) -> None:
        """Speichert (überschreibt) ein Secret."""

    @abstractmethod
    def delete_secret(self, name: str) -> None:
        """Löscht ein Secret, falls vorhanden (kein Fehler, falls nicht vorhanden)."""


class KeyringSecretStore(SecretStore):
    """Speichert Secrets im Betriebssystem-Keyring unter einem festen Service-Namen."""

    def __init__(self, keyring_module: KeyringModuleProtocol, service_name: str) -> None:
        self._keyring = keyring_module
        self._service_name = service_name

    def get_secret(self, name: str) -> str | None:
        try:
            return self._keyring.get_password(self._service_name, name)
        except Exception as exc:  # Backend nicht verfügbar o. Ä.
            raise SecretStoreUnavailableError(str(exc)) from exc

    def set_secret(self, name: str, value: str) -> None:
        try:
            self._keyring.set_password(self._service_name, name, value)
        except Exception as exc:
            raise SecretStoreUnavailableError(str(exc)) from exc

    def delete_secret(self, name: str) -> None:
        # Löschen eines nicht vorhandenen Secrets ist kein Fehler.
        with contextlib.suppress(Exception):
            self._keyring.delete_password(self._service_name, name)

    def smoke_test(self) -> bool:
        """Prüft, ob das Keyring-Backend tatsächlich funktioniert (Roundtrip)."""

        probe_name = "__investment_analyzer_probe__"
        try:
            self.set_secret(probe_name, "ok")
            ok = self.get_secret(probe_name) == "ok"
            self.delete_secret(probe_name)
            return ok
        except SecretStoreUnavailableError:
            return False


class EncryptedFileSecretStore(SecretStore):
    """Fallback: Secrets AES-verschlüsselt (Fernet) in einer JSON-Datei.

    Der Schlüssel wird niemals gespeichert; er wird bei jedem Programmstart
    aus dem vom Nutzer eingegebenen Master-Passwort neu abgeleitet (PBKDF2,
    Salt wird in der Datei mitgespeichert, da ein Salt kein Geheimnis ist).
    """

    _KDF_ITERATIONS = 390_000

    def __init__(self, path: Path, master_password: str) -> None:
        self._path = path
        self._master_password = master_password

    def _load_container(self) -> _SecretContainer:
        if not self._path.exists():
            return {"salt": base64.urlsafe_b64encode(os.urandom(16)).decode("ascii"), "secrets": {}}
        return json.loads(self._path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]

    def _derive_key(self, salt_b64: str) -> bytes:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        salt = base64.urlsafe_b64decode(salt_b64)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=self._KDF_ITERATIONS
        )
        return base64.urlsafe_b64encode(kdf.derive(self._master_password.encode("utf-8")))

    def _fernet(self, salt_b64: str) -> Fernet:
        from cryptography.fernet import Fernet

        return Fernet(self._derive_key(salt_b64))

    def _write_container(self, container: _SecretContainer) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self._path.parent), prefix=".secrets-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(container, tmp_file)
            os.replace(tmp_name, self._path)
            os.chmod(self._path, 0o600)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def get_secret(self, name: str) -> str | None:
        container = self._load_container()
        encrypted = container["secrets"].get(name)
        if encrypted is None:
            return None
        fernet = self._fernet(container["salt"])
        return fernet.decrypt(encrypted.encode("ascii")).decode("utf-8")

    def set_secret(self, name: str, value: str) -> None:
        container = self._load_container()
        fernet = self._fernet(container["salt"])
        container["secrets"][name] = fernet.encrypt(value.encode("utf-8")).decode("ascii")
        self._write_container(container)

    def delete_secret(self, name: str) -> None:
        container = self._load_container()
        if name in container["secrets"]:
            del container["secrets"][name]
            self._write_container(container)


def get_secret_store(
    *,
    path: Path,
    master_password: str | None = None,
    service_name: str = "investment-analyzer",
) -> SecretStore:
    """Wählt automatisch das beste verfügbare Backend (ADR-5).

    Reihenfolge: OS-Keyring (per Smoke-Test geprüft) → verschlüsselte Datei,
    falls ein Master-Passwort übergeben wurde. Ist keines der beiden nutzbar,
    wird ``SecretStoreUnavailableError`` ausgelöst — es gibt bewusst KEINEN
    unverschlüsselten Klartext-Fallback (Auftrag §2, §12).
    """

    try:
        import keyring as keyring_module

        candidate = KeyringSecretStore(keyring_module, service_name)
        if candidate.smoke_test():
            return candidate
    except Exception:
        pass

    if master_password:
        return EncryptedFileSecretStore(path, master_password)

    raise SecretStoreUnavailableError(
        "Kein OS-Keyring verfügbar und kein Master-Passwort für den "
        "verschlüsselten Datei-Fallback angegeben."
    )
