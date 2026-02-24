import os
import uuid
import io
import csv
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from config.schema import QUESTION_SCHEMA


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

app = FastAPI()


# ============================================================
# STATIC FILES
# ============================================================

app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/")
def root():
    return FileResponse("frontend/index.html")


@app.get("/app.js")
def serve_js():
    return FileResponse("frontend/app.js")


@app.get("/schema")
def get_schema():
    return QUESTION_SCHEMA


@app.get("/images")
def list_images():
    files = os.listdir("images")
    images = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    images.sort()
    return images


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    with engine.begin() as conn:
        conn.execute(text("select 1"))
    return {"ok": True}


# ============================================================
# MODEL
# ============================================================

class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Any]


# ============================================================
# CONSENSUS LOGIC
# ============================================================

def update_consensus(image_id: str):

    with engine.begin() as conn:

        rows = conn.execute(
            text("select * from annotations_raw where image_id = :id"),
            {"id": image_id}
        ).mappings().all()

        if not rows:
            return

        total = len(rows)

        feature_cols = [
            c for c in rows[0].keys()
            if c not in ("id", "image_id", "annotator_id")
        ]

        consensus_row = {
            "image_id": image_id,
            "n_annotations": total
        }

        for col in feature_cols:
            true_count = sum(1 for r in rows if r[col])
            consensus_row[col] = true_count > total / 2

        conn.execute(
            text("delete from image_consensus where image_id = :id"),
            {"id": image_id}
        )

        cols = ", ".join(consensus_row.keys())
        vals = ", ".join([f":{k}" for k in consensus_row.keys()])

        conn.execute(
            text(f"insert into image_consensus ({cols}) values ({vals})"),
            consensus_row
        )


# ============================================================
# SUBMIT ANNOTATION
# ============================================================

@app.post("/annotate")
def submit_annotation(annotation: Annotation):

    a = annotation.answers

    cells_multi = a.get("cell_types_present", [])

    row = {
        "id": str(uuid.uuid4()),
        "image_id": annotation.image_id,
        "annotator_id": annotation.annotator_id,

        # Q1
        "cells_present__B": "B cells are present" in cells_multi,
        "cells_present__T": "T cells are present" in cells_multi,
        "cells_present__Ki67": "Proliferating cells (Ki67+) are present" in cells_multi,

        # Q2
        "most_abundant__B": a.get("dominant_cell_population") == "B cells are the most abundant",
        "most_abundant__T": a.get("dominant_cell_population") == "T cells are the most abundant",
        "most_abundant__Ki67": a.get("dominant_cell_population") == "Proliferating cells (Ki67+) are the most abundant",
        "most_abundant__similar": a.get("dominant_cell_population") == "Cell populations appear similar in abundance",
        "most_abundant__few": a.get("dominant_cell_population") == "Very few cells are present overall",

        # Q3
        "density__high": a.get("cell_density") == "High density (cells are tightly packed and overlapping)",
        "density__moderate": a.get("cell_density") == "Moderate density (cells are very close but individually distinguishable)",
        "density__low": a.get("cell_density") == "Low density (cells are separated with visible background between them)",
        "density__very_low": a.get("cell_density") == "Very low density (isolated cells with large dark background or staining noise)",

        # Q4
        "bt_separation__not_applicable": a.get("b_t_separation") == "Not applicable (only one cell type present)",
        "bt_separation__not_separated": a.get("b_t_separation") == "Not separated (completely mixed, no distinct areas)",
        "bt_separation__low": a.get("b_t_separation") == "Low separation (early area formation but mostly mixed)",
        "bt_separation__moderate": a.get("b_t_separation") == "Moderate separation (distinct areas with some overlap)",
        "bt_separation__high": a.get("b_t_separation") == "High separation (clearly separated areas with relatively sharp boundaries)",

        # Q5
        "t_ring__not_applicable": a.get("t_cell_ring") == "Not applicable (no T cells present)",
        "t_ring__none": a.get("t_cell_ring") == "No ring present",
        "t_ring__weak": a.get("t_cell_ring") == "Weak ring formation",
        "t_ring__moderate": a.get("t_cell_ring") == "Moderate ring formation",
        "t_ring__clear": a.get("t_cell_ring") == "Clear ring formation",

        # Q6
        "gc_present__yes": a.get("gc_like_structure") == "GC-like structure present",
        "gc_present__no": a.get("gc_like_structure") == "No GC-like structure present",
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


# ============================================================
# EXPORT RAW
# ============================================================

@app.get("/admin/export/raw")
def export_raw(token: str):

    if token != "els-admin-shiraz":
        raise HTTPException(status_code=403)

    with engine.begin() as conn:
        result = conn.execute(text("select * from annotations_raw"))
        rows = result.fetchall()
        columns = result.keys()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=annotations_raw.csv"}
    )


# ============================================================
# EXPORT CONSENSUS
# ============================================================

@app.get("/admin/export/consensus")
def export_consensus(token: str):

    if token != "els-admin-shiraz":
        raise HTTPException(status_code=403)

    with engine.begin() as conn:
        result = conn.execute(text("select * from image_consensus"))
        rows = result.fetchall()
        columns = result.keys()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=image_consensus.csv"}
    )
