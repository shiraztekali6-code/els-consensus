let schema = null;
let images = [];
let doneSet = new Set();
let idx = 0;

const ADMIN_USERNAME = "ADMIN_SECRET_2025"; // 🔐 תשני את זה

const $ = id => document.getElementById(id);

async function fetchJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`${url} failed`);
  return r.json();
}

function imageUrl(name) {
  return `/images/${encodeURIComponent(name)}?v=${Date.now()}`;
}

function formatTitle(key) {
  return key.replace(/_/g, " ");
}

function showAdminScreen() {
  $("mainContent").innerHTML = `
    <div class="admin-screen">
      <div class="admin-title">Admin Panel</div>
      <p><b>Internal Question Keys (CSV column names):</b></p>
      <ul>
        ${Object.keys(schema).map(k => `<li>${k}</li>`).join("")}
      </ul>
      <br>
      <button onclick="downloadCSV()">Download All Annotations (CSV)</button>
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
        <div id="questions"></div>
        <button id="btnSubmit">Submit & Next</button>
      </div>
    </div>
  `;

  buildQuestions();
  $("btnSubmit").onclick = submit;
}

function buildQuestions() {
  $("questions").innerHTML = `
    <div class="legend-box">
      <b>Color Legend</b><br>
      Yellow = B cells<br>
      Red = T cells<br>
      Green = Proliferating cells (Ki67+)
    </div>
  `;

  for (const [q, spec] of Object.entries(schema)) {

    const wrapper = document.createElement("div");
    wrapper.className = "question-card";

    const title = document.createElement("div");
    title.className = "question-title";
    title.innerText = spec.description || formatTitle(q);

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
      input.dataset.q = q;

      label.appendChild(input);
      label.append(" " + opt);
      options.appendChild(label);
    });

    wrapper.appendChild(options);
    $("questions").appendChild(wrapper);
  }
}

function collectAnswers() {
  const a = {};
  for (const [q, spec] of Object.entries(schema)) {
    if (spec.type === "multi") {
      a[q] = Array.from(document.querySelectorAll(`input[data-q="${q}"]:checked`)).map(x => x.value);
    } else {
      const v = document.querySelector(`input[data-q="${q}"]:checked`);
      a[q] = v ? v.value : "";
    }
  }
  return a;
}

async function resume() {
  const annotator = $("annotatorId").value.trim();
  if (!annotator) return alert("Annotator ID required");

  if (annotator === ADMIN_USERNAME) {
    showAdminScreen();
    return;
  }

  showAnnotatorScreen();

  const done = await fetchJSON(`/annotated/${annotator}`);
  doneSet = new Set(done);

  idx = images.findIndex(x => !doneSet.has(x));

  if (idx === -1) {
    $("elsImage").removeAttribute("src");
    $("imgCounter").innerText = "All images annotated 🎉";
    return;
  }

  render();
}

function render() {
  $("elsImage").src = imageUrl(images[idx]);
  $("imgCounter").innerText = `Image ${idx + 1} / ${images.length}`;
  document.querySelectorAll("#questions input").forEach(i => i.checked = false);
}

async function submit() {
  const annotator = $("annotatorId").value.trim();
  const answers = collectAnswers();

  await fetch("/annotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_id: images[idx],
      annotator_id: annotator,
      answers
    })
  });

  await resume();
}

function downloadCSV() {
  window.open(`/admin/export/annotations?token=${ADMIN_USERNAME}`, "_blank");
}

$("btnResume").onclick = resume;

(async () => {
  schema = await fetchJSON("/schema");
  images = await fetchJSON("/images-list");
})();
