from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Union
from collections import Counter
import os
import json

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

# =====================
# Static files
# =====================

# Frontend (UI)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Images
app.mount("/images", StaticFiles(directory="images"), name="images")

# =====================
# Data
# =====================

DATA_PATH = "data/annotations.json"


def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


# =====================
# Models
# =====================

class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, List[str]]]


# =====================
# Validation
# =====================

def validate_answers(answers: dict):
    for q, spec in QUESTION_SCHEMA.items():
        if q not in answers:
            raise HTTPException(400, f"Missing answer for '{q}'")

        val = answers[q]

        if spec["type"] == "multi":
            if not isinstance(val, list):
                raise HTTPException(400, f"'{q}' must be a list")
            for v in val:
                if v not in spec["options"]:
                    raise HTTPException(400, f"Invalid value '{v}' for '{q}'")

        elif spec["type"] == "single":
            if val not in spec["options"]:
                raise HTTPException(400, f"Invalid value '{val}' for '{q}'")


# =====================
# API routes
# =====================

@app.get("/schema")
def get_schema():
    return QUESTION_SCHEMA


@app.get("/images-list")
def get_images():
    """
    Returns list of image filenames in /images
    """
    if not os.path.exists("images"):
        return []

    files = sorted(
        f for f in os.listdir("images")
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )
    return files


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
