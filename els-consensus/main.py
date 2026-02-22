from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Union
import json
import os
from datetime import datetime

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

# ---------- Static ----------
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

DATA_PATH = "data/annotations.json"
IMAGES_DIR = "images"


# ---------- Utilities ----------
def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def validate_answers(answers: dict):
    for question, spec in QUESTION_SCHEMA.items():
        if question not in answers:
            raise HTTPException(status_code=400, detail=f"Missing answer for '{question}'")

        value = answers[question]

        if spec["type"] == "multi":
            if not isinstance(value, list):
                raise HTTPException(status_code=400, detail=f"'{question}' must be a list")
            # מותר גם רשימה ריקה אם תרצי, אבל אצלך רצית לבחור משהו -> נשאיר לא-ריק
            if len(value) == 0:
                raise HTTPException(status_code=400, detail=f"'{question}' must be a non-empty list")
            for v in value:
                if v not in spec["options"]:
                    raise HTTPException(status_code=400, detail=f"Invalid value '{v}' for '{question}'")

        elif spec["type"] == "single":
            if value not in spec["options"]:
                raise HTTPException(status_code=400, detail=f"Invalid value '{value}' for '{question}'")

        elif spec["type"] == "boolean":
            if not isinstance(value, bool):
                raise HTTPException(status_code=400, detail=f"'{question}' must be true/false")


# ---------- Models ----------
class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, bool, List[str]]]


# ---------- API ----------
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


@app.get("/annotated/{annotator_id}")
def get_annotated_for_annotator(annotator_id: str):
    """
    Returns list of image_ids already annotated by this annotator.
    """
    data = load_data()
    done = []
    for image_id, anns in data.items():
        for ann in anns:
            if ann.get("annotator_id") == annotator_id:
                done.append(image_id)
                break
    done.sort()
    return done


@app.post("/annotate")
def submit_annotation(annotation: Annotation):
    validate_answers(annotation.answers)

    data = load_data()
    data.setdefault(annotation.image_id, []).append({
        "annotator_id": annotation.annotator_id,
        "answers": annotation.answers,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

    save_data(data)
    return {"ok": True}
