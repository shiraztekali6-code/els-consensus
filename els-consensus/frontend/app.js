let schema = null;
let images = [];
let doneSet = new Set();
let idx = 0;

const ADMIN_PASSWORD = "YOUR_SECRET_PASSWORD"; // לשנות!

const $ = id => document.getElementById(id);

async function fetchJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`${url} failed`);
  return r.json();
}

function imageUrl(name) {
  return `/images/${encodeURIComponent(name)}?v=${Date.now()}`;
}

function showAdminScreen() {
  $("mainContent").innerHTML = `
    <div class="admin-panel">
      <h2>Admin Panel</h2>
      <p>CSV Column Keys:</p>
      ${Object.keys(schema).map(k => `
        <div class="admin-key">${k}</div>
      `).join("")}
      <br><br>
      <button onclick="downloadCSV()">Download Annotations CSV</button>
    </div>
  `;
}

function showAnnotatorScreen() {
  $("mainContent").innerHTML = `
    <div class="layout">
      <div class="image-panel">
        <img id="elsImage">
        <div id="imgCounter" style="margin-top:10px;"></div>
      </div>
      <div class="annotation-panel">
        <div class="legend-box">
          <b>Color legend:</b>
          Yellow = B cells,
          Red = T cells,
          Green = Proliferating cells (Ki67+)
        </div>
        <div id="questions"></div>
        <button id="btnSubmit">Submit & Next</button>
      </div>
    </div>
  `;

  buildQuestions(false);
  $("btnSubmit").onclick = submit;
}

function buildQuestions(isAdmin) {
  for (const [q, spec] of Object.entries(schema)) {

    const wrapper = document.createElement("div");
    wrapper.className = "question-card";

    if (isAdmin) {
      const key = document.createElement("div");
      key.className = "admin-key";
      key.innerText = q;
      wrapper.appendChild(key);
    }

    const title = document.createElement("div");
    title.className = "question-title";
    title.innerText = spec.description;
    wrapper.appendChild(title);

    const options = document.createElement("div");
    options.className = "options-row";

    spec.options.forEach(opt => {
      const label = document.createElement("label");
      label.className = "option-label";

      const input = document.createElement("input");
      input.type = spec.type === "multi" ? "checkbox" : "radio";
      input.name = q;
      input.value = opt;

      label.appendChild(input);
      label.append(" " + opt);
      options.appendChild(label);
    });

    wrapper.appendChild(options);
    $("questions").appendChild(wrapper);
  }
}

async function resume() {
  const annotator = $("annotatorId").value.trim();
  if (!annotator) return alert("Annotator ID required");

  if (annotator === ADMIN_PASSWORD) {
    showAdminScreen();
    return;
  }

  showAnnotatorScreen();

  const done = await fetchJSON(`/annotated/${annotator}`);
  doneSet = new Set(done);

  idx = images.findIndex(x => !doneSet.has(x));
  render();
}

function render() {
  $("elsImage").src = imageUrl(images[idx]);
  $("imgCounter").innerText = `Image ${idx + 1} / ${images.length}`;
}

async function submit() {
  const annotator = $("annotatorId").value.trim();
  const answers = {};

  for (const [q, spec] of Object.entries(schema)) {
    const checked = document.querySelectorAll(`input[name="${q}"]:checked`);
    answers[q] = spec.type === "multi"
      ? Array.from(checked).map(x => x.value)
      : (checked[0] ? checked[0].value : "");
  }

  await fetch("/annotate", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      image_id: images[idx],
      annotator_id: annotator,
      answers
    })
  });

  idx++;
  render();
}

function downloadCSV() {
  window.open(`/admin/export/annotations?token=${ADMIN_PASSWORD}`, "_blank");
}

$("btnResume").onclick = resume;

(async () => {
  schema = await fetchJSON("/schema");
  images = await fetchJSON("/images-list");
})();
