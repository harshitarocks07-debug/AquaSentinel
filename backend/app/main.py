from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import drought, flood, unified


app = FastAPI(
    title="AquaSentinel API",
    description="AI-Powered Flood and Drought Early Warning System",
    version="1.0.0"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(drought.router)
app.include_router(flood.router)
app.include_router(unified.router)


# Health check
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# Serve React frontend
REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIST), html=True),
    name="frontend"
)