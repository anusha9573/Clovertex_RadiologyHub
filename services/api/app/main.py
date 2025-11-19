# services/api/app/main.py
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from services.api.app.routes.resource_routes import router as resource_router
from services.api.app.routes.work_routes import router as work_router

APP_ROOT = Path(__file__).resolve().parent
STATIC_DIR = APP_ROOT / "static"

app = FastAPI(
    title="Work Allocation API",
    description="Agentic pipeline for radiology work assignment with UI helpers.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(work_router)
app.include_router(resource_router)

# Static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    return {"status": "ok", "message": "Work Allocation API is running. Visit /ui for the console."}


@app.get("/ui")
def serve_ui():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(index_file)


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}
