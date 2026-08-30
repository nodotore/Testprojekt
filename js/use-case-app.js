"use strict";

/**
 * Use-Case-Interview-App (PWA)
 *
 * Führt dieselben Fragen wie der Claude-Code-Skill "use-case-generator"
 * (.claude/skills/use-case-generator/SKILL.md) als eigenständigen,
 * schrittweisen Wizard – geeignet für iPhone/Safari, installierbar über
 * "Zum Home-Bildschirm". Erzeugt am Ende direkt fertigen Use-Case-Markdown
 * im UC-00X-Format, der kopiert, heruntergeladen oder in USE_CASES.md
 * eingefügt werden kann.
 *
 * Alle Daten (Verlauf + laufender Entwurf) bleiben ausschließlich lokal
 * auf dem Gerät (localStorage) – es findet keine Übertragung statt.
 */

var STORAGE_HISTORY = "ucAppHistory";
var STORAGE_NEXT_ID = "ucAppNextId";
var STORAGE_DRAFT = "ucAppDraft";

/* ==========================================================================
   Fragenkatalog (entspricht Abschnitt 2-9 des Skills)
   ========================================================================== */

var STEPS = [
  // -- Grundidee ------------------------------------------------------------
  { id: "was_erreichen", section: "Grundidee", label: "Was möchtest du erreichen?", type: "textarea", required: true },
  { id: "problem", section: "Grundidee", label: "Welches Problem soll gelöst werden?", type: "textarea", required: true },
  { id: "benutzer", section: "Grundidee", label: "Wer soll die Funktion benutzen?", type: "text", required: true },
  { id: "aktion", section: "Grundidee", label: "Was soll der Benutzer konkret machen können?", type: "textarea", required: true },
  { id: "ergebnis", section: "Grundidee", label: "Was soll am Ende als Ergebnis herauskommen?", type: "textarea", required: true },

  // -- Ablauf -----------------------------------------------------------
  { id: "voraussetzungen", section: "Ablauf", label: "Was muss vorher schon vorhanden bzw. erledigt sein, damit es losgehen kann?", type: "textarea" },
  { id: "start", section: "Ablauf", label: "Wie startet der Benutzer die Funktion?", type: "text" },
  { id: "erster_schritt", section: "Ablauf", label: "Was macht der Benutzer zuerst?", type: "textarea" },
  { id: "danach", section: "Ablauf", label: "Was passiert danach?", type: "textarea" },
  { id: "eingaben", section: "Ablauf", label: "Welche Eingaben sind erforderlich?", type: "textarea" },
  { id: "entscheidungen", section: "Ablauf", label: "Welche Entscheidungen kann der Benutzer treffen?", type: "textarea" },
  { id: "automatische_aktionen", section: "Ablauf", label: "Welche Aktionen führt das Programm automatisch aus?", type: "textarea" },
  { id: "sichtbares", section: "Ablauf", label: "Was sieht der Benutzer währenddessen?", type: "textarea" },
  { id: "erfolg", section: "Ablauf", label: "Wann ist der Vorgang erfolgreich abgeschlossen?", type: "textarea", required: true },

  // -- Daten und Dateien (bedingt) ---------------------------------------
  { id: "daten_relevant", section: "Daten & Dateien", label: "Werden in diesem Use Case Dateien oder Daten verarbeitet?", type: "yesno" },
  { id: "dateien", section: "Daten & Dateien", label: "Welche Dateien werden verwendet?", type: "textarea", condition: dependsOn("daten_relevant") },
  { id: "datenquelle", section: "Daten & Dateien", label: "Woher kommen die Daten?", type: "text", condition: dependsOn("daten_relevant") },
  { id: "speicherort", section: "Daten & Dateien", label: "Wo liegen die Dateien?", type: "text", condition: dependsOn("daten_relevant") },
  { id: "dateiformate", section: "Daten & Dateien", label: "Welche Dateiformate gibt es?", type: "text", condition: dependsOn("daten_relevant") },
  { id: "import", section: "Daten & Dateien", label: "Müssen Daten importiert werden?", type: "yesno", condition: dependsOn("daten_relevant") },
  { id: "export", section: "Daten & Dateien", label: "Müssen Daten exportiert werden?", type: "yesno", condition: dependsOn("daten_relevant") },
  { id: "ordner_auswahl", section: "Daten & Dateien", label: "Soll der Benutzer Ordner auswählen können?", type: "yesno", condition: dependsOn("daten_relevant") },
  { id: "original_erhalten", section: "Daten & Dateien", label: "Müssen Originaldateien erhalten bleiben?", type: "yesno", condition: dependsOn("daten_relevant") },
  { id: "backup", section: "Daten & Dateien", label: "Soll automatisch ein Backup erstellt werden?", type: "yesno", condition: dependsOn("daten_relevant") },

  // -- Benutzeroberfläche (bedingt) --------------------------------------
  { id: "ui_relevant", section: "Benutzeroberfläche", label: "Wird für diesen Use Case eine Benutzeroberfläche benötigt?", type: "yesno" },
  { id: "ui_sichtbar", section: "Benutzeroberfläche", label: "Was soll auf dem Bildschirm sichtbar sein?", type: "textarea", condition: dependsOn("ui_relevant") },
  { id: "ui_buttons", section: "Benutzeroberfläche", label: "Welche Buttons werden benötigt?", type: "textarea", condition: dependsOn("ui_relevant") },
  { id: "ui_informationen", section: "Benutzeroberfläche", label: "Welche Informationen sollen angezeigt werden?", type: "textarea", condition: dependsOn("ui_relevant") },
  { id: "ui_vorschau", section: "Benutzeroberfläche", label: "Wird eine Vorschau benötigt?", type: "yesno", condition: dependsOn("ui_relevant") },
  { id: "ui_drag_drop", section: "Benutzeroberfläche", label: "Soll Drag-and-drop möglich sein?", type: "yesno", condition: dependsOn("ui_relevant") },
  { id: "ui_fortschritt", section: "Benutzeroberfläche", label: "Soll es Fortschrittsanzeigen geben?", type: "yesno", condition: dependsOn("ui_relevant") },
  { id: "ui_einstellungen", section: "Benutzeroberfläche", label: "Welche Einstellungen soll der Benutzer verändern können?", type: "textarea", condition: dependsOn("ui_relevant") },

  // -- Automatisierung -----------------------------------------------------
  { id: "auto_was", section: "Automatisierung", label: "Was soll automatisch passieren?", type: "textarea" },
  { id: "auto_bestaetigung", section: "Automatisierung", label: "Was muss der Benutzer bestätigen?", type: "textarea" },
  { id: "auto_nie", section: "Automatisierung", label: "Welche Aktionen dürfen niemals automatisch ausgeführt werden?", type: "textarea" },
  { id: "auto_entscheidet", section: "Automatisierung", label: "Soll das Programm Entscheidungen selbst treffen?", type: "yesno" },
  { id: "auto_ki", section: "Automatisierung", label: "Soll KI verwendet werden?", type: "yesno" },
  { id: "auto_lernen", section: "Automatisierung", label: "Soll das Programm aus vorherigen Aktionen lernen?", type: "yesno" },
  { id: "auto_hintergrund", section: "Automatisierung", label: "Müssen Aufgaben im Hintergrund laufen?", type: "yesno" },

  // -- Fehler und Sonderfälle ------------------------------------------------
  { id: "err_daten", section: "Fehler & Sonderfälle", label: "Was passiert bei fehlerhaften Daten?", type: "textarea" },
  { id: "err_fehlend", section: "Fehler & Sonderfälle", label: "Was passiert, wenn Dateien fehlen?", type: "textarea" },
  { id: "err_absturz", section: "Fehler & Sonderfälle", label: "Was passiert bei einem Programmabsturz?", type: "textarea" },
  { id: "err_neustart", section: "Fehler & Sonderfälle", label: "Was passiert bei einem Neustart?", type: "textarea" },
  { id: "err_fortsetzen", section: "Fehler & Sonderfälle", label: "Soll ein abgebrochener Vorgang fortgesetzt werden?", type: "yesno" },
  { id: "err_rueckgaengig", section: "Fehler & Sonderfälle", label: "Können Änderungen rückgängig gemacht werden?", type: "yesno" },
  { id: "err_datenverlust", section: "Fehler & Sonderfälle", label: "Welche Daten dürfen auf keinen Fall verloren gehen?", type: "textarea" },

  // -- Priorität / Qualität -------------------------------------------------
  { id: "nfr", section: "Priorität", label: "Welche Qualitätsmerkmale sind hier besonders wichtig?", type: "checkboxes", options: [
    { id: "speed", label: "Geschwindigkeit" },
    { id: "security", label: "Datensicherheit" },
    { id: "usability", label: "Bedienbarkeit" },
    { id: "offline", label: "Offlinefähigkeit" },
    { id: "stability", label: "Stabilität" },
    { id: "recovery", label: "Wiederherstellbarkeit" }
  ] },
  { id: "prioritaet", section: "Priorität", label: "Wie wichtig ist dieser Use Case?", type: "priority", required: true },

  // -- Abschluss -------------------------------------------------------------
  { id: "name", section: "Abschluss", label: "Wie soll der Use Case kurz heißen?", type: "text", required: true, placeholder: "z. B. Videos per Drag-and-drop importieren" },
  { id: "abhaengigkeiten", section: "Abschluss", label: "Gibt es Abhängigkeiten zu anderen Funktionen, Use Cases oder externen Systemen?", type: "textarea" },
  { id: "offene_punkte", section: "Abschluss", label: "Gibt es noch offene Fragen, die du festhalten möchtest?", type: "textarea" }
];

