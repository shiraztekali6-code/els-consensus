from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Union
import psycopg2
import os
from datetime import datetime

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

# ---------- Static ----------
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

IMAGES_DIR = "images"

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")


# ---------- DB ----------
def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ---------- Validation ----------
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
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT image_id
        FROM annotations_raw
        WHERE annotator_id = %s
    """, (annotator_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return sorted([r[0] for r in rows])


# ---------- Submit Annotation ----------
@app.post("/annotate")
def submit_annotation(annotation: Annotation):
    validate_answers(annotation.answers)

    conn = get_connection()
    cur = conn.cursor()

    # מביאים את כל שמות העמודות
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'annotations_raw'
    """)
    columns = [c[0] for c in cur.fetchall()]

    # בונים שורה מלאה
    row = {}

    for col in columns:
        if col == "image_id":
            row[col] = annotation.image_id
        elif col == "annotator_id":
            row[col] = annotation.annotator_id
        elif col in ("id", "timestamp"):
            continue
        else:
            row[col] = False

    # ממלאים TRUE לפי הבחירות
    for question_key, value in annotation.answers.items():
        selected = value if isinstance(value, list) else [value]

        for option in selected:
            normalized = option.lower() \
                               .replace(" ", "_") \
                               .replace("+", "") \
                               .replace("-", "_") \
                               .replace("(", "") \
                               .replace(")", "") \
                               .replace("%", "") \
                               .replace("/", "_")

            col_name = f"{question_key}__{normalized}"

            if col_name in row:
                row[col_name] = True

    insert_cols = list(row.keys())
    insert_vals = [row[c] for c in insert_cols]

    placeholders = ",".join(["%s"] * len(insert_vals))
    col_string = ",".join(insert_cols)

    cur.execute(
        f"INSERT INTO annotations_raw ({col_string}) VALUES ({placeholders})",
        insert_vals
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"ok": True}


# ---------- Admin Export ----------
@app.get("/admin/export/annotations")
def export_annotations(token: str):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
    if ADMIN_TOKEN is None or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM annotations_raw
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    cur.close()
    conn.close()

    def generate():
        yield ",".join(columns) + "\n"
        for row in rows:
            yield ",".join([str(x) if x is not None else "" for x in row]) + "\n"

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=annotations_raw.csv"}
    )


@app.get("/health")
def health():
    return {"ok": True}
