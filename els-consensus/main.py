from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from config.schema import QUESTION_SCHEMA

app = FastAPI(title="ELS Consensus Annotation Server")

# ---------- API ----------
@app.get("/schema")
def get_schema():
    return QUESTION_SCHEMA

@app.get("/images-list")
def get_images_list():
    return sorted(
        f for f in os.listdir("images")
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )

# ---------- Static ----------
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")
