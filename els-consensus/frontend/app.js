const API_BASE = window.location.origin;

let images = [];
let currentIndex = 0;
let annotatorId = null;
let schema = null;

// ===============================
// HELPERS
// ===============================

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`${url} failed (${res.status})`);
  return res.json();
}

// ===============================
// LOAD SCHEMA
// ===============================

async function loadSchema() {
  schema = await fetchJSON(`${API_BASE}/schema`);
  buildQuestions();
}

function buildQuestions() {
  const container = document.getElementById("questions");
  container.innerHTML = "";

  Object.entries(schema).forEach(([key, spec]) => {
    const card = document.createElement("div");
    card.className = "question-card";

    const title = document.createElement("div");
    title.className = "question-title";
    title.textContent = key;
    card.appendChild(title);

    if (spec.description) {
      const desc = document.createElement("div");
      desc.className = "question-desc";
      desc.textContent = spec.description;
      card.appendChild(desc);
    }

    const optionsRow = document.createElement("div");
    optionsRow.className = "options-row";

    spec.options.forEach(opt => {
      const label = document.createElement("label");
      label.className = "option-label";

      const input = document.createElement("input");
      input.type = spec.type === "multi" ? "checkbox" : "radio";
      input.name = key;
      input.value = opt;

      label.appendChild(input);
      label.appendChild(document.createTextNode(opt));
      optionsRow.appendChild(label);
    });

    card.appendChild(optionsRow);
    container.appendChild(card);
  });
}

// ===============================
// LOAD IMAGES FOR USER (RESUME BUILT-IN)
// ===============================

async function loadImagesForUser() {
  images = await fetchJSON(`${API_BASE}/images-list/${annotatorId}`);
  currentIndex = 0;
  renderImage();
}

// ===============================
// RENDER IMAGE
// ===============================

function renderImage() {
  if (!images.length) {
    document.getElementById("elsImage").src = "";
    document.getElementById("imgCounter").innerText = "No more images to annotate.";
    return;
  }

  const imageName = images[currentIndex];
  document.getElementById("elsImage").src = `${API_BASE}/images/${imageName}`;
  document.getElementById("imgCounter").innerText =
    `Image ${currentIndex + 1} of ${images.length}`;
}

// ===============================
// COLLECT ANSWERS
// ===============================

function collectAnswers() {
  const answers = {};

  Object.keys(schema).forEach(key => {
    const inputs = document.querySelectorAll(`input[name="${key}"]`);
    const selected = [];

    inputs.forEach(input => {
      if (input.checked) selected.push(input.value);
    });

    if (schema[key].type === "single") {
      answers[key] = selected[0] || "";
    } else {
      answers[key] = selected;
    }
  });

  return answers;
}

// ===============================
// SUBMIT
// ===============================

async function submitAnnotation() {
  if (!images.length) return;

  const payload = {
    image_id: images[currentIndex],
    annotator_id: annotatorId,
    answers: collectAnswers()
  };

  await fetchJSON(`${API_BASE}/annotate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  currentIndex++;
  renderImage();
}

// ===============================
// ADMIN CSV
// ===============================

function downloadCSV() {
  const token = document.getElementById("adminToken").value;
  window.open(`${API_BASE}/admin/export/annotations?token=${token}`, "_blank");
}

// ===============================
// EVENTS
// ===============================

document.getElementById("btnResume").addEventListener("click", async () => {
  annotatorId = document.getElementById("annotatorId").value.trim();
  if (!annotatorId) return alert("Please enter Annotator ID.");

  await loadSchema();
  await loadImagesForUser();
});

document.getElementById("btnSubmit").addEventListener("click", submitAnnotation);