function dependsOn(gateId) {
  return function (answers) {
    return answers[gateId] === "ja";
  };
}

/* ==========================================================================
   Abgeleitete Anforderungen (Abschnitt 18 des Skills): einfache
   Stichwort-Heuristik über alle Freitext-Antworten.
   ========================================================================== */

var DERIVED_RULES = [
  { pattern: /drag.?and.?drop|hineinzieh/i, items: [
    "Drag-and-drop-Zone erforderlich.",
    "Unterstützte Dateiformate müssen definiert werden.",
    "Ungültige Dateien müssen erkannt und abgewiesen werden.",
    "Mehrere Dateien gleichzeitig müssen berücksichtigt werden.",
    "Importfortschritt sollte angezeigt werden.",
    "Fehler beim Import müssen verständlich angezeigt werden."
  ] },
  { pattern: /video/i, items: [
    "Unterstützte Videoformate müssen definiert werden.",
    "Eine Vorschau bzw. ein Thumbnail für Videos ist sinnvoll."
  ] },
  { pattern: /foto|bild|kamera/i, items: [
    "Zugriff auf Kamera bzw. Fotobibliothek erfordert eine iOS-Berechtigung.",
    "Verhalten bei verweigerter Berechtigung muss festgelegt werden."
  ] },
  { pattern: /standort|gps|location/i, items: [
    "Standortzugriff erfordert eine iOS-Berechtigung.",
    "Verhalten bei verweigerter Standortberechtigung muss festgelegt werden."
  ] },
  { pattern: /push|benachrichtigung/i, items: [
    "Push-Benachrichtigungen erfordern eine iOS-Berechtigung."
  ] },
  { pattern: /passwort|login|anmeld/i, items: [
    "Sichere Authentifizierung erforderlich.",
    "Passwörter dürfen niemals im Klartext gespeichert werden."
  ] },
  { pattern: /e-?mail/i, items: [
    "E-Mail-Adressen müssen validiert werden."
  ] },
  { pattern: /offline/i, items: [
    "Kernfunktion muss auch ohne Internetverbindung nutzbar sein."
  ] },
  { pattern: /synchron|sync/i, items: [
    "Verhalten bei gleichzeitigen Änderungen auf mehreren Geräten muss festgelegt werden."
  ] }
];

