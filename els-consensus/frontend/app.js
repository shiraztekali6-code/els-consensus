// ===============================
// CONFIG
// ===============================

const API_BASE = window.location.origin;

// ===============================
// STATE
// ===============================

let images = [];
let currentIndex = 0;
let userId = null;

// ===============================
// HELPERS
// ===============================

async function fetchJSON(url, options = {}) {
    const res = await fetch(url, options);

    if (!res.ok) {
        throw new Error(`${url} failed with ${res.status}`);
    }

    return res.json();
}

// ===============================
// LOAD IMAGES FOR USER (RESUME BUILT-IN)
// ===============================

async function loadImagesForUser() {
    images = await fetchJSON(`${API_BASE}/images-list/${userId}`);
    currentIndex = 0;
}

// ===============================
// LOAD SCHEMA & BUILD QUESTIONS
// ===============================

async function loadSchema() {
    const schema = await fetchJSON(`${API_BASE}/schema`);
    const container = document.getElementById("questions-container");
    container.innerHTML = "";

    for (const [key, spec] of Object.entries(schema)) {
        const wrapper = document.createElement("div");
        wrapper.className = "question-block";

        const label = document.createElement("h4");
        label.textContent = key;
        wrapper.appendChild(label);

        if (spec.type === "single") {
            spec.options.forEach(opt => {
                const radio = document.createElement("input");
                radio.type = "radio";
                radio.name = key;
                radio.value = opt;

                wrapper.appendChild(radio);
                wrapper.appendChild(document.createTextNode(opt));
                wrapper.appendChild(document.createElement("br"));
            });
        }

        if (spec.type === "multi") {
            spec.options.forEach(opt => {
                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.name = key;
                checkbox.value = opt;

                wrapper.appendChild(checkbox);
                wrapper.appendChild(document.createTextNode(opt));
                wrapper.appendChild(document.createElement("br"));
            });
        }

        container.appendChild(wrapper);
    }
}

// ===============================
// RENDER IMAGE
// ===============================

function renderImage() {
    if (!images.length) {
        alert("No more images to annotate.");
        return;
    }

    const imageName = images[currentIndex];
    const imgElement = document.getElementById("els-image");
    imgElement.src = `${API_BASE}/images/${imageName}`;
}

// ===============================
// COLLECT ANSWERS
// ===============================

function collectAnswers() {
    const answers = {};

    document.querySelectorAll(".question-block").forEach(block => {
        const key = block.querySelector("h4").textContent;
        const inputs = block.querySelectorAll("input");

        const selected = [];

        inputs.forEach(input => {
            if (input.checked) {
                selected.push(input.value);
            }
        });

        if (inputs[0].type === "radio") {
            answers[key] = selected[0] || "";
        } else {
            answers[key] = selected;
        }
    });

    return answers;
}

// ===============================
// SUBMIT
// ===============================

async function submitAndNext() {
    const imageName = images[currentIndex];

    const payload = {
        image_id: imageName,
        annotator_id: userId,
        answers: collectAnswers()
    };

    await fetchJSON(`${API_BASE}/annotate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    currentIndex++;
    renderImage();
}

// ===============================
// START APP
// ===============================

async function startApp() {
    userId = document.getElementById("username").value.trim();

    if (!userId) {
        alert("Please enter a username.");
        return;
    }

    await loadImagesForUser();
    await loadSchema();
    renderImage();
}

// ===============================
// EVENTS
// ===============================

document.getElementById("start-btn")
    .addEventListener("click", startApp);

document.getElementById("submit-btn")
    .addEventListener("click", submitAndNext);
