import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from komarc_from_isbn import (
    DEFAULT_ALADIN_TTB_KEY,
    build_komarc,
    build_markdown_output,
    fetch_book_info_by_isbn,
    normalize_isbn,
)


class KomarcRequest(BaseModel):
    isbn: str = Field(..., description="ISBN-10 또는 ISBN-13")
    source: str = Field(default="aladin", description="aladin/openlibrary/nl_seoji/auto")


class KomarcResponse(BaseModel):
    isbn: str
    source: str
    komarc_lines: list[str]
    result_text: str
    markdown_text: str


app = FastAPI(title="ISBN -> KORMARC Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/komarc", response_model=KomarcResponse)
def generate_komarc(payload: KomarcRequest) -> KomarcResponse:
    try:
        isbn = normalize_isbn(payload.isbn.strip())
        nl_raw = os.getenv("NL_SEOKJI_CERT_KEY") or os.getenv("NL_ISBN_CERT_KEY") or ""
        aladin_key = os.getenv("ALADIN_TTB_KEY", "").strip() or DEFAULT_ALADIN_TTB_KEY
        book = fetch_book_info_by_isbn(
            isbn=isbn,
            source=payload.source,
            aladin_ttb_key=aladin_key,
            nl_seokji_cert_key=nl_raw.strip() or None,
        )
        komarc_lines = build_komarc(book)
        result_text = "\n".join(komarc_lines)
        markdown_text = build_markdown_output(book, komarc_lines)
        return KomarcResponse(
            isbn=isbn,
            source=payload.source,
            komarc_lines=komarc_lines,
            result_text=result_text,
            markdown_text=markdown_text,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
