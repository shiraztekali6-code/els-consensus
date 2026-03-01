const API_BASE = window.location.origin;

let images = [];
let currentIndex = 0;
let annotatorId = null;


// ---------- Fetch Helper ----------
async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}


// ---------- Load Schema ----------
async function loadSchema() {
  const schema = await fetchJSON(`${API_BASE}/schema`);
  renderQuestions(schema);
}


// ---------- Load Images ----------
async function loadImages() {
  images = await fetchJSON(`${API_BASE}/images-list`);
}


// ---------- Resume ----------
async function resume(userId) {
  const done = await fetchJSON(`${API_BASE}/annotated/${userId}`);
  currentIndex = done.length;
}


// ---------- Render Image ----------
function renderImage() {
  if (!images.length || currentIndex >= images.length) return;

  const imageName = images[currentIndex];
  document.getElementById("elsImage").src = `${API_BASE}/images/${imageName}`;
  document.getElementById("imgCounter").innerText =
    `Image ${currentIndex + 1} of ${images.length}`;
}


// ---------- Render Questions ----------
function renderQuestions(schema) {
  const container = document.getElementById("questions");
  container.innerHTML = "";

  for (const key in schema) {
    const q = schema[key];

    const card = document.createElement("div");
    card.style.marginBottom = "20px";

    const title = document.createElement("div");
    title.innerHTML = `<b>${key}</b>`;
    card.appendChild(title);

    if (q.description) {
      const desc = document.createElement("div");
      desc.style.fontSize = "13px";
      desc.style.color = "#666";
      desc.innerText = q.description;
      card.appendChild(desc);
    }

    q.options.forEach(option => {
      const label = document.createElement("label");
      label.style.display = "block";

      const input = document.createElement("input");
      input.type = q.type === "multi" ? "checkbox" : "radio";
      input.name = key;
      input.value = option;

      label.appendChild(input);
      label.appendChild(document.createTextNode(" " + option));
      card.appendChild(label);
    });

    container.appendChild(card);
  }
}


// ---------- Collect Answers ----------
function collectAnswers(schema) {
  const answers = {};

  for (const key in schema) {
    const inputs = document.querySelectorAll(`[name="${key}"]`);
    const selected = [];

    inputs.forEach(input => {
      if (input.checked) selected.push(input.value);
    });

    if (schema[key].type === "single") {
      answers[key] = selected[0];
    } else {
      answers[key] = selected;
    }
  }

  return answers;
}


// ---------- Submit ----------
async function submitAnnotation() {
  const schema = await fetchJSON(`${API_BASE}/schema`);
  const answers = collectAnswers(schema);

  await fetch(`${API_BASE}/annotate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_id: images[currentIndex],
      annotator_id: annotatorId,
      answers: answers
    })
  });

  currentIndex++;
  renderImage();
}


// ---------- Download CSV ----------
function downloadCSV() {
  const token = document.getElementById("adminToken").value;
  window.location.href = `${API_BASE}/admin/export/annotations?token=${token}`;
}


// ---------- Login Button ----------
document.getElementById("btnResume").addEventListener("click", async () => {

  const id = document.getElementById("annotatorId").value.trim();
  if (!id) {
    alert("Please enter Annotator ID");
    return;
  }

  annotatorId = id;

  await loadImages();
  await loadSchema();
  await resume(id);
  renderImage();

  document.getElementById("login-screen").style.display = "none";
  document.getElementById("annotation-screen").style.display = "block";
});


// ---------- Submit Button ----------
document.getElementById("btnSubmit")
  .addEventListener("click", submitAnnotation);
