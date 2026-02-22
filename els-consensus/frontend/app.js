// ---------- Helpers ----------
const $ = (id) => document.getElementById(id);

const LS_KEY_ANNOTATOR = "els.annotator_id";
const lsKeyIndex = (annotatorId) => `els.index.${annotatorId}`;
const lsKeyImage = (annotatorId) => `els.image.${annotatorId}`;

async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return await r.json();
}

function setStatus(msg) {
  $("status").textContent = msg || "";
}

function getAnnotatorId() {
  return ($("annotatorId").value || "").trim();
}

function persistAnnotatorId(id) {
  localStorage.setItem(LS_KEY_ANNOTATOR, id);
}

function loadPersistedAnnotatorId() {
  return localStorage.getItem(LS_KEY_ANNOTATOR) || "";
}

function persistPosition(annotatorId, index, imageId) {
  localStorage.setItem(lsKeyIndex(annotatorId), String(index));
  localStorage.setItem(lsKeyImage(annotatorId), imageId);
}

function loadPersistedPosition(annotatorId) {
  const idx = parseInt(localStorage.getItem(lsKeyIndex(annotatorId) || "") || "0", 10);
  const img = localStorage.getItem(lsKeyImage(annotatorId) || "") || "";
  return { idx: isNaN(idx) ? 0 : idx, img };
}

function clearForm(container) {
  container.innerHTML = "";
}

function buildQuestionUI(schema, container) {
  clearForm(container);

  // Legend
  const legend = document.createElement("div");
  legend.innerHTML = `
    <div style="border:1px solid #ddd;padding:10px;margin:10px 0;">
      <b>Color Legend</b><br/>
      Yellow = B cells<br/>
      Red = T cells<br/>
      Green = Proliferating cells (Ki67+)
    </div>
  `;
  container.appendChild(legend);

  // Questions
  Object.entries(schema).forEach(([qKey, spec]) => {
    const box = document.createElement("div");
    box.style.border = "1px solid #ccc";
    box.style.padding = "10px";
    box.style.margin = "10px 0";

    const title = document.createElement("div");
    title.innerHTML = `<b>${qKey}</b>`;
    box.appendChild(title);

    if (spec.description) {
      const desc = document.createElement("div");
      desc.style.margin = "6px 0 10px 0";
      desc.textContent = spec.description;
      box.appendChild(desc);
    }

    if (spec.type === "multi") {
      spec.options.forEach((opt, i) => {
        const id = `${qKey}__${i}`;
        const row = document.createElement("div");
        row.innerHTML = `
          <label>
            <input type="checkbox" id="${id}" data-q="${qKey}" data-type="multi" value="${opt}">
            ${opt}
          </label>
        `;
        box.appendChild(row);
      });
    } else if (spec.type === "single") {
      spec.options.forEach((opt, i) => {
        const id = `${qKey}__${i}`;
        const row = document.createElement("div");
        row.innerHTML = `
          <label>
            <input type="radio" name="${qKey}" id="${id}" data-q="${qKey}" data-type="single" value="${opt}">
            ${opt}
          </label>
        `;
        box.appendChild(row);
      });
    } else if (spec.type === "boolean") {
      const row = document.createElement("div");
      row.innerHTML = `
        <label><input type="radio" name="${qKey}" data-q="${qKey}" data-type="boolean" value="true"> True</label>
        &nbsp;&nbsp;
        <label><input type="radio" name="${qKey}" data-q="${qKey}" data-type="boolean" value="false"> False</label>
      `;
      box.appendChild(row);
    }

    container.appendChild(box);
  });
}

function collectAnswers(schema) {
  const answers = {};
  for (const [qKey, spec] of Object.entries(schema)) {
    if (spec.type === "multi") {
      const checked = Array.from(document.querySelectorAll(`input[data-q="${qKey}"][data-type="multi"]:checked`));
      answers[qKey] = checked.map(x => x.value);
    } else if (spec.type === "single") {
      const sel = document.querySelector(`input[name="${qKey}"][data-type="single"]:checked`);
      answers[qKey] = sel ? sel.value : null;
    } else if (spec.type === "boolean") {
      const sel = document.querySelector(`input[name="${qKey}"][data-type="boolean"]:checked`);
      answers[qKey] = sel ? (sel.value === "true") : null;
    }
  }
  return answers;
}

function validateClientSide(schema, answers) {
  for (const [qKey, spec] of Object.entries(schema)) {
    const v = answers[qKey];

    if (spec.type === "multi") {
      if (!Array.isArray(v) || v.length === 0) return `Please answer: ${qKey}`;
    } else {
      if (v === null || v === undefined) return `Please answer: ${qKey}`;
    }
  }
  return null;
}


