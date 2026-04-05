import os
import logging
from pathlib import Path

# Load .env file before any other imports that read env vars
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_claims import router as claims_router

app = FastAPI(
    title="Insurance Claim Settlement Agent",
    description="AI-powered claim evaluation with OCR, NLP retrieval, and rule-based decisioning.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure storage directories exist
for folder in ["app/storage/uploads", "app/storage/outputs", "app/storage/logs"]:
    os.makedirs(folder, exist_ok=True)

app.include_router(claims_router, prefix="/claims", tags=["Claims"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
