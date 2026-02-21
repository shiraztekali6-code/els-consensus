// ===============================
// Global state
// ===============================
let schema = {};
let images = [];
let currentIndex = 0;

// ===============================
// Init
// ===============================
async function init() {
  await loadSchema();
  await loadImages();
  showCurrentImage();
}

// ===============================
// Load schema
// ===============================
async function loadSchema() {
  const res = await fetch("/schema");
  schema = await res.json();
}

// ===============================
// Load images list from backend
// ===============================
async function loadImages() {
  const res = await fetch("/images-list");
  images = await res.json();
}

// ===============================
// Show image + form
// ===============================
function showCurrentImage() {
  if (currentIndex >= images.length) {
    document.body.innerHTML = "<h2>All images annotated 🎉</h2>";
    return;
  }

  const imageName = images[currentIndex];
  document.getElementById("image").src = `/images/${imageName}`;
  document.getElementById("status").innerText =
    `Image ${currentIndex + 1} / ${images.length}`;

  buildForm();
}

// ===============================
// Build form dynamically
// ===============================
function buildForm() {
  const form = document.getElementById("annotationForm");
  form.innerHTML = "";

  for (const [question, spec] of Object.entries(schema)) {
    const div = document.createElement("div");
    div.className = "question";

    div.innerHTML = `<b>${question}</b><br><small>${spec.description || ""}</small><br>`;

    if (spec.type === "multi") {
      spec.options.forEach(opt => {
        div.innerHTML += `
          <label>
            <input type="checkbox" name="${question}" value="${opt}">
            ${opt}
          </label><br>`;
      });
    } else {
      spec.options.forEach(opt => {
        div.innerHTML += `
          <label>
            <input type="radio" name="${question}" value="${opt}" required>
            ${opt}
          </label><br>`;
      });
    }

    div.innerHTML += "<br>";
    form.appendChild(div);
  }
}

// ===============================
// Submit
// ===============================
async function submitAnnotation() {
  const annotatorId = document.getElementById("annotatorId").value.trim();
  if (!annotatorId) {
    alert("Please enter Annotator ID");
    return;
  }

  const answers = {};

  for (const question of Object.keys(schema)) {
    const inputs = document.querySelectorAll(`[name="${question}"]`);
    const values = [];
    inputs.forEach(i => i.checked && values.push(i.value));

    answers[question] =
      schema[question].type === "multi" ? values : values[0] || null;
  }

  await fetch("/annotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_id: images[currentIndex],
      annotator_id: annotatorId,
      answers: answers
    })
  });

  currentIndex++;
  showCurrentImage();
}

init();
