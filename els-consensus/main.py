from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Union
from collections import Counter
import json
import os

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

# =========================
# Static files
# =========================

# images will be available at /images/els1.png
app.mount("/images", StaticFiles(directory="images"), name="images")

# frontend (index.html + app.js) served at /
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


# =========================
# Paths
# =========================

DATA_PATH = "data/annotations.json"
IMAGES_DIR = "images"


# =========================
# Utilities
# =========================

def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def validate_answers(answers: dict):
    for question, spec in QUESTION_SCHEMA.items():
        if question not in answers:
            raise HTTPException(
                status_code=400,
                detail=f"Missing answer for '{question}'"
            )

        value = answers[question]

        if spec["type"] == "multi":
            if not isinstance(value, list):
                raise HTTPException(400, f"'{question}' must be a list")
            for v in value:
                if v not in spec["options"]:
                    raise HTTPException(400, f"Invalid value '{v}' for '{question}'")

        else:  # single
            if value not in spec["options"]:
                raise HTTPException(400, f"Invalid value '{value}' for '{question}'")


# =========================
# Models
# =========================

class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, List[str]]]


# =========================
# API routes
# =========================

@app.get("/schema")
def get_schema():
    """
    Returns the QUESTION_SCHEMA to the frontend
    """
    return QUESTION_SCHEMA


@app.get("/images-list")
def get_images_list():
    """
    Returns sorted list of image filenames
    """
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


# =========================
# Consensus (admin utility)
# =========================

@app.get("/admin/consensus/{image_id}")
def get_consensus(image_id: str):
    data = load_data()

    if image_id not in data or len(data[image_id]) == 0:
        return {
            "image_id": image_id,
            "n_annotators": 0,
            "consensus": {}
        }

    consensus = {}

    for question in QUESTION_SCHEMA:
        values = []
        for ann in data[image_id]:
            ans = ann["answers"][question]
            values.extend(ans if isinstance(ans, list) else [ans])

        if values:
            consensus[question] = Counter(values).most_common(1)[0][0]

    return {
        "image_id": image_id,
        "n_annotators": len(data[image_id]),
        "consensus": consensus
    }
