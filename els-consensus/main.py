from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Union
import os, json
from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

# ---------- Static ----------
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

DATA_PATH = "data/annotations.json"

# ---------- Utilities ----------
def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH) as f:
        return json.load(f)

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

# ---------- Models ----------
class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, List[str]]]

# ---------- API ----------
@app.get("/schema")
def get_schema():
    return QUESTION_SCHEMA

@app.get("/images-list")
def images_list():
    files = sorted([
        f for f in os.listdir("images")
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ])
    return files

@app.post("/annotate")
def annotate(a: Annotation):
    data = load_data()
    data.setdefault(a.image_id, [])
    data[a.image_id].append(a.dict())
    save_data(data)
    return {"ok": True}
