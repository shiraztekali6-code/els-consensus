let schema = null;
let images = [];
let doneSet = new Set();
let idx = 0;
let isAdmin = false;

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
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase());
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

    // 🔹 Show title only for admin
    if (isAdmin) {
      const title = document.createElement("div");
      title.className = "question-title";
      title.innerText = formatTitle(q);
      wrapper.appendChild(title);
    }

    if (spec.description) {
      const desc = document.createElement("div");
      desc.className = "question-desc";
      desc.innerText = spec.description;
      wrapper.appendChild(desc);
    }

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

function allAnswered(ans) {
  let ok = true;

  document.querySelectorAll(".question-card").forEach(card => {
    card.style.border = "1px solid #e5e7eb";
  });

  for (const [q, spec] of Object.entries(schema)) {

    if (spec.type === "multi" && ans[q].length === 0) ok = false;
    if (spec.type !== "multi" && !ans[q]) ok = false;

    if (!ans[q] || (Array.isArray(ans[q]) && ans[q].length === 0)) {
      document.querySelectorAll(".question-card").forEach(card => {
        if (card.querySelector(`input[data-q="${q}"]`)) {
          card.style.border = "2px solid #e11d48";
        }
      });
    }
  }

  return ok;
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
  if (!allAnswered(answers)) return;

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

// 🔹 Detect admin mode automatically
$("adminToken").addEventListener("input", () => {
  isAdmin = $("adminToken").value.length > 0;
  buildQuestions();
});

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
