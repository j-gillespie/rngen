from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.generator import TEMPLATE_PATH, generate_markdown

app = FastAPI(title="ACME Release Notes Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class GenerateRequest(BaseModel):
    product: str = Field(min_length=1)
    version: str = Field(min_length=1)
    release_date: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO date from the UI date picker (YYYY-MM-DD)",
    )
    details: str = Field(min_length=1)


class GenerateResponse(BaseModel):
    markdown: str


@app.get("/")
async def index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_release_notes(payload: GenerateRequest) -> GenerateResponse:
    if not TEMPLATE_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Template not found at {TEMPLATE_PATH}",
        )

    markdown = generate_markdown(
        product=payload.product.strip(),
        version=payload.version.strip(),
        release_date=payload.release_date,
        details=payload.details.strip(),
    )
    return GenerateResponse(markdown=markdown)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
