from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Union
from config.schema import QUESTION_SCHEMA

import json
import os
import io
import zipfile
import pandas as pd
from collections import Counter
from datetime import datetime

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


# ---------- Admin: Export Raw + Consensus (ZIP) ----------
@app.get("/admin/export/annotations")
def export_annotations(token: str):

    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

    if ADMIN_TOKEN is None or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = load_data()

    # =======================
    # RAW DATA (wide format)
    # =======================
    raw_rows = []

    for image_id, anns in data.items():
        for ann in anns:

            row = {
                "image_id": image_id,
                "annotator_id": ann["annotator_id"],
                "timestamp": ann.get("timestamp", "")
            }

            for q in QUESTION_SCHEMA.keys():
                val = ann["answers"].get(q, "")
                if isinstance(val, list):
                    row[q] = ", ".join(val)
                else:
                    row[q] = val

            raw_rows.append(row)

    raw_df = pd.DataFrame(raw_rows)

    # =======================
    # CONSENSUS PER IMAGE
    # =======================
    consensus_rows = []

    for image_id, anns in data.items():

        image_row = {"image_id": image_id}

        for q, spec in QUESTION_SCHEMA.items():

            answers = [ann["answers"][q] for ann in anns]

            if spec["type"] == "multi":
                # One-hot majority encoding
                for opt in spec["options"]:
                    count = sum(
                        1 for a in answers
                        if isinstance(a, list) and opt in a
                    )
                    image_row[f"{q}__{opt}"] = int(count >= len(answers) / 2)

            else:
                counter = Counter(answers)
                majority = counter.most_common(1)[0][0] if counter else ""
                image_row[q] = majority

        consensus_rows.append(image_row)

    consensus_df = pd.DataFrame(consensus_rows)

    # =======================
    # ZIP EXPORT
    # =======================
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as zf:

        raw_excel = io.BytesIO()
        raw_df.to_excel(raw_excel, index=False, engine="openpyxl")
        zf.writestr("ELS_raw_data.xlsx", raw_excel.getvalue())

        consensus_excel = io.BytesIO()
        consensus_df.to_excel(consensus_excel, index=False, engine="openpyxl")
        zf.writestr("ELS_consensus_per_image.xlsx", consensus_excel.getvalue())

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=ELS_exports.zip"
        }
    )


@app.get("/health")
def health():
    return {"ok": True}
