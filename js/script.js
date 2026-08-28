"use strict";

/**
 * Nordlicht Studio - script.js
 * Enthält: Hamburger-Menü, Dropdown-Menü (Maus + Tastatur),
 * sowie clientseitige Validierung des Kontaktformulars.
 * Kein Inline-JavaScript, ausschließlich Event-Listener.
 */

document.addEventListener("DOMContentLoaded", function () {
  initMobileNav();
  initDropdown();
  initContactForm();
});

/* ==========================================================================
   Mobiles Hamburger-Menü
   ========================================================================== */

function initMobileNav() {
  var toggle = document.getElementById("nav-toggle");
  var nav = document.getElementById("primary-nav");

  if (!toggle || !nav) {
    return;
  }

  toggle.addEventListener("click", function () {
    var isOpen = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  // Menü schließen, wenn ein Link innerhalb der Navigation angeklickt wird
  // (relevant für die mobile Ansicht).
  nav.addEventListener("click", function (event) {
    var target = event.target;
    if (target.tagName === "A" && nav.classList.contains("is-open")) {
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });

  // Bei Wechsel auf breite Ansicht sicherstellen, dass das mobile Menü
  // nicht "offen hängen bleibt".
  window.addEventListener("resize", function () {
    if (window.innerWidth > 600 && nav.classList.contains("is-open")) {
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
}

/* ==========================================================================
   Dropdown-Menü "Leistungen" (Maus- und Tastaturbedienung)
   ========================================================================== */

function initDropdown() {
  var dropdownToggle = document.getElementById("dropdown-toggle");
  var dropdownMenu = document.getElementById("dropdown-menu");

  if (!dropdownToggle || !dropdownMenu) {
    return;
  }

  function openDropdown() {
    dropdownMenu.classList.add("is-open");
    dropdownToggle.setAttribute("aria-expanded", "true");
  }

  function closeDropdown() {
    dropdownMenu.classList.remove("is-open");
    dropdownToggle.setAttribute("aria-expanded", "false");
  }

  function toggleDropdown() {
    var isOpen = dropdownMenu.classList.contains("is-open");
    if (isOpen) {
      closeDropdown();
    } else {
      openDropdown();
    }
  }

  dropdownToggle.addEventListener("click", function (event) {
    event.stopPropagation();
    toggleDropdown();
  });

  // Tastaturbedienung: Escape schließt das Dropdown und setzt den Fokus
  // zurück auf den Toggle-Button.
  dropdownToggle.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeDropdown();
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      openDropdown();
      var firstLink = dropdownMenu.querySelector("a");
      if (firstLink) {
        firstLink.focus();
      }
    }
  });

  dropdownMenu.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeDropdown();
      dropdownToggle.focus();
    }
  });

  // Außerhalb des Dropdowns klicken schließt es wieder.
  document.addEventListener("click", function (event) {
    if (!dropdownMenu.classList.contains("is-open")) {
      return;
    }
    var isClickInside = dropdownToggle.contains(event.target) || dropdownMenu.contains(event.target);
    if (!isClickInside) {
      closeDropdown();
    }
  });

  // Fokus verlässt das Dropdown komplett -> schließen.
  document.addEventListener("focusin", function (event) {
    var isFocusInside = dropdownToggle.contains(event.target) || dropdownMenu.contains(event.target);
    if (!isFocusInside) {
      closeDropdown();
    }
  });
}

/* ==========================================================================
   Kontaktformular: Validierung + simulierte Erfolgsmeldung
   ========================================================================== */

function initContactForm() {
  var form = document.getElementById("contact-form");

  if (!form) {
    return;
  }

  var nameField = document.getElementById("name");
  var emailField = document.getElementById("email");
  var messageField = document.getElementById("message");
  var successBox = document.getElementById("form-success");

  var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function setFieldError(field, errorElement, message) {
    if (message) {
      field.setAttribute("aria-invalid", "true");
      errorElement.textContent = message;
    } else {
      field.removeAttribute("aria-invalid");
      errorElement.textContent = "";
    }
  }

  function validateName() {
    var value = nameField.value.trim();
    var errorElement = document.getElementById("name-error");
    if (value === "") {
      setFieldError(nameField, errorElement, "Bitte geben Sie Ihren Namen ein.");
      return false;
    }
    setFieldError(nameField, errorElement, "");
    return true;
  }

  function validateEmail() {
    var value = emailField.value.trim();
    var errorElement = document.getElementById("email-error");
    if (value === "") {
      setFieldError(emailField, errorElement, "Bitte geben Sie Ihre E-Mail-Adresse ein.");
      return false;
    }
    if (!emailPattern.test(value)) {
      setFieldError(emailField, errorElement, "Bitte geben Sie eine gültige E-Mail-Adresse ein.");
      return false;
    }
    setFieldError(emailField, errorElement, "");
    return true;
  }

  function validateMessage() {
    var value = messageField.value.trim();
    var errorElement = document.getElementById("message-error");
    if (value === "") {
      setFieldError(messageField, errorElement, "Bitte geben Sie eine Nachricht ein.");
      return false;
    }
    setFieldError(messageField, errorElement, "");
    return true;
  }

  // Live-Validierung bei Verlassen des Feldes
  nameField.addEventListener("blur", validateName);
  emailField.addEventListener("blur", validateEmail);
  messageField.addEventListener("blur", validateMessage);

  form.addEventListener("submit", function (event) {
    event.preventDefault();

    var isNameValid = validateName();
    var isEmailValid = validateEmail();
    var isMessageValid = validateMessage();

    if (!isNameValid || !isEmailValid || !isMessageValid) {
      successBox.hidden = true;
      // Fokus auf das erste fehlerhafte Feld setzen
      if (!isNameValid) {
        nameField.focus();
      } else if (!isEmailValid) {
        emailField.focus();
      } else {
        messageField.focus();
      }
      return;
    }

    // Demo/kein echter Versand: Es wird lediglich lokal eine
    // Erfolgsmeldung angezeigt. Nutzereingaben werden ausschließlich über
    // textContent eingefügt, niemals über innerHTML, um XSS zu vermeiden.
    var enteredName = nameField.value.trim();

    successBox.textContent = "";
    var successText = document.createElement("p");
    successText.textContent = "Danke, " + enteredName + "! Ihre Nachricht wurde erfasst (Demo, kein echter Versand).";
    successBox.appendChild(successText);
    successBox.hidden = false;

    form.reset();
    successBox.setAttribute("tabindex", "-1");
    successBox.focus();
  });
}
