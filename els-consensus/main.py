from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Union
import json
import os

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

DATA_PATH = "data/annotations.json"


# -----------------------
# Utilities
# -----------------------

def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def validate_answers(answers: dict):
    for question, spec in QUESTION_SCHEMA.items():
        if question not in answers:
            raise HTTPException(
                status_code=400,
                detail=f"Missing answer for question '{question}'"
            )

        value = answers[question]

        if spec["type"] == "multi":
            if not isinstance(value, list):
                raise HTTPException(
                    status_code=400,
                    detail=f"'{question}' must be a list"
                )
            for v in value:
                if v not in spec["options"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid value '{v}' for '{question}'"
                    )

        elif spec["type"] == "single":
            if value not in spec["options"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value '{value}' for '{question}'"
                )

        elif spec["type"] == "boolean":
            if not isinstance(value, bool):
                raise HTTPException(
                    status_code=400,
                    detail=f"'{question}' must be true/false"
                )


# -----------------------
# Models
# -----------------------

class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, bool, List[str]]]


# -----------------------
# Routes
# -----------------------

@app.get("/")
def root():
    return {"status": "ELS annotation server running"}


@app.post("/annotate")
def submit_annotation(annotation: Annotation):
    validate_answers(annotation.answers)

    data = load_data()

    if annotation.image_id not in data:
        data[annotation.image_id] = []

    data[annotation.image_id].append({
        "annotator_id": annotation.annotator_id,
        "answers": annotation.answers
    })

    save_data(data)

    return {"ok": True}


@app.get("/admin/image/{image_id}")
def admin_view_image(image_id: str, token: str):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

    if ADMIN_TOKEN is None or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = load_data()

    if image_id not in data:
        return {
            "image_id": image_id,
            "n_annotators": 0,
            "annotations": []
        }

    return {
        "image_id": image_id,
        "n_annotators": len(data[image_id]),
        "annotations": data[image_id]
    }
