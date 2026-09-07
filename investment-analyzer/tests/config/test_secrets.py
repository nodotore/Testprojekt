from __future__ import annotations

from pathlib import Path

import pytest

from investment_analyzer.config.secrets import (
    EncryptedFileSecretStore,
    KeyringSecretStore,
    SecretStoreUnavailableError,
    get_secret_store,
)


class FakeKeyring:
    """In-Memory-Doppelgänger des ``keyring``-Pakets für Tests."""

    def __init__(self, *, raise_on_use: bool = False) -> None:
        self._store: dict[tuple[str, str], str] = {}
        self._raise_on_use = raise_on_use

    def get_password(self, service_name: str, username: str) -> str | None:
        if self._raise_on_use:
            raise RuntimeError("kein Backend verfügbar")
        return self._store.get((service_name, username))

    def set_password(self, service_name: str, username: str, password: str) -> None:
        if self._raise_on_use:
            raise RuntimeError("kein Backend verfügbar")
        self._store[(service_name, username)] = password

    def delete_password(self, service_name: str, username: str) -> None:
        if self._raise_on_use:
            raise RuntimeError("kein Backend verfügbar")
        self._store.pop((service_name, username), None)


def test_keyring_store_roundtrip() -> None:
    store = KeyringSecretStore(FakeKeyring(), service_name="investment-analyzer")
    assert store.get_secret("alpha_vantage") is None

    store.set_secret("alpha_vantage", "geheim-123")
    assert store.get_secret("alpha_vantage") == "geheim-123"

    store.delete_secret("alpha_vantage")
    assert store.get_secret("alpha_vantage") is None


def test_keyring_store_wirft_bei_backend_fehler() -> None:
    store = KeyringSecretStore(FakeKeyring(raise_on_use=True), service_name="x")
    with pytest.raises(SecretStoreUnavailableError):
        store.get_secret("foo")


def test_keyring_smoke_test_erkennt_defektes_backend() -> None:
    store = KeyringSecretStore(FakeKeyring(raise_on_use=True), service_name="x")
    assert store.smoke_test() is False


def test_keyring_smoke_test_erkennt_funktionierendes_backend() -> None:
    store = KeyringSecretStore(FakeKeyring(), service_name="x")
    assert store.smoke_test() is True
    # Smoke-Test-Sonde darf keine Spuren hinterlassen:
    assert store.get_secret("__investment_analyzer_probe__") is None


def test_encrypted_file_store_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "secrets.enc.json"
    store = EncryptedFileSecretStore(path, master_password="korrekt-pferd-batterie")

    assert store.get_secret("sec_edgar") is None
    store.set_secret("sec_edgar", "kontakt@example.com")
    assert store.get_secret("sec_edgar") == "kontakt@example.com"

    store.set_secret("alpha_vantage", "abcd1234")
    store.delete_secret("sec_edgar")
    assert store.get_secret("sec_edgar") is None
    assert store.get_secret("alpha_vantage") == "abcd1234"


def test_encrypted_file_store_datei_enthaelt_keinen_klartext(tmp_path: Path) -> None:
    path = tmp_path / "secrets.enc.json"
    store = EncryptedFileSecretStore(path, master_password="pw")
    store.set_secret("api_key", "SUPER-GEHEIMER-WERT")

    raw = path.read_text(encoding="utf-8")
    assert "SUPER-GEHEIMER-WERT" not in raw


def test_encrypted_file_store_falsches_passwort_schlaegt_fehl(tmp_path: Path) -> None:
    from cryptography.fernet import InvalidToken

    path = tmp_path / "secrets.enc.json"
    EncryptedFileSecretStore(path, master_password="richtig").set_secret("k", "v")

    falsch = EncryptedFileSecretStore(path, master_password="falsch")
    with pytest.raises(InvalidToken):
        falsch.get_secret("k")


def test_get_secret_store_ohne_keyring_und_ohne_passwort_wirft(tmp_path: Path) -> None:
    # In der Sandbox-/CI-Umgebung ist i. d. R. kein OS-Keyring-Backend
    # verfügbar; ohne Master-Passwort darf es dann KEINEN stillen
    # Klartext-Fallback geben (Auftrag §2, §12).
    with pytest.raises(SecretStoreUnavailableError):
        get_secret_store(path=tmp_path / "secrets.enc.json", master_password=None)


def test_get_secret_store_faellt_auf_verschluesselte_datei_zurueck(tmp_path: Path) -> None:
    store = get_secret_store(
        path=tmp_path / "secrets.enc.json", master_password="mein-master-passwort"
    )
    store.set_secret("k", "v")
    assert store.get_secret("k") == "v"
