from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
import os
import json
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "changeme")


@app.get("/")
def root():
    return {"status": "ELS annotation server running"}


@app.get("/admin/full-dump")
def full_dump(token: str):
    if token != ADMIN_TOKEN:
        return JSONResponse(status_code=403, content={"error": "Unauthorized"})

    inspector = inspect(engine)
    dump_data = {}

    with SessionLocal() as db:
        for table_name in inspector.get_table_names():
            rows = db.execute(text(f"SELECT * FROM {table_name}")).mappings().all()
            dump_data[table_name] = [dict(row) for row in rows]

    return dump_data


@app.get("/admin/backup-file")
def create_backup_file(token: str):
    if token != ADMIN_TOKEN:
        return JSONResponse(status_code=403, content={"error": "Unauthorized"})

    inspector = inspect(engine)
    dump_data = {}

    with SessionLocal() as db:
        for table_name in inspector.get_table_names():
            rows = db.execute(text(f"SELECT * FROM {table_name}")).mappings().all()
            dump_data[table_name] = [dict(row) for row in rows]

    filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, "w") as f:
        json.dump(dump_data, f, indent=2)

    return {"status": "backup_created", "file": filename}
