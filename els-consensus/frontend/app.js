// frontend/app.js

let schema = null;
let images = [];
let doneSet = new Set();   // from server (/annotated/<annotator>)
let currentIndex = 0;

const elAnnotator = document.getElementById("annotatorId");
const elImg = document.getElementById("elsImage");
const elQuestions = document.getElementById("questions");
const elCounter = document.getElementById("imgCounter");
const elStatus = document.getElementById("status");
const elError = document.getElementById("error");
const btnResume = document.getElementById("btnResume");
const btnSubmit = document.getElementById("btnSubmit");

const LS_LAST_ANNOTATOR = "els.lastAnnotator";

function setStatus(msg) { elStatus.textContent = msg || ""; }
function setError(msg) { elError.textContent = msg || ""; }

function getAnnotatorId() {
  return (elAnnotator.value || "").trim();
}

async function fetchJSON(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json();
}

function imageUrl(filename) {
  // IMPORTANT: absolute path so it works under /ui/
  return `/images/${encodeURIComponent(filename)}?v=${Date.now()}`;
}

function buildQuestions() {
  elQuestions.innerHTML = "";

  // Optional: show legend once
  const legend = document.createElement("div");
  legend.style.border = "1px solid #ddd";
  legend.style.padding = "10px";
  legend.style.margin = "10px 0";
  legend.innerHTML = `<b>Color Legend</b><br>Yellow = B cells<br>Red = T cells<br>Green = Proliferating cells (Ki67+)`;
  elQuestions.appendChild(legend);

  for (const [qKey, spec] of Object.entries(schema)) {
    const fs = document.createElement("fieldset");
    const lg = document.createElement("legend");
    lg.textContent = qKey;
    fs.appendChild(lg);

    if (spec.description) {
      const p = document.createElement("div");
      p.textContent = spec.description;
      p.style.margin = "8px 0 10px";
      fs.appendChild(p);
    }

    for (const opt of spec.options) {
      const label = document.createElement("label");
      label.style.display = "block";
      label.style.margin = "6px 0";

      const input = document.createElement("input");
      input.type = (spec.type === "multi") ? "checkbox" : "radio";
      input.name = qKey;
      input.value = opt;
      input.dataset.q = qKey;
      input.style.marginRight = "10px";

      label.appendChild(input);
      label.appendChild(document.createTextNode(opt));
      fs.appendChild(label);
    }

    elQuestions.appendChild(fs);
  }
}

function clearSelections() {
  elQuestions.querySelectorAll("input").forEach(i => i.checked = false);
}

function collectAnswers() {
  const answers = {};
  for (const [qKey, spec] of Object.entries(schema)) {
    if (spec.type === "multi") {
      const checked = Array.from(document.querySelectorAll(`input[data-q="${qKey}"]:checked`))
        .map(x => x.value);
      answers[qKey] = checked;
    } else {
      const chosen = document.querySelector(`input[data-q="${qKey}"]:checked`);
      answers[qKey] = chosen ? chosen.value : "";
    }
  }
  return answers;
}

function validateAnswers(answers) {
  for (const [qKey, spec] of Object.entries(schema)) {
    if (spec.type === "multi") {
      if (!Array.isArray(answers[qKey]) || answers[qKey].length === 0) return false;
    } else {
      if (!answers[qKey]) return false;
    }
  }
  return true;
}

function findFirstUnannotated() {
  for (let i = 0; i < images.length; i++) {
    if (!doneSet.has(images[i])) return i;
  }
  return -1;
}

function renderImage() {
  if (!images.length) {
    elImg.removeAttribute("src");
    elCounter.textContent = "No images found";
    return;
  }

  const filename = images[currentIndex];
  elImg.src = imageUrl(filename);
  elCounter.textContent = `Image ${currentIndex + 1} / ${images.length} (${filename})`;
}

async function resume() {
  setError("");
  setStatus("");

  const annotator = getAnnotatorId();
  if (!annotator) {
    setError("Please enter Annotator ID and click Resume");
    return;
  }

  localStorage.setItem(LS_LAST_ANNOTATOR, annotator);

  // Pull from server: what this annotator already submitted
  const doneList = await fetchJSON(`/annotated/${encodeURIComponent(annotator)}`);
  doneSet = new Set(doneList);

  const nextIdx = findFirstUnannotated();
  if (nextIdx === -1) {
    elImg.removeAttribute("src");
    elQuestions.innerHTML = "";
    elCounter.textContent = "All images annotated 🎉";
    setStatus("All done 🎉");
    return;
  }

  currentIndex = nextIdx;
  clearSelections();
  renderImage();
  setStatus("Resumed ✔");
}

async function submitAndNext() {
  setError("");

  const annotator = getAnnotatorId();
  if (!annotator) {
    setError("Annotator ID is required");
    return;
  }

  const answers = collectAnswers();
  if (!validateAnswers(answers)) {
    setError("Please answer ALL questions before continuing.");
    return;
  }

  const payload = {
    image_id: images[currentIndex],
    annotator_id: annotator,
    answers
  };

  setStatus("Saving...");

  const res = await fetch("/annotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const txt = await res.text();
    setError(`Save failed (${res.status}): ${txt}`);
    setStatus("");
    return;
  }

  // Mark locally to move forward immediately
  doneSet.add(images[currentIndex]);

  // Find next unannotated
  const nextIdx = findFirstUnannotated();
  if (nextIdx === -1) {
    elImg.removeAttribute("src");
    elQuestions.innerHTML = "";
    elCounter.textContent = "All images annotated 🎉";
    setStatus("All done 🎉");
    return;
  }

  currentIndex = nextIdx;
  clearSelections();
  renderImage();
  setStatus("Saved ✔");
}

btnResume.addEventListener("click", (e) => { e.preventDefault(); resume(); });
btnSubmit.addEventListener("click", (e) => { e.preventDefault(); submitAndNext(); });

(async function init() {
  try {
    schema = await fetchJSON("/schema");
    images = await fetchJSON("/images-list");
    buildQuestions();

    // Auto-fill last annotator & auto-resume on refresh
    const last = localStorage.getItem(LS_LAST_ANNOTATOR);
    if (last) elAnnotator.value = last;

    if (last) {
      await resume(); // THIS is what makes refresh resume
    } else {
      // show first image only (no resume until annotator entered)
      currentIndex = 0;
      renderImage();
      setStatus("Enter Annotator ID and click Resume");
    }
  } catch (err) {
    setError(String(err));
  }
})();
