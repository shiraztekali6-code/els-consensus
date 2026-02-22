// frontend/app.js

let images = [];
let schema = null;

let idx = 0; // current image index

const elAnnotator = document.getElementById("annotatorId");
const elImg = document.getElementById("elsImage");
const elQuestions = document.getElementById("questions");
const elCounter = document.getElementById("imgCounter");
const elStatus = document.getElementById("status");
const btnSubmit = document.getElementById("btnSubmit");
const btnResume = document.getElementById("btnResume");

// ---- helpers ----
function setStatus(msg) {
  if (elStatus) elStatus.textContent = msg || "";
}

function getAnnotatorId() {
  return (elAnnotator?.value || "").trim();
}

function imageUrl(filename) {
  // IMPORTANT: absolute path (works even when page is under /ui/)
  // Also add cache-buster so browser won't show old/broken cached result.
  return `/images/${encodeURIComponent(filename)}?v=${Date.now()}`;
}

function getProgressKey(annotatorId) {
  return `els_progress:${annotatorId}`;
}

function saveProgress(annotatorId) {
  try {
    localStorage.setItem(getProgressKey(annotatorId), String(idx));
  } catch (e) {}
}

function loadProgress(annotatorId) {
  try {
    const v = localStorage.getItem(getProgressKey(annotatorId));
    if (v === null) return 0;
    const n = parseInt(v, 10);
    return Number.isFinite(n) && n >= 0 ? n : 0;
  } catch (e) {
    return 0;
  }
}

function clearQuestionUI() {
  if (elQuestions) elQuestions.innerHTML = "";
}

function buildQuestionUI() {
  clearQuestionUI();
  if (!schema || !elQuestions) return;

  // schema is QUESTION_SCHEMA dict
  for (const [qKey, spec] of Object.entries(schema)) {
    const box = document.createElement("div");
    box.style.border = "1px solid #ddd";
    box.style.padding = "12px";
    box.style.margin = "12px 0";
    box.style.maxWidth = "720px";

    const title = document.createElement("div");
    title.style.fontWeight = "700";
    title.style.fontSize = "20px";
    title.textContent = qKey;
    box.appendChild(title);

    if (spec.description) {
      const desc = document.createElement("div");
      desc.style.margin = "8px 0 10px";
      desc.textContent = spec.description;
      box.appendChild(desc);
    }

    const type = spec.type; // "multi" / "single"
    const options = spec.options || [];

    options.forEach((opt, i) => {
      const row = document.createElement("label");
      row.style.display = "block";
      row.style.margin = "6px 0";
      row.style.cursor = "pointer";

      const input = document.createElement("input");
      input.type = (type === "multi") ? "checkbox" : "radio";
      input.name = qKey;
      input.value = opt;
      input.dataset.qkey = qKey;
      input.style.marginRight = "10px";

      row.appendChild(input);
      row.appendChild(document.createTextNode(opt));
      box.appendChild(row);
    });

    elQuestions.appendChild(box);
  }
}

function collectAnswers() {
  if (!schema) return null;

  const answers = {};

  for (const [qKey, spec] of Object.entries(schema)) {
    const type = spec.type;

    if (type === "multi") {
      const checked = Array.from(document.querySelectorAll(`input[data-qkey="${qKey}"]:checked`))
        .map(x => x.value);
      // allow empty? depends on your validate_answers. if you require non-empty, keep as-is.
      answers[qKey] = checked;
    } else {
      const chosen = document.querySelector(`input[data-qkey="${qKey}"]:checked`);
      answers[qKey] = chosen ? chosen.value : "";
    }
  }

  return answers;
}

function renderImage() {
  if (!images.length) {
    setStatus("No images found.");
    if (elCounter) elCounter.textContent = "";
    if (elImg) elImg.removeAttribute("src");
    return;
  }

  const filename = images[idx];

  if (elCounter) elCounter.textContent = `Image ${idx + 1} / ${images.length}`;
  setStatus("");

  // Update image
  if (elImg) {
    elImg.alt = "ELS image";
    elImg.style.maxWidth = "720px";
    elImg.style.width = "100%";
    elImg.style.height = "auto";
    elImg.src = imageUrl(filename);
  }
}

async function loadSchema() {
  const r = await fetch("/schema");
  if (!r.ok) throw new Error("Failed to load schema");
  return await r.json();
}

async function loadImagesList() {
  const r = await fetch("/images-list");
  if (!r.ok) throw new Error("Failed to load images list");
  return await r.json();
}

async function submitCurrent() {
  const annotatorId = getAnnotatorId();
  if (!annotatorId) {
    alert("Please enter Annotator ID");
    return;
  }

  const answers = collectAnswers();

  const payload = {
    image_id: images[idx],
    annotator_id: annotatorId,
    answers
  };

  const r = await fetch("/annotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!r.ok) {
    const txt = await r.text();
    alert("Submit failed: " + txt);
    return;
  }

  // advance
  if (idx < images.length - 1) idx += 1;

  saveProgress(annotatorId);
  // reset choices
  document.querySelectorAll("#questions input").forEach(x => (x.checked = false));
  renderImage();
}

// ---- wire ----
btnSubmit?.addEventListener("click", (e) => {
  e.preventDefault();
  submitCurrent();
});

btnResume?.addEventListener("click", (e) => {
  e.preventDefault();
  const annotatorId = getAnnotatorId();
  if (!annotatorId) {
    alert("Please enter Annotator ID");
    return;
  }
  idx = Math.min(loadProgress(annotatorId), Math.max(images.length - 1, 0));
  renderImage();
});

// ---- init ----
(async function init() {
  try {
    schema = await loadSchema();
    images = await loadImagesList();
    buildQuestionUI();
    renderImage();
  } catch (err) {
    setStatus(String(err));
  }
})();
