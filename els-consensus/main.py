from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Union
from config.schema import QUESTION_SCHEMA

import os
import uuid
import io
import zipfile
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# ===============================
# ENV
# ===============================

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(DATABASE_URL)

app = FastAPI(title="ELS Consensus Annotation Server")

app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")


# ===============================
# MODELS
# ===============================

class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, List[str]]]


# ===============================
# SCHEMA ENDPOINT (FRONTEND NEEDS THIS)
# ===============================

@app.get("/schema")
def get_schema():
    return QUESTION_SCHEMA


# ===============================
# IMAGES LIST
# ===============================

IMAGES_DIR = "images"

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


# ===============================
# SUBMIT ANNOTATION
# ===============================

@app.post("/annotate")
def submit_annotation(annotation: Annotation):

    a = annotation.answers

    # ---- Multi question ----
    cells_multi = a["Which cell types are present in the ELS?"]

    row = {
        "id": str(uuid.uuid4()),
        "image_id": annotation.image_id,
        "annotator_id": annotation.annotator_id,

        # Q1
        "cells_present__B": "B cells are present" in cells_multi,
        "cells_present__T": "T cells are present" in cells_multi,
        "cells_present__Ki67": "Proliferating cells (Ki67+) are present" in cells_multi,

        # Q2
        "most_abundant__B": a["Which cell population appears to be the most abundant?"] == "B cells are the most abundant",
        "most_abundant__T": a["Which cell population appears to be the most abundant?"] == "T cells are the most abundant",
        "most_abundant__Ki67": a["Which cell population appears to be the most abundant?"] == "Proliferating cells (Ki67+) are the most abundant",
        "most_abundant__similar": a["Which cell population appears to be the most abundant?"] == "Cell populations appear similar in abundance",
        "most_abundant__few": a["Which cell population appears to be the most abundant?"] == "Very few cells are present overall",

        # Q3
        "density__high": a["How dense are the cells inside the ELS?"] == "High density (cells are tightly packed and overlapping)",
        "density__moderate": a["How dense are the cells inside the ELS?"] == "Moderate density (cells are very close but individually distinguishable)",
        "density__low": a["How dense are the cells inside the ELS?"] == "Low density (cells are separated with visible background between them)",
        "density__very_low": a["How dense are the cells inside the ELS?"] == "Very low density (isolated cells with large dark background or staining noise)",

        # Q4
        "bt_separation__not_applicable": a["How separated are the B-cell and T-cell areas?"] == "Not applicable (only one cell type present)",
        "bt_separation__not_separated": a["How separated are the B-cell and T-cell areas?"] == "Not separated (completely mixed, no distinct areas)",
        "bt_separation__low": a["How separated are the B-cell and T-cell areas?"] == "Low separation (early area formation but mostly mixed)",
        "bt_separation__moderate": a["How separated are the B-cell and T-cell areas?"] == "Moderate separation (distinct areas with some overlap)",
        "bt_separation__high": a["How separated are the B-cell and T-cell areas?"] == "High separation (clearly separated areas with relatively sharp boundaries)",

        # Q5
        "t_ring__not_applicable": a["Is there a T-cell ring at the edge of the ELS?"] == "Not applicable (no T cells present)",
        "t_ring__none": a["Is there a T-cell ring at the edge of the ELS?"] == "No ring present",
        "t_ring__weak": a["Is there a T-cell ring at the edge of the ELS?"] == "Weak ring formation",
        "t_ring__moderate": a["Is there a T-cell ring at the edge of the ELS?"] == "Moderate ring formation",
        "t_ring__clear": a["Is there a T-cell ring at the edge of the ELS?"] == "Clear ring formation",

        # Q6
        "gc_present__yes": a["Is there a GC-like structure?"] == "GC-like structure present",
        "gc_present__no": a["Is there a GC-like structure?"] == "No GC-like structure present",
    }

    cols = ", ".join(row.keys())
    vals = ", ".join([f":{k}" for k in row.keys()])

    with engine.begin() as conn:
    conn.execute(
        text(f"insert into annotations_raw ({cols}) values ({vals})"),
        row
    )

    update_consensus(annotation.image_id)

    return {"ok": True}


# ===============================
# MAJORITY CONSENSUS
# ===============================

def update_consensus(image_id):

    with engine.connect() as conn:
        rows = conn.execute(
            text("select * from annotations_raw where image_id = :img"),
            {"img": image_id}
        ).mappings().all()

    if not rows:
        return

    consensus = {}
    keys = [k for k in rows[0].keys() if k not in ["id", "image_id", "annotator_id", "timestamp"]]

    for k in keys:
        true_count = sum(1 for r in rows if r[k])
        consensus[k] = true_count > (len(rows) // 2)

    with engine.connect() as conn:
        conn.execute(
            text(f"""
                insert into image_consensus (image_id, {", ".join(consensus.keys())})
                values (:image_id, {", ".join([f":{k}" for k in consensus.keys()])})
                on conflict (image_id)
                do update set
                {", ".join([f"{k}=:{k}" for k in consensus.keys()])},
                updated_at = now()
            """),
            {"image_id": image_id, **consensus}
        )
        conn.commit()


# ===============================
# EXPORT
# ===============================

@app.get("/admin/export/annotations")
def export_annotations(token: str):

    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    with engine.connect() as conn:
        raw = conn.execute(text("select * from annotations_raw")).mappings().all()
        cons = conn.execute(text("select * from image_consensus")).mappings().all()

    raw_df = pd.DataFrame(raw)
    cons_df = pd.DataFrame(cons)

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as zf:
        raw_excel = io.BytesIO()
        raw_df.to_excel(raw_excel, index=False)
        zf.writestr("ELS_raw_data.xlsx", raw_excel.getvalue())

        cons_excel = io.BytesIO()
        cons_df.to_excel(cons_excel, index=False)
        zf.writestr("ELS_consensus_per_image.xlsx", cons_excel.getvalue())

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=ELS_exports.zip"}
    )


# ===============================
# HEALTH
# ===============================

@app.get("/health")
def health():
    return {"ok": True}