/* ==========================================================================
   Freitext-Felder, die als Anforderungen in den Use Case übernommen werden
   ========================================================================== */

var REQUIREMENT_LABELS = {
  dateien: "Verwendete Dateien",
  datenquelle: "Datenquelle",
  speicherort: "Speicherort der Dateien",
  dateiformate: "Unterstützte Dateiformate",
  ui_sichtbar: "Sichtbare Bildschirminhalte",
  ui_buttons: "Benötigte Buttons/Aktionen",
  ui_informationen: "Angezeigte Informationen",
  ui_einstellungen: "Einstellbare Optionen",
  auto_was: "Automatisch ausgeführte Aktionen",
  auto_bestaetigung: "Bestätigungspflichtige Aktionen",
  auto_nie: "Niemals automatisch auszuführende Aktionen (Sicherheitsregel)"
};

var YESNO_REQUIREMENT_TEXT = {
  import: { ja: "Daten können importiert werden." },
  export: { ja: "Daten können exportiert werden." },
  ordner_auswahl: { ja: "Der Benutzer kann Ordner auswählen." },
  original_erhalten: { ja: "Originaldateien bleiben unverändert erhalten (Bearbeitungen erfolgen ausschließlich auf Kopien)." },
  backup: { ja: "Vor kritischen Änderungen wird automatisch ein Backup erstellt." },
  ui_vorschau: { ja: "Eine Vorschau wird angezeigt." },
  ui_drag_drop: { ja: "Drag-and-drop wird unterstützt." },
  ui_fortschritt: { ja: "Der Fortschritt wird während der Verarbeitung angezeigt." },
  auto_entscheidet: { ja: "Das Programm trifft bestimmte Entscheidungen selbstständig.", nein: "Das Programm trifft keine Entscheidungen selbstständig – alles läuft über eine Bestätigung durch den Benutzer." },
  auto_ki: { ja: "Es wird KI-Unterstützung eingesetzt." },
  auto_lernen: { ja: "Das Programm lernt aus vorherigen Aktionen." },
  auto_hintergrund: { ja: "Aufgaben laufen im Hintergrund." }
};

var NFR_TEXT = {
  speed: "Die Funktion reagiert spürbar schnell, auch bei größeren Datenmengen.",
  security: "Daten werden sicher verarbeitet und nicht unautorisiert offengelegt.",
  usability: "Die Bedienung ist auch ohne Anleitung weitgehend selbsterklärend.",
  offline: "Die Funktion ist auch ohne Internetverbindung nutzbar.",
  stability: "Die Funktion läuft auch bei fehlerhaften Eingaben stabil weiter.",
  recovery: "Nach einem Absturz oder Neustart lässt sich der letzte Stand wiederherstellen."
};

