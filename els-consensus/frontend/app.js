let SCHEMA = null;
let IMAGES = [];
let currentIndex = 0;
let currentImage = null;

function $(id) {
  return document.getElementById(id);
}

function showError(msg) {
  const el = $("error");
  if (!el) return;
  el.textContent = msg || "";
}

function annotatorId() {
  return ($("annotator")?.value || "").trim();
}

function keyForAnnotator(aid) {
  return `els_progress__${aid}`;
}

function loadProgress(aid) {
  try {
    const raw = localStorage.getItem(keyForAnnotator(aid));
    if (!raw) return { done: {} };
    const obj = JSON.parse(raw);
    if (!obj.done) obj.done = {};
    return obj;
  } catch {
    return { done: {} };
  }
}

function saveProgress(aid, progress) {
  localStorage.setItem(keyForAnnotator(aid), JSON.stringify(progress));
}

async function fetchJSON(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

function buildForm() {
  const form = $("annotation-form");
  form.innerHTML = "";

  for (const [q, spec] of Object.entries(SCHEMA)) {
    const fs = document.createElement("fieldset");
    const legend = document.createElement("legend");
    legend.textContent = q;
    fs.appendChild(legend);

    if (spec.description) {
      const p = document.createElement("div");
      p.textContent = spec.description;
      p.style.marginBottom = "8px";
      fs.appendChild(p);
    }

    for (const opt of spec.options) {
      const label = document.createElement("label");
      label.style.display = "block";
      label.style.margin = "4px 0";

      const input = document.createElement("input");
      input.type = spec.type === "multi" ? "checkbox" : "radio";
      input.name = q;
      input.value = opt;

      label.appendChild(input);
      label.appendChild(document.createTextNode(" " + opt));
      fs.appendChild(label);
    }

    form.appendChild(fs);
  }
}

function readAnswersFromForm() {
  const answers = {};
  for (const [q, spec] of Object.entries(SCHEMA)) {
    if (spec.type === "multi") {
      const checked = Array.from(document.querySelectorAll(`input[name="${q}"]:checked`))
        .map(x => x.value);
      answers[q] = checked;
    } else {
      const picked = document.querySelector(`input[name="${q}"]:checked`);
      answers[q] = picked ? picked.value : null;
    }
  }
  return answers;
}

function validateAnswers(answers) {
  for (const [q, spec] of Object.entries(SCHEMA)) {
    const v = answers[q];

    if (spec.type === "multi") {
      if (!Array.isArray(v) || v.length === 0) {
        throw new Error(`Please select at least one option for: ${q}`);
      }
    } else {
      if (!v) {
        throw new Error(`Please select one option for: ${q}`);
      }
    }
  }
}

function setCounterText() {
  const el = $("counter");
  if (!el) return;

  if (!currentImage) {
    el.textContent = "";
    return;
  }
  el.textContent = `Image ${currentIndex + 1} / ${IMAGES.length} (${currentImage})`;
}

function showImage(name) {
  currentImage = name;
  const img = $("els-image");

  // חשוב: נתיב מוחלט עם /
  const url = `/images/${encodeURIComponent(name)}`;
  img.src = url;

  img.onload = () => {
    showError("");
  };
  img.onerror = () => {
    showError(`Image failed to load: ${url} (check that /images/${name} opens)`);
  };

  setCounterText();
}

function pickNextUnseenImage(aid) {
  const progress = loadProgress(aid);
  const done = progress.done || {};

  for (let i = 0; i < IMAGES.length; i++) {
    const idx = (currentIndex + i) % IMAGES.length;
    const imgName = IMAGES[idx];
    if (!done[imgName]) {
      currentIndex = idx;
      return imgName;
    }
  }
  return null;
}

async function submitAndNext() {
  try {
    showError("");

    const aid = annotatorId();
    if (!aid) {
      showError("Please enter Annotator ID");
      return;
    }

    const answers = readAnswersFromForm();
    validateAnswers(answers);

    if (!currentImage) {
      showError("No image loaded");
      return;
    }

    const payload = {
      image_id: currentImage,
      annotator_id: aid,
      answers
    };

    const res = await fetch("/annotate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Submit failed (${res.status}): ${text}`);
    }

    // mark as done locally (resume after refresh)
    const progress = loadProgress(aid);
    progress.done[currentImage] = true;
    saveProgress(aid, progress);

    // next
    const next = pickNextUnseenImage(aid);
    if (!next) {
      $("els-image").removeAttribute("src");
      $("annotation-form").innerHTML = "";
      $("counter").textContent = "All images annotated 🎉";
      return;
    }

    // reset selections
    Array.from(document.querySelectorAll(`#annotation-form input`)).forEach(i => {
      i.checked = false;
    });

    showImage(next);
  } catch (e) {
    showError(e.message || String(e));
  }
}

async function init() {
  try {
    showError("");

    // ודאי שהנתיבים נכונים:
    // /schema, /images-list
    SCHEMA = await fetchJSON("/schema");
    IMAGES = await fetchJSON("/images-list");

    if (!IMAGES || IMAGES.length === 0) {
      showError("No images found. /images-list returned empty.");
      return;
    }

    buildForm();

    // אם כבר יש Annotator ID שנשמר בדפדפן (אופציונלי)
    // לא חובה, אבל נוח:
    const savedA = localStorage.getItem("els_last_annotator");
    if (savedA && $("annotator")) $("annotator").value = savedA;

    // כשמשנים annotator – ממשיכים מאיפה שהפסיק
    $("annotator")?.addEventListener("change", () => {
      const aid = annotatorId();
      if (aid) localStorage.setItem("els_last_annotator", aid);
      const next = pickNextUnseenImage(aid);
      if (next) showImage(next);
    });

    // ברירת מחדל: קחי את הראשון
    currentIndex = 0;
    showImage(IMAGES[0]);
  } catch (e) {
    showError(e.message || String(e));
  }
}

window.submitAndNext = submitAndNext;
window.addEventListener("load", init);
