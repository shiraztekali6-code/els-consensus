from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Union
from collections import Counter
import json, os, csv

from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

# ---------- Static ----------
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

DATA_PATH = "data/annotations.json"


# ---------- Utils ----------
def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH) as f:
        return json.load(f)


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def require_admin(token: str):
    if token != os.environ.get("ADMIN_TOKEN"):
        raise HTTPException(status_code=403, detail="Forbidden")


# ---------- Models ----------
class Annotation(BaseModel):
    image_id: str
    annotator_id: str
    answers: Dict[str, Union[str, List[str]]]


# ---------- Consensus ----------
def compute_consensus(annotations):
    consensus = {}
    flags = {}

    for q, spec in QUESTION_SCHEMA.items():
        values = []
        for a in annotations:
            ans = a["answers"][q]
            values.extend(ans if isinstance(ans, list) else [ans])

        if not values:
            consensus[q] = None
            continue

        counts = Counter(values).most_common()
        if len(counts) > 1 and counts[0][1] == counts[1][1]:
            consensus[q] = "ambiguous"
            flags[q] = "tie"
        else:
            consensus[q] = counts[0][0]

    return consensus, flags


# ---------- API ----------
@app.post("/annotate")
def annotate(a: Annotation):
    data = load_data()
    data.setdefault(a.image_id, []).append(a.dict())
    save_data(data)
    return {"ok": True}


@app.get("/schema")
def schema():
    return QUESTION_SCHEMA


# ---------- ADMIN ----------
@app.get("/admin/annotations")
def admin_all(token: str):
    require_admin(token)
    return load_data()


@app.get("/admin/consensus/{image_id}")
def admin_consensus(image_id: str, token: str):
    require_admin(token)
    data = load_data()
    anns = data.get(image_id, [])
    consensus, flags = compute_consensus(anns)
    return {
        "image_id": image_id,
        "n_annotators": len(anns),
        "consensus": consensus,
        "flags": flags
    }


@app.get("/admin/vectors")
def admin_vectors(token: str):
    require_admin(token)
    data = load_data()
    vectors = []

    for image_id, anns in data.items():
        consensus, flags = compute_consensus(anns)
        row = {"image_id": image_id, "n_annotators": len(anns)}

        for q, spec in QUESTION_SCHEMA.items():
            if spec["type"] == "multi":
                for opt in spec["options"]:
                    row[f"{q}:{opt}"] = int(
                        any(opt in a["answers"][q] for a in anns)
                    )
            else:
                for opt in spec["options"]:
                    row[f"{q}:{opt}"] = int(consensus.get(q) == opt)

        vectors.append(row)

    return vectors


@app.get("/admin/export/csv")
def export_csv(token: str):
    require_admin(token)
    vectors = admin_vectors(token)
    path = "data/els_vectors.csv"

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=vectors[0].keys())
        writer.writeheader()
        writer.writerows(vectors)

    return FileResponse(path, filename="els_vectors.csv")
