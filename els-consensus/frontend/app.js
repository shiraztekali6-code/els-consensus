// ==============================
// STATE
// ==============================

let schema = null;
let images = [];
let idx = 0;

const ADMIN_TOKEN = "els-admin-shiraz";

const $ = (id) => document.getElementById(id);

// ==============================
// UTIL
// ==============================

async function fetchJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`${url} failed`);
  return r.json();
}

function imageUrl(name) {
  return `/images/${encodeURIComponent(name)}?v=${Date.now()}`;
}

// ==============================
// BUILD QUESTIONS
// ==============================

function buildQuestions() {

  $("questions").innerHTML = "";

  for (const [q, spec] of Object.entries(schema)) {

    const wrapper = document.createElement("div");
    wrapper.style.border = "1px solid #ddd";
    wrapper.style.borderRadius = "10px";
    wrapper.style.padding = "12px";
    wrapper.style.marginBottom = "15px";
    wrapper.style.background = "#f9fafb";

    const title = document.createElement("div");
    title.style.fontWeight = "600";
    title.style.marginBottom = "10px";
    title.style.fontSize = "16px";
    title.innerText = q;

    wrapper.appendChild(title);

    spec.options.forEach(opt => {

      const label = document.createElement("label");
      label.style.display = "block";
      label.style.marginBottom = "6px";

      const input = document.createElement("input");
      input.type = spec.type === "multi" ? "checkbox" : "radio";
      input.name = q;
      input.value = opt;
      input.dataset.q = q;
      input.style.marginRight = "6px";

      label.appendChild(input);
      label.append(opt);

      wrapper.appendChild(label);
    });

    $("questions").appendChild(wrapper);
  }
}

// ==============================
// ANSWERS
// ==============================

function collectAnswers() {

  const answers = {};

  for (const [q, spec] of Object.entries(schema)) {

    if (spec.type === "multi") {
      answers[q] = Array.from(
        document.querySelectorAll(`input[data-q="${q}"]:checked`)
      ).map(x => x.value);
    } else {
      const v = document.querySelector(`input[data-q="${q}"]:checked`);
      answers[q] = v ? v.value : "";
    }
  }

  return answers;
}

function allAnswered(ans) {

  for (const [q, spec] of Object.entries(schema)) {

    if (spec.type === "multi" && ans[q].length === 0) return false;
    if (spec.type !== "multi" && !ans[q]) return false;
  }

  return true;
}

// ==============================
// RENDER IMAGE
// ==============================

function render() {

  $("elsImage").src = imageUrl(images[idx]);
  $("imgCounter").innerText = `Image ${idx + 1} / ${images.length}`;

  document.querySelectorAll("#questions input")
    .forEach(i => i.checked = false);
}

// ==============================
// SUBMIT
// ==============================

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

  idx++;
  if (idx >= images.length) {
    alert("All images completed");
    return;
  }

  render();
}

// ==============================
// ADMIN DOWNLOAD
// ==============================

function downloadAll() {

  const token = $("annotatorId").value.trim();

  if (token !== ADMIN_TOKEN) {
    alert("Admin only");
    return;
  }

  window.open(`/admin/export/raw?token=${token}`, "_blank");
  window.open(`/admin/export/consensus?token=${token}`, "_blank");
}

// ==============================
// LOGIN / MODE SWITCH
// ==============================

function enter() {

  const annotator = $("annotatorId").value.trim();
  if (!annotator) return alert("Annotator ID required");

  if (annotator === ADMIN_TOKEN) {
    $("adminPanel").style.display = "block";
  } else {
    $("adminPanel").style.display = "none";
  }

  render();
}

// ==============================
// INIT
// ==============================

(async () => {

  schema = await fetchJSON("/schema");
  images = await fetchJSON("/images-list");

  buildQuestions();

  $("btnSubmit").onclick = submit;
  $("btnEnter").onclick = enter;
  $("btnDownload").onclick = downloadAll;

})();
