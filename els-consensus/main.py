from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Union
import json
import os

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

DATA_PATH = "data/annotations.json"
IMAGES_DIR = "images"
FRONTEND_DIR = "frontend"


# -----------------------
# Utilities
# -----------------------
def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def validate_answers(answers: dict):
    for question, spec in QUESTION_SCHEMA.items():
        if question not in answers:
            raise HTTPException(status_code=400, detail=f"Missing answer for '{question}'")

        value = answers[question]

        if spec["type"] == "multi":
            if not isinstance(value, list):
                raise HTTPException(status_code=400, detail=f"'{question}' must be a list")
            # מאפשר גם רשימה ריקה (לפעמים באמת אין משהו לבחור)
            for v in value:
                if v not in spec["options"]:
                    raise HTTPException(status_code=400, detail=f"Invalid value '{v}' for '{question}'")

        elif spec["type"] == "single":
            if value not in spec["options"]:
                raise HTTPException(status_code=400, detail=f"Invalid value '{value}' for '{question}'")

        else:
            raise HTTPException(status_code=400, detail=f"Unknown schema type for '{question}'")


# -----------------------
# Models
# -----------------------
class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, List[str]]]


# -----------------------
# API routes (שמים לפני mount כדי שלא יידרסו)
# -----------------------
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def root():
    # להפוך את / לכניסה ל-UI
    return RedirectResponse(url="/ui/")


@app.get("/schema")
def get_schema():
    return QUESTION_SCHEMA


@app.get("/images-list")
def get_images_list():
    if not os.path.exists(IMAGES_DIR):
        return []
    images = [
        f for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff"))
    ]
    images.sort()
    return images


@app.post("/annotate")
def submit_annotation(annotation: Annotation):
    validate_answers(annotation.answers)

    data = load_data()
    data.setdefault(annotation.image_id, []).append({
        "annotator_id": annotation.annotator_id,
        "answers": annotation.answers
    })

    save_data(data)
    return {"ok": True}


# -----------------------
# Static mounts (שמים בסוף!)
# -----------------------
if os.path.isdir(IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")
