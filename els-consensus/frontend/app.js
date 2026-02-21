const imageId = prompt("Image ID (e.g. ELS_001)");
const annotator = prompt("Your name");

document.getElementById("image-title").innerText = imageId;
document.getElementById("els-image").src = `/images/${imageId}.png`;

fetch("/schema").then(r => r.json()).then(schema => {
  const form = document.getElementById("form");
  for (const q in schema) {
    const div = document.createElement("div");
    div.innerHTML = `<b>${q}</b><br>`;
    schema[q].options.forEach(opt => {
      div.innerHTML += `
        <label>
          <input type="${schema[q].type === "multi" ? "checkbox" : "radio"}"
                 name="${q}" value="${opt}">
          ${opt}
        </label><br>`;
    });
    form.appendChild(div);
  }
});

function submit() {
  const data = {};
  document.querySelectorAll("input").forEach(i => {
    if (i.checked) {
      if (!data[i.name]) data[i.name] = [];
      data[i.name].push(i.value);
    }
  });

  fetch("/annotate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      image_id: imageId,
      annotator_id: annotator,
      answers: data
    })
  }).then(() => alert("Saved"));
}