var NFR_LABEL = {};
STEPS.forEach(function (step) {
  if (step.id === "nfr") {
    step.options.forEach(function (opt) {
      NFR_LABEL[opt.id] = opt.label;
    });
  }
});

/* ==========================================================================
   Anwendungsstatus
   ========================================================================== */

var wizardAnswers = {};
var wizardStepIndex = 0;
var activeSteps = [];
var viewingHistoryId = null;

document.addEventListener("DOMContentLoaded", function () {
  registerServiceWorker();
  renderHistory();
  bindStaticEvents();
  restoreDraftIfPresent();
});

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    return;
  }
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("sw.js").catch(function () {
      // Offline-Unterstützung ist ein Komfortfeature; ein Fehler hier
      // darf die App nicht blockieren.
    });
  });
}

/* ==========================================================================
   Navigation zwischen den drei Screens
   ========================================================================== */

function showScreen(name) {
  ["home", "wizard", "result"].forEach(function (screen) {
    var el = document.getElementById("screen-" + screen);
    if (el) {
      el.hidden = screen !== name;
    }
  });
  window.scrollTo(0, 0);
}

function bindStaticEvents() {
  document.getElementById("btn-new-use-case").addEventListener("click", startWizard);
  document.getElementById("btn-cancel-wizard").addEventListener("click", cancelWizard);
  document.getElementById("btn-back-home").addEventListener("click", function () {
    viewingHistoryId = null;
    renderHistory();
    showScreen("home");
  });
  document.getElementById("wizard-form").addEventListener("submit", function (event) {
    event.preventDefault();
    handleNext();
  });
  document.getElementById("btn-back").addEventListener("click", handleBack);
  document.getElementById("btn-skip").addEventListener("click", handleSkip);
  document.getElementById("btn-copy").addEventListener("click", copyResultToClipboard);
  document.getElementById("btn-download").addEventListener("click", downloadResult);
  document.getElementById("btn-delete-entry").addEventListener("click", deleteViewedEntry);
}

/* ==========================================================================
   Wizard: Ablauf
   ========================================================================== */

function startWizard() {
  wizardAnswers = {};
  wizardStepIndex = 0;
  activeSteps = computeActiveSteps(wizardAnswers);
  saveDraft();
  showScreen("wizard");
  renderStep();
}

function cancelWizard() {
  if (!window.confirm("Interview wirklich abbrechen? Die bisherigen Antworten gehen verloren.")) {
    return;
  }
  clearDraft();
  showScreen("home");
}

function computeActiveSteps(answers) {
  return STEPS.filter(function (step) {
    return typeof step.condition !== "function" || step.condition(answers);
  });
}

function currentStep() {
  return activeSteps[wizardStepIndex];
}

function renderStep() {
  activeSteps = computeActiveSteps(wizardAnswers);
  if (wizardStepIndex >= activeSteps.length) {
    finishWizard();
    return;
  }

  var step = currentStep();
  var container = document.getElementById("wizard-question");
  container.innerHTML = "";
  document.getElementById("wizard-error").textContent = "";

  var sectionEl = document.createElement("p");
  sectionEl.className = "wizard-section";
  sectionEl.textContent = step.section;
  container.appendChild(sectionEl);

  var labelEl = document.createElement("label");
  labelEl.className = "wizard-label";
  labelEl.setAttribute("for", "field-" + step.id);
  labelEl.textContent = step.label + (step.required ? " *" : "");
  container.appendChild(labelEl);

  container.appendChild(buildFieldElement(step));

  var existingRecommendation = document.getElementById("wizard-recommendation");
  if (existingRecommendation) {
    existingRecommendation.remove();
  }
  if (step.id === "prioritaet") {
    var rec = document.createElement("p");
    rec.id = "wizard-recommendation";
    rec.className = "wizard-hint";
    rec.textContent = "Empfehlung von Claude auf Basis deiner Antworten: " + recommendPriority(wizardAnswers) + " (kannst du unten ändern).";
    container.appendChild(rec);
  }

  document.getElementById("btn-back").disabled = wizardStepIndex === 0;
  document.getElementById("btn-skip").hidden = !!step.required;

  updateProgress(step);
  focusFirstField();
}

