let images = [];
let index = 0;

async function loadImages() {
  const res = await fetch("/images-list");
  images = await res.json();

  if (images.length === 0) {
    alert("No images found");
    return;
  }

  showImage();
}

function showImage() {
  const img = document.getElementById("els-image");
  img.src = `/images/${images[index]}`;

  document.getElementById("counter").innerText =
    `Image ${index + 1} / ${images.length}`;
}

function nextImage() {
  index++;
  if (index >= images.length) {
    alert("All images done 🎉");
    return;
  }
  showImage();
}

loadImages();
