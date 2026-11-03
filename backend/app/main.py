
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import drought, flood, unified


# Initialize FastAPI
app = FastAPI(
    title="AquaSentinel API",
    description="AI-Powered Flood and Drought Early Warning System",
    version="1.0.0"
)


# CORS configuration for frontend
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

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to AquaSentinel API",
        "status": "online",
        "version": "1.0.0"
    }


# Health check
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