function buildFieldElement(step) {
  var value = wizardAnswers[step.id];

  if (step.type === "text") {
    var input = document.createElement("input");
    input.type = "text";
    input.id = "field-" + step.id;
    input.className = "wizard-input";
    input.value = value || "";
    if (step.placeholder) {
      input.placeholder = step.placeholder;
    }
    return input;
  }

  if (step.type === "textarea") {
    var textarea = document.createElement("textarea");
    textarea.id = "field-" + step.id;
    textarea.className = "wizard-input";
    textarea.rows = 4;
    textarea.value = value || "";
    if (step.placeholder) {
      textarea.placeholder = step.placeholder;
    }
    return textarea;
  }

  if (step.type === "yesno") {
    var wrap = document.createElement("div");
    wrap.className = "wizard-choice-group";
    wrap.id = "field-" + step.id;
    ["ja", "nein"].forEach(function (option) {
      var optId = "field-" + step.id + "-" + option;
      var label = document.createElement("label");
      label.className = "wizard-choice";
      label.setAttribute("for", optId);

      var radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "field-" + step.id;
      radio.id = optId;
      radio.value = option;
      radio.checked = value === option;

      var text = document.createElement("span");
      text.textContent = option === "ja" ? "Ja" : "Nein";

      label.appendChild(radio);
      label.appendChild(text);
      wrap.appendChild(label);
    });
    return wrap;
  }

  if (step.type === "checkboxes") {
    var box = document.createElement("div");
    box.className = "wizard-choice-group";
    box.id = "field-" + step.id;
    var selected = value || [];
    step.options.forEach(function (opt) {
      var optId = "field-" + step.id + "-" + opt.id;
      var label = document.createElement("label");
      label.className = "wizard-choice";
      label.setAttribute("for", optId);

      var checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = optId;
      checkbox.value = opt.id;
      checkbox.checked = selected.indexOf(opt.id) !== -1;

      var text = document.createElement("span");
      text.textContent = opt.label;

      label.appendChild(checkbox);
      label.appendChild(text);
      box.appendChild(label);
    });
    return box;
  }

  if (step.type === "priority") {
    var priorityWrap = document.createElement("div");
    priorityWrap.className = "wizard-choice-group";
    priorityWrap.id = "field-" + step.id;
    var current = value || recommendPriority(wizardAnswers);
    [
      { id: "MUSS", desc: "Ohne diese Funktion ist der Use Case nicht sinnvoll nutzbar." },
      { id: "SOLL", desc: "Wichtig, aber nicht zwingend für die erste Version." },
      { id: "KANN", desc: "Komfort- oder Erweiterungsfunktion." }
    ].forEach(function (option) {
      var optId = "field-" + step.id + "-" + option.id;
      var label = document.createElement("label");
      label.className = "wizard-choice wizard-choice-priority";
      label.setAttribute("for", optId);

      var radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "field-" + step.id;
      radio.id = optId;
      radio.value = option.id;
      radio.checked = current === option.id;

      var textWrap = document.createElement("span");
      var strong = document.createElement("strong");
      strong.textContent = option.id;
      var desc = document.createElement("small");
      desc.textContent = option.desc;
      textWrap.appendChild(strong);
      textWrap.appendChild(desc);

      label.appendChild(radio);
      label.appendChild(textWrap);
      priorityWrap.appendChild(label);
    });
    return priorityWrap;
  }

  var fallback = document.createElement("input");
  fallback.type = "text";
  fallback.id = "field-" + step.id;
  return fallback;
}

function focusFirstField() {
  var step = currentStep();
  var field = document.getElementById("field-" + step.id);
  if (field && typeof field.focus === "function") {
    field.focus();
  } else {
    var firstRadio = document.querySelector("#field-" + step.id + " input");
    if (firstRadio) {
      firstRadio.focus();
    }
  }
}

function readFieldValue(step) {
  if (step.type === "text" || step.type === "textarea") {
    var el = document.getElementById("field-" + step.id);
    return el.value.trim();
  }
  if (step.type === "yesno" || step.type === "priority") {
    var checked = document.querySelector("#field-" + step.id + " input:checked");
    return checked ? checked.value : "";
  }
  if (step.type === "checkboxes") {
    var boxes = document.querySelectorAll("#field-" + step.id + " input:checked");
    return Array.prototype.map.call(boxes, function (box) {
      return box.value;
    });
  }
  return "";
}

function updateProgress(step) {
  var total = activeSteps.length;
  var percent = Math.round(((wizardStepIndex + 1) / total) * 100);
  document.getElementById("wizard-progress-fill").style.width = percent + "%";
  document.getElementById("wizard-step-label").textContent =
    step.section + " – Frage " + (wizardStepIndex + 1) + " von " + total;
}

function handleNext() {
  var step = currentStep();
  var value = readFieldValue(step);

  if (step.required) {
    var isEmpty = Array.isArray(value) ? value.length === 0 : value === "";
    if (isEmpty) {
      document.getElementById("wizard-error").textContent = "Diese Frage wird für einen vollständigen Use Case benötigt.";
      return;
    }
  }

  wizardAnswers[step.id] = value;
  saveDraft();
  wizardStepIndex++;
  renderStep();
}

function handleSkip() {
  var step = currentStep();
  delete wizardAnswers[step.id];
  saveDraft();
  wizardStepIndex++;
  renderStep();
}

