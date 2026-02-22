let images = [];
let schema = null;
let doneSet = new Set();
let idx = 0;

const elAnnotator = document.getElementById("annotatorId");
const elImg = document.getElementById("elsImage");
const elQuestions = document.getElementById("questions");
const elCounter = document.getElementById("imgCounter");
const elStatus = document.getElementById("status");
const btnSubmit = document.getElementById("btnSubmit");
const btnResume = document.getElementById("btnResume");

function setStatus(msg) { if (elStatus) elStatus.textContent = msg || ""; }
function getAnnotatorId() { return (elAnnotator?.value || "").trim(); }

function imageUrl(filename) {
  return `/images/${encodeURIComponent(filename)}?v=${Date.now()}`;
}

async function fetchJSON(path) {
  const r = await fetch(path, { cache: "no-store" });
  if (!r.ok) throw new Error(`${path} failed: ${r.status}`);
  return r.json();
}

function buildQuestionUI() {
  elQuestions.innerHTML = "";
  for (const [qKey, spec] of Object.entries(schema)) {
    const box = document.createElement("div");
    box.style.border = "1px solid #ddd";
    box.style.padding = "12px";
    box.style.margin = "12px 0";
    box.style.maxWidth = "720px";

    const title = document.createElement("div");
    title.style.fontWeight = "700";
    title.style.fontSize = "18px";
    title.textContent = qKey;
    box.appendChild(title);

    if (spec.description) {
      const desc = document.createElement("div");
      desc.style.margin = "8px 0 10px";
      desc.textContent = spec.description;
      box.appendChild(desc);
    }

    spec.options.forEach((opt, i) => {
      const row = document.createElement("label");
      row.style.display = "block";
      row.style.margin = "6px 0";

      const input = document.createElement("input");
      input.type = (spec.type === "multi") ? "checkbox" : "radio";
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

function clearSelections() {
  document.querySelectorAll("#questions input").forEach(x => (x.checked = false));
}

function collectAnswers() {
  const answers = {};
  for (const [qKey, spec] of Object.entries(schema)) {
    if (spec.type === "multi") {
      const checked = Array.from(document.querySelectorAll(`input[data-qkey="${qKey}"]:checked`))
        .map(x => x.value);
      answers[qKey] = checked;
    } else {
      const chosen = document.querySelector(`input[data-qkey="${qKey}"]:checked`);
      answers[qKey] = chosen ? chosen.value : "";
    }
  }
  return answers;
}

function validateAllAnswered(answers) {
  for (const [qKey, spec] of Object.entries(schema)) {
    if (spec.type === "multi") {
      if (!Array.isArray(answers[qKey]) || answers[qKey].length === 0) return false;
    } else {
      if (!answers[qKey]) return false;
    }
  }
  return true;
}

function findNextUnannotated(startAt = 0) {
  for (let i = startAt; i < images.length; i++) {
    if (!doneSet.has(images[i])) return i;
  }
  return -1;
}

function renderImage() {
  if (!images.length) {
    setStatus("No images found.");
    elCounter.textContent = "";
    elImg.removeAttribute("src");
    return;
  }

  if (idx < 0 || idx >= images.length) idx = 0;

  const filename = images[idx];
  elCounter.textContent = `Image ${idx + 1} / ${images.length} (${filename})`;
  elImg.src = imageUrl(filename);
}

async function loadDoneForAnnotator(annotatorId) {
  const doneList = await fetchJSON(`/annotated/${encodeURIComponent(annotatorId)}`);
  doneSet = new Set(doneList);
}

async function resume() {
  const annotatorId = getAnnotatorId();
  if (!annotatorId) {
    alert("Please enter Annotator ID");
    return;
  }

  localStorage.setItem("els.lastAnnotator", annotatorId);

  await loadDoneForAnnotator(annotatorId);

  const nextIdx = findNextUnannotated(0);
  if (nextIdx === -1) {
    elImg.removeAttribute("src");
    elQuestions.innerHTML = "";
    elCounter.textContent = "All images annotated 🎉";
    setStatus("All done 🎉");
    return;
  }

  idx = nextIdx;
  clearSelections();
  renderImage();
  setStatus("Resumed ✔");
}

async function submitAndNext() {
  const annotatorId = getAnnotatorId();
  if (!annotatorId) {
    alert("Please enter Annotator ID");
    return;
  }

  const answers = collectAnswers();
  if (!validateAllAnswered(answers)) {
    alert("Please answer ALL questions before continuing.");
    return;
  }

  const payload = {
    image_id: images[idx],
    annotator_id: annotatorId,
    answers
  };

  setStatus("Saving...");
  const r = await fetch("/annotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!r.ok) {
    const txt = await r.text();
    alert("Submit failed: " + txt);
    setStatus("Save failed.");
    return;
  }

  // mark done locally + find next
  doneSet.add(images[idx]);

  const nextIdx = findNextUnannotated(idx + 1);
  if (nextIdx === -1) {
    elImg.removeAttribute("src");
    elQuestions.innerHTML = "";
    elCounter.textContent = "All images annotated 🎉";
    setStatus("All done 🎉");
    return;
  }

  idx = nextIdx;
  clearSelections();
  renderImage();
  setStatus("Saved ✔");
}

btnResume?.addEventListener("click", (e) => { e.preventDefault(); resume(); });
btnSubmit?.addEventListener("click", (e) => { e.preventDefault(); submitAndNext(); });

(async function init() {
  try {
    schema = await fetchJSON("/schema");
    images = await fetchJSON("/images-list");
    buildQuestionUI();
    renderImage();

    const last = localStorage.getItem("els.lastAnnotator");
    if (last) elAnnotator.value = last;

    // Resume automatically on refresh if annotator exists
    if (last) {
      await resume();
    }
  } catch (e) {
    setStatus(String(e));
  }
})();
