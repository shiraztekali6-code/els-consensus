from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Union
from collections import Counter
import json
import os

from config.schema import QUESTION_SCHEMA  # schema.py must be in the same folder

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
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
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
# Consensus logic
# -----------------------

def compute_consensus(annotations: list):
    """
    annotations: list of {"annotator_id": ..., "answers": {...}}
    """
    consensus = {}
    flags = {}

    for question, spec in QUESTION_SCHEMA.items():
        values = []

        for ann in annotations:
            answer = ann["answers"][question]
            if isinstance(answer, list):
                values.extend(answer)
            else:
                values.append(answer)

        if not values:
            consensus[question] = None
            continue

        counts = Counter(values)
        most_common = counts.most_common()

        if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
            consensus[question] = "ambiguous"
            flags[question] = "tie"
        else:
            consensus[question] = most_common[0][0]

    return consensus, flags


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


@app.get("/admin/consensus/{image_id}")
def admin_consensus(image_id: str, token: str):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

    if ADMIN_TOKEN is None or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = load_data()

    if image_id not in data or len(data[image_id]) == 0:
        return {
            "image_id": image_id,
            "n_annotators": 0,
            "consensus": {},
            "flags": {}
        }

    consensus, flags = compute_consensus(data[image_id])

    return {
        "image_id": image_id,
        "n_annotators": len(data[image_id]),
        "consensus": consensus,
        "flags": flags
    }


@app.get("/admin/vectors")
def admin_vectors(token: str):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

    if ADMIN_TOKEN is None or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = load_data()
    vectors = []

    for image_id, annotations in data.items():
        consensus, flags = compute_consensus(annotations)
        vector = {}

        for question, spec in QUESTION_SCHEMA.items():
            if spec["type"] == "multi":
                for opt in spec["options"]:
                    key = f"{question}:{opt}"
                    present = any(
                        opt in ann["answers"][question]
                        for ann in annotations
                    )
                    vector[key] = 1 if present else 0
            else:
                for opt in spec["options"]:
                    key = f"{question}:{opt}"
                    vector[key] = 1 if consensus.get(question) == opt else 0

        vectors.append({
            "image_id": image_id,
            "vector": vector,
            "n_annotators": len(annotations),
            "flags": flags
        })

    return vectors