function handleBack() {
  if (wizardStepIndex === 0) {
    return;
  }
  wizardStepIndex--;
  renderStep();
}

/* ==========================================================================
   Priorität-Empfehlung (Abschnitt 8 des Skills)
   ========================================================================== */

function recommendPriority(answers) {
  var text = collectAllText(answers).toLowerCase();
  var mustHints = /unbedingt|zwingend|kritisch|pflicht|muss funktionieren|ohne das (geht|funktioniert)/;
  var canHints = /wäre schön|optional|nice.to.have|später|vielleicht|kann warten|nicht dringend/;

  if (mustHints.test(text)) {
    return "MUSS";
  }
  if (canHints.test(text)) {
    return "KANN";
  }
  return "SOLL";
}

function collectAllText(answers) {
  return Object.keys(answers)
    .map(function (key) {
      var value = answers[key];
      return Array.isArray(value) ? value.join(" ") : String(value || "");
    })
    .join(" ");
}

/* ==========================================================================
   Use Case abschließen: Markdown erzeugen, speichern, anzeigen
   ========================================================================== */

function finishWizard() {
  var derived = deriveRequirements(wizardAnswers);
  var ucNumber = getNextUcNumber();
  var markdown = buildMarkdown(ucNumber, wizardAnswers, derived);
  var name = wizardAnswers.name || "Unbenannter Use Case";

  var entry = {
    id: ucNumber,
    name: name,
    createdAt: new Date().toISOString(),
    answers: wizardAnswers,
    markdown: markdown
  };

  saveHistoryEntry(entry);
  incrementUcCounter();
  clearDraft();

  viewingHistoryId = entry.id;
  showResult(entry, derived);
  renderHistory();
}

function deriveRequirements(answers) {
  var text = collectAllText(answers);
  var found = [];
  DERIVED_RULES.forEach(function (rule) {
    if (rule.pattern.test(text)) {
      rule.items.forEach(function (item) {
        if (found.indexOf(item) === -1) {
          found.push(item);
        }
      });
    }
  });
  return found;
}

function getNextUcNumber() {
  var next = parseInt(localStorage.getItem(STORAGE_NEXT_ID) || "1", 10);
  var padded = String(next).length < 3 ? ("000" + next).slice(-3) : String(next);
  return "UC-" + padded;
}

function incrementUcCounter() {
  var next = parseInt(localStorage.getItem(STORAGE_NEXT_ID) || "1", 10);
  localStorage.setItem(STORAGE_NEXT_ID, String(next + 1));
}

/* ==========================================================================
   Markdown-Erzeugung im UC-00X-Format aus SKILL.md Abschnitt 10
   ========================================================================== */

function buildMarkdown(ucNumber, a, derived) {
  var lines = [];

  lines.push("## " + ucNumber + " – " + (a.name || "Unbenannter Use Case"));
  lines.push("");

  lines.push("### Ziel");
  lines.push(joinNonEmpty([a.was_erreichen, a.ergebnis], " "));
  lines.push("");

  lines.push("### Benutzer");
  lines.push(a.benutzer || "_Nicht angegeben._");
  lines.push("");

  lines.push("### Ausgangssituation");
  lines.push(a.voraussetzungen || "_Keine besonderen Voraussetzungen erfasst._");
  lines.push("");

  lines.push("### Auslöser");
  lines.push(a.start || "_Nicht angegeben._");
  lines.push("");

  lines.push("### Normaler Ablauf");
  var ablaufSchritte = buildAblaufSchritte(a);
  ablaufSchritte.forEach(function (schritt, idx) {
    lines.push((idx + 1) + ". " + schritt);
  });
  lines.push("");

  lines.push("### Ergebnis");
  lines.push(a.erfolg || a.ergebnis || "_Nicht angegeben._");
  lines.push("");

  lines.push("### Alternative Abläufe");
  if (a.entscheidungen) {
    lines.push("Je nach Entscheidung des Benutzers: " + a.entscheidungen);
  } else {
    lines.push("Keine besonderen alternativen Abläufe erfasst.");
  }
  lines.push("");

  lines.push("### Fehlerfälle");
  var fehler = buildFehlerfaelle(a);
  if (fehler.length) {
    fehler.forEach(function (f) {
      lines.push("- " + f);
    });
  } else {
    lines.push("Keine besonderen Fehlerfälle erfasst.");
  }
  lines.push("");

  lines.push("### Anforderungen");
  var anforderungen = buildAnforderungen(a, derived);
  if (anforderungen.length) {
    anforderungen.forEach(function (r) {
      lines.push("- " + r);
    });
  } else {
    lines.push("_Keine zusätzlichen Anforderungen erfasst._");
  }
  lines.push("");

  lines.push("### Nichtfunktionale Anforderungen");
  var nfr = a.nfr || [];
  if (nfr.length) {
    nfr.forEach(function (id) {
      lines.push("- " + NFR_LABEL[id] + ": " + NFR_TEXT[id]);
    });
  } else {
    lines.push("_Keine besonderen nichtfunktionalen Anforderungen ausgewählt._");
  }
  lines.push("");

  lines.push("### Akzeptanzkriterien");
  buildAkzeptanzkriterien(a).forEach(function (k) {
    lines.push("- " + k);
  });
  lines.push("");

  lines.push("### Priorität");
  lines.push(a.prioritaet || recommendPriority(a));
  lines.push("");

  lines.push("### Abhängigkeiten");
  lines.push(a.abhaengigkeiten || "Keine bekannt.");
  lines.push("");

  lines.push("### Offene Punkte");
  var offenePunkte = buildOffenePunkte(a);
  if (offenePunkte.length) {
    offenePunkte.forEach(function (p) {
      lines.push("- " + p);
    });
  } else {
    lines.push("Keine.");
  }

  return lines.join("\n");
}

