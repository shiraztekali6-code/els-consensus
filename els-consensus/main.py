from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Union
from collections import Counter
import json
import os

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

DATA_PATH = "data/annotations.json"


# --------------------
# Utilities
# --------------------

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

        if spec["type"] == "single":
            if val not in spec["options"]:
                raise HTTPException(400, f"Invalid value '{val}' for '{q}'")


# --------------------
# Models
# --------------------

class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, List[str]]]


# --------------------
# Consensus logic
# --------------------

def compute_consensus(annotations):
    consensus = {}
    flags = {}

    for q in QUESTION_SCHEMA:
        values = []
        for ann in annotations:
            a = ann["answers"][q]
            values.extend(a if isinstance(a, list) else [a])

        if not values:
            consensus[q] = None
            continue

        counts = Counter(values)
        top = counts.most_common()

        if len(top) > 1 and top[0][1] == top[1][1]:
            consensus[q] = "ambiguous"
            flags[q] = "tie"
        else:
            consensus[q] = top[0][0]

    return consensus, flags


# --------------------
# Routes
# --------------------

@app.get("/")
def root():
    return {"status": "ELS annotation server running"}


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


# ---------- ADMIN ----------

def check_admin(token: str):
    if token != os.environ.get("ADMIN_TOKEN"):
        raise HTTPException(403, "Forbidden")


@app.get("/admin/image/{image_id}")
def admin_image(image_id: str, token: str):
    check_admin(token)
    data = load_data()
    anns = data.get(image_id, [])
    return {
        "image_id": image_id,
        "n_annotators": len(anns),
        "annotations": anns
    }


@app.get("/admin/consensus/{image_id}")
def admin_consensus(image_id: str, token: str):
    check_admin(token)
    data = load_data()
    anns = data.get(image_id, [])
    consensus, flags = compute_consensus(anns) if anns else ({}, {})
    return {
        "image_id": image_id,
        "n_annotators": len(anns),
        "consensus": consensus,
        "flags": flags
    }


@app.get("/admin/vectors")
def admin_vectors(token: str):
    check_admin(token)
    data = load_data()
    output = []

    for image_id, anns in data.items():
        consensus, flags = compute_consensus(anns)
        vector = {}

        for q, spec in QUESTION_SCHEMA.items():
            for opt in spec["options"]:
                key = f"{q}:{opt}"
                vector[key] = int(consensus.get(q) == opt)

        output.append({
            "image_id": image_id,
            "vector": vector,
            "n_annotators": len(anns),
            "flags": flags
        })

    return output
