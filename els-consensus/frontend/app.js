let images = [];
let schema = {};
let index = 0;

// ---------- init ----------
async function init() {
  const annotator = localStorage.getItem("annotator_id");
  if (annotator) {
    document.getElementById("annotator").value = annotator;
    await loadForAnnotator(annotator);
  } else {
    schema = await fetch("/schema").then(r => r.json());
  }
}

// ---------- load images for annotator ----------
async function loadForAnnotator(annotator) {
  localStorage.setItem("annotator_id", annotator);

  schema = await fetch("/schema").then(r => r.json());
  images = await fetch(`/images-list/${annotator}`).then(r => r.json());

  if (images.length === 0) {
    document.body.innerHTML = "<h2>All images annotated 🎉</h2>";
    return;
  }

  index = 0;
  render();
}

// ---------- render ----------
function render() {
  document.getElementById("error").innerText = "";

  document.getElementById("els-image").src = "/images/" + images[index];
  document.getElementById("counter").innerText =
    `Image ${index + 1} / ${images.length}`;

  buildForm();
}

// ---------- build form ----------
function buildForm() {
  const form = document.getElementById("annotation-form");
  form.innerHTML = "";

  for (const [qKey, qSpec] of Object.entries(schema)) {
    const fs = document.createElement("fieldset");
    const legend = document.createElement("legend");
    legend.innerText = qKey;
    fs.appendChild(legend);

    if (qSpec.description) {
      const p = document.createElement("p");
      p.innerText = qSpec.description;
      fs.appendChild(p);
    }

    qSpec.options.forEach(opt => {
      const label = document.createElement("label");
      const input = document.createElement("input");

      input.type = qSpec.type === "multi" ? "checkbox" : "radio";
      input.name = qKey;
      input.value = opt;

      label.appendChild(input);
      label.appendChild(document.createTextNode(" " + opt));

      fs.appendChild(label);
      fs.appendChild(document.createElement("br"));
    });

    form.appendChild(fs);
  }
}

// ---------- collect answers ----------
function collectAnswers() {
  const answers = {};

  for (const [qKey, qSpec] of Object.entries(schema)) {
    const inputs = document.querySelectorAll(`[name="${qKey}"]`);
    const selected = [];

    inputs.forEach(i => {
      if (i.checked) selected.push(i.value);
    });

    if (qSpec.type === "multi") {
      if (selected.length === 0) return null;
      answers[qKey] = selected;
    } else {
      if (selected.length !== 1) return null;
      answers[qKey] = selected[0];
    }
  }

  return answers;
}

// ---------- submit ----------
async function submitAndNext() {
  const annotator = document.getElementById("annotator").value.trim();
  if (!annotator) {
    document.getElementById("error").innerText =
      "Annotator ID is required.";
    return;
  }

  // אם זה annotator חדש — טוענים לו רשימת תמונות
  if (images.length === 0) {
    await loadForAnnotator(annotator);
    return;
  }

  const answers = collectAnswers();
  if (answers === null) {
    document.getElementById("error").innerText =
      "Please answer ALL questions before continuing.";
    return;
  }

  const payload = {
    image_id: images[index],
    annotator_id: annotator,
    answers: answers
  };

  const res = await fetch("/annotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    document.getElementById("error").innerText =
      "Failed to save annotation. Please try again.";
    return;
  }

  index++;
  if (index >= images.length) {
    document.body.innerHTML = "<h2>All images annotated 🎉</h2>";
    return;
  }

  render();
}

init();
