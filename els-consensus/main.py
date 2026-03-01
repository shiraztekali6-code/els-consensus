from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Union
import json
import os
import csv
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
    os.makedirs("data", exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def validate_answers(answers: dict):
    for q, spec in QUESTION_SCHEMA.items():
        if q not in answers:
            raise HTTPException(400, f"Missing answer for '{q}'")

        val = answers[q]

        if spec["type"] == "multi":
            if not isinstance(val, list) or len(val) == 0:
                raise HTTPException(400, f"'{q}' must be a non-empty list")
            for v in val:
                if v not in spec["options"]:
                    raise HTTPException(400, f"Invalid value '{v}' for '{q}'")
        else:
            if val not in spec["options"]:
                raise HTTPException(400, f"Invalid value '{val}' for '{q}'")


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
def get_annotated(annotator_id: str):
    data = load_data()
    done = []
    for image_id, anns in data.items():
        for ann in anns:
            if ann["annotator_id"] == annotator_id:
                done.append(image_id)
                break
    return sorted(done)


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


# ---------- Admin: Export CSV ----------
@app.get("/admin/export/annotations")
def export_annotations(token: str):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
    if ADMIN_TOKEN is None or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = load_data()

    def generate():
        yield "image_id,annotator_id,question,answer\n"
        for image_id, anns in data.items():
            for ann in anns:
                annotator = ann["annotator_id"]
                for q, ans in ann["answers"].items():
                    if isinstance(ans, list):
                        for a in ans:
                            yield f"{image_id},{annotator},{q},{a}\n"
                    else:
                        yield f"{image_id},{annotator},{q},{ans}\n"

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=annotations.csv"}
    )


@app.get("/health")
def health():
    return {"ok": True}