function joinNonEmpty(parts, separator) {
  var filtered = parts.filter(function (p) {
    return p && String(p).trim() !== "";
  });
  return filtered.length ? filtered.join(separator) : "_Nicht angegeben._";
}

function buildAblaufSchritte(a) {
  var schritte = [];
  schritte.push("Benutzer startet: " + (a.start || "die Funktion"));
  if (a.erster_schritt) schritte.push(a.erster_schritt);
  if (a.eingaben) schritte.push("Benutzer gibt Folgendes ein: " + a.eingaben);
  if (a.entscheidungen) schritte.push("Benutzer trifft ggf. folgende Entscheidung(en): " + a.entscheidungen);
  if (a.automatische_aktionen) schritte.push("System führt automatisch aus: " + a.automatische_aktionen);
  if (a.danach) schritte.push(a.danach);
  if (a.sichtbares) schritte.push("Währenddessen sieht der Benutzer: " + a.sichtbares);
  schritte.push("Ergebnis wird angezeigt bzw. gespeichert: " + (a.erfolg || a.ergebnis || "siehe Abschnitt Ergebnis"));
  return schritte;
}

function buildFehlerfaelle(a) {
  var out = [];
  if (a.err_daten) out.push("Fehlerhafte Daten: " + a.err_daten);
  if (a.err_fehlend) out.push("Fehlende Dateien: " + a.err_fehlend);
  if (a.err_absturz) out.push("Programmabsturz: " + a.err_absturz);
  if (a.err_neustart) out.push("Neustart: " + a.err_neustart);
  if (a.err_fortsetzen === "ja") out.push("Ein abgebrochener Vorgang wird fortgesetzt.");
  if (a.err_fortsetzen === "nein") out.push("Ein abgebrochener Vorgang muss neu gestartet werden.");
  if (a.err_rueckgaengig === "ja") out.push("Änderungen können rückgängig gemacht werden.");
  if (a.err_rueckgaengig === "nein") out.push("Änderungen können nicht rückgängig gemacht werden.");
  if (a.err_datenverlust) out.push("Auf keinen Fall dürfen folgende Daten verloren gehen: " + a.err_datenverlust);
  return out;
}

function buildAnforderungen(a, derived) {
  var out = [];

  Object.keys(REQUIREMENT_LABELS).forEach(function (key) {
    if (a[key]) {
      out.push(REQUIREMENT_LABELS[key] + ": " + a[key]);
    }
  });

  Object.keys(YESNO_REQUIREMENT_TEXT).forEach(function (key) {
    var value = a[key];
    var mapping = YESNO_REQUIREMENT_TEXT[key];
    if (value && mapping[value]) {
      out.push(mapping[value]);
    }
  });

  derived.forEach(function (item) {
    out.push(item + " *(abgeleitet)*");
  });

  return out;
}

function buildAkzeptanzkriterien(a) {
  var out = [];
  out.push("Der Use Case gilt als abgeschlossen, wenn: " + (a.erfolg || a.ergebnis || "das beschriebene Ergebnis eintritt"));
  buildFehlerfaelle(a).forEach(function (f) {
    out.push("Der Fehlerfall wird korrekt abgefangen: " + f);
  });
  if (!out.length) {
    out.push("Wird beim Umsetzen konkretisiert.");
  }
  return out;
}

function buildOffenePunkte(a) {
  var out = [];
  activeSteps.forEach(function (step) {
    if (step.required) return;
    if (step.id === "offene_punkte" || step.id === "nfr") return;
    var value = a[step.id];
    var isEmpty = value === undefined || value === "" || (Array.isArray(value) && value.length === 0);
    if (isEmpty) {
      out.push(step.label + " (nicht beantwortet)");
    }
  });
  if (a.offene_punkte) {
    a.offene_punkte.split(/\n+/).forEach(function (line) {
      var trimmed = line.trim();
      if (trimmed) {
        out.push(trimmed);
      }
    });
  }
  return out;
}

