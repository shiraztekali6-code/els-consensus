let schema = null;
let images = [];
let doneSet = new Set();
let idx = 0;

const $ = id => document.getElementById(id);

async function fetchJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`${url} failed`);
  return r.json();
}

function imageUrl(name) {
  return `/images/${encodeURIComponent(name)}?v=${Date.now()}`;
}

function buildQuestions() {
  $("questions").innerHTML = `
    <div style="border:1px solid #ccc;padding:10px;margin-bottom:10px;">
      <b>Color Legend</b><br>
      Yellow = B cells<br>
      Red = T cells<br>
      Green = Proliferating cells (Ki67+)
    </div>
  `;

  for (const [q, spec] of Object.entries(schema)) {
    const fs = document.createElement("fieldset");
    fs.innerHTML = `<legend>${q}</legend><p>${spec.description || ""}</p>`;
    spec.options.forEach(opt => {
      const l = document.createElement("label");
      const i = document.createElement("input");
      i.type = spec.type === "multi" ? "checkbox" : "radio";
      i.name = q;
      i.value = opt;
      i.dataset.q = q;
      l.appendChild(i);
      l.append(" " + opt);
      fs.appendChild(l);
      fs.appendChild(document.createElement("br"));
    });
    $("questions").appendChild(fs);
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

function allAnswered(ans) {
  for (const [q, spec] of Object.entries(schema)) {
    if (spec.type === "multi" && ans[q].length === 0) return false;
    if (spec.type !== "multi" && !ans[q]) return false;
  }
  return true;
}

async function resume() {
  const annotator = $("annotatorId").value.trim();
  if (!annotator) return alert("Annotator ID required");

  localStorage.setItem("els.annotator", annotator);

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
  if (!annotator) return alert("Annotator ID required");

  const answers = collectAnswers();
  if (!allAnswered(answers)) return alert("Answer all questions");

  await fetch("/annotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_id: images[idx],
      annotator_id: annotator,
      answers
    })
  });

  doneSet.add(images[idx]);
  await resume();
}

function downloadCSV() {
  const t = $("adminToken").value;
  if (!t) return alert("Admin token required");
  window.open(`/admin/export/annotations?token=${encodeURIComponent(t)}`, "_blank");
}

$("btnResume").onclick = resume;
$("btnSubmit").onclick = submit;

(async () => {
  schema = await fetchJSON("/schema");
  images = await fetchJSON("/images-list");
  buildQuestions();

  const last = localStorage.getItem("els.annotator");
  if (last) {
    $("annotatorId").value = last;
    await resume();
  }
})();
