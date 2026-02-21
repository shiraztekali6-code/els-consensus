let images = [];
let index = 0;

async function loadImages() {
  const res = await fetch("/images-list");
  images = await res.json();
  showImage();
}

function showImage() {
  if (index >= images.length) {
    document.body.innerHTML = "<h2>All images annotated 🎉</h2>";
    return;
  }

  document.getElementById("image").src = "/images/" + images[index];
  document.getElementById("counter").innerText =
    `Image ${index + 1} / ${images.length}`;
}

async function submit() {
  const annotator = document.getElementById("annotator").value;
  if (!annotator) {
    alert("Please enter annotator ID");
    return;
  }

  await fetch("/annotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_id: images[index],
      annotator_id: annotator,
      answers: {} // נרחיב בהמשך
    })
  });

  index++;
  showImage();
}

loadImages();
