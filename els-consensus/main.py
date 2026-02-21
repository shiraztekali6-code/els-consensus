from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import json
import os

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Annotation Server")

# Serve UI and images
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/", StaticFiles(directory="static", html=True), name="static")

DATA_PATH = "data/annotations.json"


# ---------- Utilities ----------
def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ---------- API ----------
@app.get("/schema")
def get_schema():
    return QUESTION_SCHEMA


@app.get("/images-list")
def get_images_list():
    files = sorted(
        f for f in os.listdir("images")
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )
    return files


@app.post("/annotate")
def submit_annotation(payload: dict):
    required = {"image_id", "annotator_id", "answers"}
    if not required.issubset(payload):
        raise HTTPException(400, "Invalid payload")

    data = load_data()
    image_id = payload["image_id"]

    data.setdefault(image_id, []).append({
        "annotator_id": payload["annotator_id"],
        "answers": payload["answers"]
    })

    save_data(data)
    return {"ok": True}