// ---------- App State ----------
let SCHEMA = null;
let IMAGES = [];
let DONE_SET = new Set();
let currentIndex = 0;
let currentImageId = "";


function setImage(imageId) {
  currentImageId = imageId;
  $("elsImage").src = `/images/${encodeURIComponent(imageId)}`;
  $("imgCounter").textContent = `Image ${currentIndex + 1} / ${IMAGES.length}`;
}

function findNextUnannotated(startIdx = 0) {
  for (let i = startIdx; i < IMAGES.length; i++) {
    if (!DONE_SET.has(IMAGES[i])) return i;
  }
  return -1;
}

async function loadAnnotatorProgress(annotatorId) {
  const done = await fetchJSON(`/annotated/${encodeURIComponent(annotatorId)}`);
  DONE_SET = new Set(done);
}

async function boot() {
  try {
    SCHEMA = await fetchJSON("/schema");
    IMAGES = await fetchJSON("/images-list");

    buildQuestionUI(SCHEMA, $("questions"));

    // restore annotator id
    const savedId = loadPersistedAnnotatorId();
    if (savedId) $("annotatorId").value = savedId;

    setStatus("Ready. Enter Annotator ID.");
  } catch (e) {
    console.error(e);
    setStatus("Failed to load schema/images. Check server endpoints.");
  }
}

async function startOrResume() {
  const annotatorId = getAnnotatorId();
  if (!annotatorId) {
    alert("Please enter Annotator ID");
    return;
  }

  persistAnnotatorId(annotatorId);
  await loadAnnotatorProgress(annotatorId);

  // try restore last position
  const { idx: savedIdx, img: savedImg } = loadPersistedPosition(annotatorId);

  // if saved image exists and not done -> return to it
  if (savedImg && IMAGES.includes(savedImg) && !DONE_SET.has(savedImg)) {
    currentIndex = IMAGES.indexOf(savedImg);
    setImage(savedImg);
    setStatus(`Resumed at ${savedImg}`);
    return;
  }

  // else, start from saved index but find first unannotated from there
  const startIdx = Math.min(Math.max(savedIdx, 0), IMAGES.length - 1);
  const nextIdx = findNextUnannotated(startIdx);

  if (nextIdx === -1) {
    $("elsImage").src = "";
    $("imgCounter").textContent = `All images annotated 🎉`;
    setStatus("All done 🎉");
    return;
  }

  currentIndex = nextIdx;
  setImage(IMAGES[currentIndex]);
  persistPosition(annotatorId, currentIndex, currentImageId);
  setStatus(`Loaded ${currentImageId}`);
}

async function submitAndNext() {
  const annotatorId = getAnnotatorId();
  if (!annotatorId) {
    alert("Please enter Annotator ID");
    return;
  }

  // Ensure we resumed/loaded progress at least once
  if (!SCHEMA || IMAGES.length === 0) {
    alert("Not ready yet. Refresh page.");
    return;
  }
  if (!currentImageId) {
    await startOrResume();
    if (!currentImageId) return;
  }

  const answers = collectAnswers(SCHEMA);
  const err = validateClientSide(SCHEMA, answers);
  if (err) {
    alert(err);
    return;
  }

  const payload = {
    image_id: currentImageId,
    annotator_id: annotatorId,
    answers: answers
  };

  setStatus("Saving...");
  const r = await fetch("/annotate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });

  if (!r.ok) {
    const txt = await r.text();
    console.error(txt);
    alert("Save failed. Check server response.");
    setStatus("Save failed.");
    return;
  }

  DONE_SET.add(currentImageId);

  // move to next unannotated
  const nextIdx = findNextUnannotated(currentIndex + 1);
  if (nextIdx === -1) {
    $("elsImage").src = "";
    $("imgCounter").textContent = `All images annotated 🎉`;
    persistPosition(annotatorId, IMAGES.length - 1, "");
    setStatus("All done 🎉");
    return;
  }

  currentIndex = nextIdx;
  setImage(IMAGES[currentIndex]);

  // persist position for refresh-resume
  persistPosition(annotatorId, currentIndex, currentImageId);

  setStatus("Saved ✔");
}


// ---------- Wire up ----------
window.addEventListener("load", async () => {
  await boot();

  $("annotatorId").addEventListener("change", () => {
    // only persist the ID; resume happens on button click
    const id = getAnnotatorId();
    if (id) persistAnnotatorId(id);
  });

  $("btnResume").addEventListener("click", startOrResume);
  $("btnSubmit").addEventListener("click", submitAndNext);
});
