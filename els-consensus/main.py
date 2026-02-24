import os
import uuid
import io
import csv
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from config.schema import SCHEMA


# =====================
# CONFIG
# =====================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

app = FastAPI()

# =====================
# FRONTEND ROUTES
# =====================

app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")

@app.get("/app.js")
def serve_js():
    return FileResponse("frontend/app.js")

@app.get("/schema")
def get_schema():
    return SCHEMA


# =====================
# HEALTH
# =====================

@app.get("/health")
def health():
    with engine.begin() as conn:
        conn.execute(text("select 1"))
    return {"ok": True}


# =====================
# MODEL
# =====================

class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Any]


# =====================
# CONSENSUS
# =====================

def update_consensus(image_id: str):

    with engine.begin() as conn:

        rows = conn.execute(
            text("select * from annotations_raw where image_id = :id"),
            {"id": image_id}
        ).mappings().all()

        if not rows:
            return

        total = len(rows)
        keys = [k for k in rows[0].keys() if k not in ["id", "image_id", "annotator_id"]]

        consensus = {
            "image_id": image_id,
            "n_annotations": total
        }

        for key in keys:
            count_true = sum(1 for r in rows if r[key])
            consensus[key] = count_true > total / 2

        conn.execute(
            text("delete from image_consensus where image_id = :id"),
            {"id": image_id}
        )

        cols = ", ".join(consensus.keys())
        vals = ", ".join([f":{k}" for k in consensus.keys()])

        conn.execute(
            text(f"insert into image_consensus ({cols}) values ({vals})"),
            consensus
        )


# =====================
# SUBMIT
# =====================

@app.post("/annotate")
def submit_annotation(annotation: Annotation):

    a = annotation.answers
    cells_multi = a["Which cell types are present in the ELS?"]

    row = {
        "id": str(uuid.uuid4()),
        "image_id": annotation.image_id,
        "annotator_id": annotation.annotator_id,

        "cells_present__B": "B cells are present" in cells_multi,
        "cells_present__T": "T cells are present" in cells_multi,
        "cells_present__Ki67": "Proliferating cells (Ki67+) are present" in cells_multi,
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


# =====================
# EXPORT RAW
# =====================

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


# =====================
# EXPORT CONSENSUS
# =====================

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
