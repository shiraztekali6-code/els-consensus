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
// LOAD IMAGES LIST
// ===============================

async function loadImages() {
    images = await fetchJSON(`${API_BASE}/images-list`);
}

// ===============================
// LOAD IMAGE TO UI
// ===============================

function renderImage() {
    if (!images.length) return;

    const imageName = images[currentIndex];
    const imgElement = document.getElementById("els-image");

    imgElement.src = `${API_BASE}/images/${imageName}`;
}

// ===============================
// RESUME (SAFE)
// ===============================

async function resume(userId) {
    try {
        const data = await fetchJSON(`${API_BASE}/annotated/${userId}`);

        if (data && data.last_index !== undefined) {
            currentIndex = data.last_index;
        }

        console.log("Resume successful");
    } catch (err) {
        console.log("No previous session found. Starting fresh.");
        currentIndex = 0;
    }
}

// ===============================
// START APP
// ===============================

async function startApp() {
    try {
        userId = document.getElementById("username").value.trim();

        if (!userId) {
            alert("Please enter a username.");
            return;
        }

        await loadImages();
        await resume(userId);

        renderImage();
    } catch (err) {
        console.error("Initialization error:", err);
    }
}

// ===============================
// EVENT LISTENERS
// ===============================

document.getElementById("start-btn")
    .addEventListener("click", startApp);