/* ==========================================================================
   Verlauf (localStorage)
   ========================================================================== */

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_HISTORY) || "[]");
  } catch (e) {
    return [];
  }
}

function saveHistoryEntry(entry) {
  var history = loadHistory();
  history.unshift(entry);
  localStorage.setItem(STORAGE_HISTORY, JSON.stringify(history));
}

function deleteHistoryEntry(id) {
  var history = loadHistory().filter(function (item) {
    return item.id !== id;
  });
  localStorage.setItem(STORAGE_HISTORY, JSON.stringify(history));
}

function renderHistory() {
  var history = loadHistory();
  var list = document.getElementById("history-list");
  var empty = document.getElementById("history-empty");
  list.innerHTML = "";

  if (!history.length) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  history.forEach(function (entry) {
    var li = document.createElement("li");
    li.className = "history-item";

    var button = document.createElement("button");
    button.type = "button";
    button.className = "history-item-btn";

    var idSpan = document.createElement("span");
    idSpan.className = "history-item-id";
    idSpan.textContent = entry.id;

    var nameSpan = document.createElement("span");
    nameSpan.className = "history-item-name";
    nameSpan.textContent = entry.name;

    var dateSpan = document.createElement("span");
    dateSpan.className = "history-item-date";
    dateSpan.textContent = formatDate(entry.createdAt);

    button.appendChild(idSpan);
    button.appendChild(nameSpan);
    button.appendChild(dateSpan);
    button.addEventListener("click", function () {
      viewingHistoryId = entry.id;
      showResult(entry, deriveRequirements(entry.answers));
    });

    li.appendChild(button);
    list.appendChild(li);
  });
}

function formatDate(iso) {
  try {
    var d = new Date(iso);
    return d.toLocaleDateString("de-DE") + " " + d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
  } catch (e) {
    return "";
  }
}

function deleteViewedEntry() {
  if (!viewingHistoryId) {
    return;
  }
  if (!window.confirm("Diesen Use Case wirklich löschen?")) {
    return;
  }
  deleteHistoryEntry(viewingHistoryId);
  viewingHistoryId = null;
  renderHistory();
  showScreen("home");
}

/* ==========================================================================
   Ergebnis-Screen
   ========================================================================== */

function showResult(entry, derived) {
  document.getElementById("result-title").textContent = entry.id + " – " + entry.name;
  document.getElementById("result-markdown").textContent = entry.markdown;

  var assumptionsBox = document.getElementById("result-assumptions");
  assumptionsBox.innerHTML = "";
  if (derived.length) {
    var title = document.createElement("p");
    title.className = "wizard-hint";
    title.textContent = "Automatisch abgeleitete Anforderungen wurden bereits in den Text übernommen (siehe „Anforderungen“).";
    assumptionsBox.appendChild(title);
    assumptionsBox.hidden = false;
  } else {
    assumptionsBox.hidden = true;
  }

  document.getElementById("copy-status").textContent = "";
  showScreen("result");
}

function copyResultToClipboard() {
  var text = document.getElementById("result-markdown").textContent;
  var status = document.getElementById("copy-status");

  function onSuccess() {
    status.textContent = "In die Zwischenablage kopiert.";
  }
  function onError() {
    status.textContent = "Kopieren nicht möglich – bitte Text manuell markieren.";
  }

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(onSuccess, onError);
  } else {
    onError();
  }
}

function downloadResult() {
  var text = document.getElementById("result-markdown").textContent;
  var id = viewingHistoryId || "use-case";
  var blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
  var url = URL.createObjectURL(blob);
  var link = document.createElement("a");
  link.href = url;
  link.download = id + ".md";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/* ==========================================================================
   Entwurf zwischenspeichern (abgebrochenes Interview fortsetzen)
   ========================================================================== */

function saveDraft() {
  localStorage.setItem(STORAGE_DRAFT, JSON.stringify({
    answers: wizardAnswers,
    stepIndex: wizardStepIndex
  }));
}

function clearDraft() {
  localStorage.removeItem(STORAGE_DRAFT);
}

function restoreDraftIfPresent() {
  var raw = localStorage.getItem(STORAGE_DRAFT);
  if (!raw) {
    return;
  }
  try {
    var draft = JSON.parse(raw);
    if (!draft.answers || typeof draft.stepIndex !== "number") {
      return;
    }
    var resume = window.confirm("Es gibt ein unvollständiges Interview. Möchtest du dort weitermachen?");
    if (!resume) {
      clearDraft();
      return;
    }
    wizardAnswers = draft.answers;
    wizardStepIndex = draft.stepIndex;
    activeSteps = computeActiveSteps(wizardAnswers);
    if (wizardStepIndex >= activeSteps.length) {
      wizardStepIndex = Math.max(0, activeSteps.length - 1);
    }
    showScreen("wizard");
    renderStep();
  } catch (e) {
    clearDraft();
  }
}
