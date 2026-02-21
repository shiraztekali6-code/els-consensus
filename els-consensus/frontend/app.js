// ===============================
// Global state
// ===============================
let schema = null;
let images = [];
let currentIndex = 0;

// ===============================
// Load everything on page load
// ===============================
async function init() {
  await loadSchema();
  await loadImages();
  showCurrentImage();
}

// ===============================
// Load schema from backend
// ===============================
async function loadSchema() {
  const res = await fetch("/schema");
  if (!res.ok) {
    document.getElementById("status").innerText = "Failed to load schema";
    return;
  }
  schema = await res.json();
}

// ===============================
// Load images list (from /images)
// ===============================
async function loadImages() {
  // Hard-coded image list approach:
  // GitHub/Render does NOT allow directory listing.
  // 👉 You must maintain this list manually or via a text file.

  images = [
    "image1.png",
    "image2.png",
    "image3.png"
  ];

  // If you renamed files – update names here
}

// ===============================
// Display current image + questions
// ===============================
function showCurrentImage() {
  if (currentIndex >= images.length) {
    document.getElementById("status").innerText =
      "All images annotated 🎉";
    document.getElementById("image").style.display = "none";
    document.getElementById("annotationForm").innerHTML = "";
    return;
  }

  const imageName = images[currentIndex];
  document.getElementById("image").src = `/images/${imageName}`;

  buildForm();
}

// ===============================
// Build annotation form dynamically
// ===============================
function buildForm() {
  const form = document.getElementById("annotationForm");
  form.innerHTML = "";

  for (const [question, spec] of Object.entries(schema)) {
    const div = document.createElement("div");
    div.className = "question";

    const title = document.createElement("h3");
    title.innerText = question;
    div.appendChild(title);

    if (spec.description) {
      const desc = document.createElement("p");
      desc.innerText = spec.description;
      div.appendChild(desc);
    }

    if (spec.type === "multi") {
      spec.options.forEach(opt => {
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "checkbox";
        input.name = question;
        input.value = opt;
        label.appendChild(input);
        label.appendChild(document.createTextNode(" " + opt));
        div.appendChild(label);
        div.appendChild(document.createElement("br"));
      });
    } else {
      spec.options.forEach(opt => {
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "radio";
        input.name = question;
        input.value = opt;
        label.appendChild(input);
        label.appendChild(document.createTextNode(" " + opt));
        div.appendChild(label);
        div.appendChild(document.createElement("br"));
      });
    }

    form.appendChild(div);
  }
}

// ===============================
// Submit annotation
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

    inputs.forEach(input => {
      if (input.checked) values.push(input.value);
    });

    if (schema[question].type === "multi") {
      answers[question] = values;
    } else {
      answers[question] = values[0] || null;
    }
  }

  const payload = {
    image_id: images[currentIndex],
    annotator_id: annotatorId,
    answers: answers
  };

  const res = await fetch("/annotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    alert("Failed to submit annotation");
    return;
  }

  currentIndex++;
  showCurrentImage();
}

// ===============================
init();
// ===============================
