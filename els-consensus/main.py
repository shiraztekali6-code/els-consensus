from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Union
from collections import Counter
import json
import os

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

# ---------- Static files ----------
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


def validate_answers(answers):
    for q, spec in QUESTION_SCHEMA.items():
        if q not in answers:
            raise HTTPException(400, f"Missing '{q}'")
        val = answers[q]
        if spec["type"] == "multi":
            if not isinstance(val, list):
                raise HTTPException(400, f"{q} must be list")
            for v in val:
                if v not in spec["options"]:
                    raise HTTPException(400, f"Invalid {v}")
        else:
            if val not in spec["options"]:
                raise HTTPException(400, f"Invalid {val}")


# ---------- Models ----------
class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, List[str]]]


# ---------- Consensus ----------
def compute_consensus(annotations):
    consensus = {}
    for q in QUESTION_SCHEMA:
        values = []
        for a in annotations:
            ans = a["answers"][q]
            values.extend(ans if isinstance(ans, list) else [ans])
        if values:
            consensus[q] = Counter(values).most_common(1)[0][0]
    return consensus


# ---------- API ----------
@app.post("/annotate")
def annotate(a: Annotation):
    validate_answers(a.answers)
    data = load_data()
    data.setdefault(a.image_id, []).append(a.dict())
    save_data(data)
    return {"ok": True}


@app.get("/schema")
def schema():
    return QUESTION_SCHEMA
