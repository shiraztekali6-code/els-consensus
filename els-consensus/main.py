import os
import uuid
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import io
import csv

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

app = FastAPI()


# ==============================
# MODELS
# ==============================

class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Any]


# ==============================
# HEALTH
# ==============================

@app.get("/health")
def health():
    with engine.begin() as conn:
        conn.execute(text("select 1"))
    return {"ok": True}


# ==============================
# CONSENSUS UPDATE
# ==============================

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

        consensus_row = {
            "image_id": image_id,
            "n_annotations": total
        }

        for key in keys:
            true_count = sum(1 for r in rows if r[key])
            consensus_row[key] = true_count > total / 2

        # delete old
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


# ==============================
# SUBMIT
# ==============================

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

        "most_abundant__B": a["Which cell population appears to be the most abundant?"] == "B cells are the most abundant",
        "most_abundant__T": a["Which cell population appears to be the most abundant?"] == "T cells are the most abundant",
        "most_abundant__Ki67": a["Which cell population appears to be the most abundant?"] == "Proliferating cells (Ki67+) are the most abundant",
        "most_abundant__similar": a["Which cell population appears to be the most abundant?"] == "Cell populations appear similar in abundance",
        "most_abundant__few": a["Which cell population appears to be the most abundant?"] == "Very few cells are present overall",

        "density__high": a["How dense are the cells inside the ELS?"] == "High density (cells are tightly packed and overlapping)",
        "density__moderate": a["How dense are the cells inside the ELS?"] == "Moderate density (cells are very close but individually distinguishable)",
        "density__low": a["How dense are the cells inside the ELS?"] == "Low density (cells are separated with visible background between them)",
        "density__very_low": a["How dense are the cells inside the ELS?"] == "Very low density (isolated cells with large dark background or staining noise)",

        "bt_separation__not_applicable": a["How separated are the B-cell and T-cell areas?"] == "Not applicable (only one cell type present)",
        "bt_separation__not_separated": a["How separated are the B-cell and T-cell areas?"] == "Not separated (completely mixed, no distinct areas)",
        "bt_separation__low": a["How separated are the B-cell and T-cell areas?"] == "Low separation (early area formation but mostly mixed)",
        "bt_separation__moderate": a["How separated are the B-cell and T-cell areas?"] == "Moderate separation (distinct areas with some overlap)",
        "bt_separation__high": a["How separated are the B-cell and T-cell areas?"] == "High separation (clearly separated areas with relatively sharp boundaries)",

        "t_ring__not_applicable": a["Is there a T-cell ring at the edge of the ELS?"] == "Not applicable (no T cells present)",
        "t_ring__none": a["Is there a T-cell ring at the edge of the ELS?"] == "No ring present",
        "t_ring__weak": a["Is there a T-cell ring at the edge of the ELS?"] == "Weak ring formation",
        "t_ring__moderate": a["Is there a T-cell ring at the edge of the ELS?"] == "Moderate ring formation",
        "t_ring__clear": a["Is there a T-cell ring at the edge of the ELS?"] == "Clear ring formation",

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


# ==============================
# EXPORT RAW
# ==============================

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


# ==============================
# EXPORT CONSENSUS
# ==============================

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
