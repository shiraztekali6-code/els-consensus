let images = [];
let current = 0;
let schema = {};

async function init() {
  images = await fetch("/images-list").then(r => r.json());
  schema = await fetch("/schema").then(r => r.json());
  loadImage();
}

function loadImage() {
  const imageId = images[current];
  document.getElementById("image-title").innerText = imageId;
  document.getElementById("els-image").src = `/images/${imageId}`;

  const form = document.getElementById("form");
  form.innerHTML = "";

  for (const q in schema) {
    const spec = schema[q];
    const div = document.createElement("div");
    div.innerHTML = `<b>${q}</b><br><small>${spec.description || ""}</small><br>`;

    if (spec.type === "multi") {
      spec.options.forEach(opt => {
        div.innerHTML += `
          <label>
            <input type="checkbox" name="${q}" value="${opt}"> ${opt}
          </label><br>`;
      });
    } else {
      spec.options.forEach(opt => {
        div.innerHTML += `
          <label>
            <input type="radio" name="${q}" value="${opt}" required> ${opt}
          </label><br>`;
      });
    }

    div.innerHTML += "<br>";
    form.appendChild(div);
  }
}

async function submitAnnotation() {
  const annotator = document.getElementById("annotator").value;
  if (!annotator) {
    alert("Please enter annotator ID");
    return;
  }

  const answers = {};
  document.querySelectorAll("input").forEach(el => {
    if (!el.checked) return;
    if (!answers[el.name]) answers[el.name] = [];
    answers[el.name].push(el.value);
  });

  await fetch("/annotate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      image_id: images[current],
      annotator_id: annotator,
      answers: answers
    })
  });

  current++;
  if (current < images.length) {
    loadImage();
  } else {
    document.body.innerHTML = "<h2>All images annotated 🎉</h2>";
  }
}

init();
