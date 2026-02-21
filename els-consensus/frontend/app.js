let images = [];
let schema = {};
let index = 0;

async function init() {
  images = await fetch("/images-list").then(r => r.json());
  schema = await fetch("/schema").then(r => r.json());
  render();
}

function render() {
  if (index >= images.length) {
    document.body.innerHTML = "<h2>All images annotated 🎉</h2>";
    return;
  }

  document.getElementById("els-image").src = "/images/" + images[index];

  const qDiv = document.getElementById("questions");
  qDiv.innerHTML = "";

  for (const [q, spec] of Object.entries(schema)) {
    const div = document.createElement("div");
    div.innerHTML = `<h4>${q}</h4>`;

    spec.options.forEach(opt => {
      const input = document.createElement("input");
      input.type = spec.type === "multi" ? "checkbox" : "radio";
      input.name = q;
      input.value = opt;

      div.appendChild(input);
      div.appendChild(document.createTextNode(opt));
      div.appendChild(document.createElement("br"));
    });

    qDiv.appendChild(div);
  }
}

async function submitAnnotation() {
  const annotator = document.getElementById("annotator").value;
  if (!annotator) {
    alert("Annotator ID required");
    return;
  }

  const answers = {};
  for (const q in schema) {
    const inputs = document.querySelectorAll(`[name="${q}"]`);
    const vals = [];
    inputs.forEach(i => {
      if (i.checked) vals.push(i.value);
    });
    answers[q] = schema[q].type === "multi" ? vals : vals[0];
  }

  await fetch("/annotate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      image_id: images[index],
      annotator_id: annotator,
      answers: answers
    })
  });

  index++;
  render();
}

init();
