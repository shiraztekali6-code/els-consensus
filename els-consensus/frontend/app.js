let images = [];
let index = 0;

async function loadImages() {
  const res = await fetch("/api/images-list");
  images = await res.json();

  if (images.length === 0) {
    document.getElementById("counter").innerText = "No images found";
    return;
  }

  showImage();
}

function showImage() {
  const img = document.getElementById("els-image");
  const name = images[index];

  img.src = `/images/${name}`;
  img.alt = name;

  document.getElementById("counter").innerText =
    `Image ${index + 1} / ${images.length}`;
}

function nextImage() {
  if (index < images.length - 1) {
    index++;
    showImage();
  } else {
    alert("All images annotated 🎉");
  }
}

loadImages();
