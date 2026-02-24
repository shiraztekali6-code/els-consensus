let schema = null;
let images = [];
let idx = 0;

const ADMIN = "els-admin-shiraz";

async function init() {
  schema = await fetch("/schema").then(r => r.json());
  images = await fetch("/images").then(r => r.json());
  render();
}

function render() {
  document.getElementById("elsImage").src = `/images/${images[idx]}`;
  document.getElementById("imgCounter").innerText = `Image ${idx+1}/${images.length}`;
}

document.getElementById("enterBtn").onclick = () => {
  const id = document.getElementById("annotatorId").value;
  if (id === ADMIN)
    document.getElementById("adminPanel").style.display = "block";
};

document.getElementById("downloadBtn").onclick = () => {
  const token = document.getElementById("annotatorId").value;
  window.open(`/admin/export/raw?token=${token}`);
  window.open(`/admin/export/consensus?token=${token}`);
};

document.getElementById("submitBtn").onclick = async () => {

  await fetch("/annotate", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      image_id: images[idx],
      annotator_id: document.getElementById("annotatorId").value,
      answers: {}
    })
  });

  idx++;
  render();
};

init();
