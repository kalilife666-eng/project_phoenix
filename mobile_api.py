#!/usr/bin/env python3
"""
HTTP API for exposing the shared legal analyzer to mobile clients.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ai_integration import AIIntegration
from charter_analyzer import CharterAnalyzer
from document_processor import DocumentProcessor, _split_paragraphs, _split_sentences


app = FastAPI(
    title="project_phoenix Mobile API",
    version="1.0.0",
    description="API wrapper around the shared Charter and human-rights analysis engine.",
)

logger = logging.getLogger(__name__)

SUPPORTED_FILE_EXTENSIONS = {".pdf", ".docx", ".txt", ".rtf", ".md"}
MAX_TEXT_CHARS = int(os.environ.get("PROJECT_PHOENIX_MAX_TEXT_CHARS", "200000"))
MAX_UPLOAD_BYTES = int(os.environ.get("PROJECT_PHOENIX_MAX_UPLOAD_BYTES", str(15 * 1024 * 1024)))
ANALYSIS_TIMEOUT_SECONDS = int(os.environ.get("PROJECT_PHOENIX_ANALYSIS_TIMEOUT_SECONDS", "90"))


class AnalyzerOptions(BaseModel):
    canlii_api_key: str | None = None
    ai_api_key: str | None = None
    ai_provider: Literal["openai", "gemini"] = "openai"
    ai_model: str = "gpt-4.1-mini"
    ai_reasoning_effort: Literal["low", "medium", "high"] | None = None


class AnalyzeTextRequest(AnalyzerOptions):
    text: str = Field(..., min_length=1)


class AnalyzeHumanRightsRequest(AnalyzerOptions):
    text: str = Field(..., min_length=1)
    include_charter_context: bool = True


class TranslateTextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    target_language: Literal["english", "french", "en", "fr"]
    source_language: Literal["english", "french", "en", "fr"] | None = None
    ai_api_key: str | None = None
    ai_provider: Literal["openai", "gemini"] = "openai"
    ai_model: str = "gpt-4.1-mini"
    ai_reasoning_effort: Literal["low", "medium", "high"] | None = None


@dataclass
class FileAnalysisForm:
    canlii_api_key: str | None = Form(default=None)
    ai_api_key: str | None = Form(default=None)
    ai_provider: Literal["openai", "gemini"] = Form(default="openai")
    ai_model: str = Form(default="gpt-4.1-mini")
    ai_reasoning_effort: Literal["low", "medium", "high"] | None = Form(default=None)

    def to_options(self) -> AnalyzerOptions:
        return AnalyzerOptions(
            canlii_api_key=self.canlii_api_key,
            ai_api_key=self.ai_api_key,
            ai_provider=self.ai_provider,
            ai_model=self.ai_model,
            ai_reasoning_effort=self.ai_reasoning_effort,
        )


def _normalize_text(text: str) -> str:
    safe_text = text.strip()
    if not safe_text:
        _raise_api_error(400, "empty_text", "Text input cannot be empty.")
    if len(safe_text) > MAX_TEXT_CHARS:
        _raise_api_error(
            413,
            "text_too_large",
            f"Text input exceeds the {MAX_TEXT_CHARS:,}-character limit.",
        )
    return safe_text


def _raise_api_error(status_code: int, code: str, message: str) -> None:
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _required_mobile_api_token() -> str | None:
    token = os.environ.get("PROJECT_PHOENIX_MOBILE_API_TOKEN", "").strip()
    return token or None


def _verify_mobile_api_token(
    x_project_phoenix_token: str | None = Header(default=None),
) -> None:
    expected = _required_mobile_api_token()
    if expected and x_project_phoenix_token != expected:
        _raise_api_error(401, "unauthorized", "Missing or invalid mobile API token.")


def _build_ai_params(options: AnalyzerOptions) -> dict[str, Any] | None:
    explicit_api_key = options.ai_api_key
    env_api_key = os.environ.get("OPENAI_API_KEY") if options.ai_provider == "openai" else os.environ.get("GEMINI_API_KEY")

    if not explicit_api_key and not env_api_key:
        return None

    params: dict[str, Any] = {
        "provider": options.ai_provider,
        "model": options.ai_model,
    }
    if explicit_api_key:
        params["api_key"] = explicit_api_key
    if options.ai_reasoning_effort:
        params["reasoning"] = {"effort": options.ai_reasoning_effort}
    return params


def _build_analyzer(options: AnalyzerOptions) -> CharterAnalyzer:
    return CharterAnalyzer(
        canlii_api_key=options.canlii_api_key,
        ai_params=_build_ai_params(options),
    )


def _build_ai(options: AnalyzerOptions) -> AIIntegration:
    return AIIntegration(
        api_key=options.ai_api_key,
        provider=options.ai_provider,
        model=options.ai_model,
        reasoning={"effort": options.ai_reasoning_effort} if options.ai_reasoning_effort else None,
    )


def _text_metadata(text: str, source_name: str, source_format: str) -> dict[str, Any]:
    paragraphs = _split_paragraphs(text)
    sentences = _split_sentences(text)
    words = text.split()
    return {
        "file_name": source_name,
        "format": source_format,
        "char_count": len(text),
        "word_count": len(words),
        "paragraph_count": len(paragraphs),
        "sentence_count": len(sentences),
        "avg_sentence_length": len(words) / max(len(sentences), 1),
        "avg_paragraph_length": len(words) / max(len(paragraphs), 1),
    }


def _source_payload(kind: str, text: str, metadata: dict[str, Any], processor: DocumentProcessor | None = None) -> dict[str, Any]:
    helper = processor or DocumentProcessor()
    return {
        "kind": kind,
        "metadata": metadata,
        "citations": helper.find_legal_citations(text),
        "key_legal_terms": helper.find_key_legal_terms(text),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=lambda item: str(item))]
    return value


def _public_metadata(metadata: dict[str, Any], file_name: str | None = None) -> dict[str, Any]:
    public = {key: value for key, value in metadata.items() if key != "file_path"}
    if file_name:
        public["file_name"] = file_name
    return public


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _success_payload(request: Request, source: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    return _json_safe(
        {
            "meta": {
                "request_id": _request_id(request),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "source": source,
            "analysis": analysis,
        }
    )


async def _run_analysis(callable_obj):
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(callable_obj),
            timeout=ANALYSIS_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        _raise_api_error(
            504,
            "analysis_timeout",
            f"Analysis exceeded the {ANALYSIS_TIMEOUT_SECONDS}-second timeout.",
        )


async def _read_upload_bytes(file: UploadFile) -> bytes:
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        _raise_api_error(
            413,
            "file_too_large",
            f"Uploaded file exceeds the {MAX_UPLOAD_BYTES:,}-byte limit.",
        )
    return data


def _validate_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_FILE_EXTENSIONS:
        _raise_api_error(
            400,
            "unsupported_file_type",
            f"Unsupported file type '{extension or 'unknown'}'. Supported: {', '.join(sorted(SUPPORTED_FILE_EXTENSIONS))}.",
        )
    return extension


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    request.state.request_id = uuid4().hex[:12]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "http_error", "message": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": detail.get("code", "http_error"),
                "message": detail.get("message", "Request failed."),
                "request_id": _request_id(request),
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled mobile API exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "Unexpected server error.",
                "request_id": _request_id(request),
            }
        },
    )


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "project_phoenix Mobile API",
        "docs": "/docs",
        "health": "/health",
        "limits": {
            "max_text_chars": MAX_TEXT_CHARS,
            "max_upload_bytes": MAX_UPLOAD_BYTES,
            "analysis_timeout_seconds": ANALYSIS_TIMEOUT_SECONDS,
        },
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "auth_required": bool(_required_mobile_api_token()),
    }


@app.post("/analyze/text")
async def analyze_text(
    http_request: Request,
    request: AnalyzeTextRequest,
    _auth: None = Depends(_verify_mobile_api_token),
) -> dict[str, Any]:
    text = _normalize_text(request.text)
    metadata = _text_metadata(text, "inline_text.txt", "text")
    analysis = await _run_analysis(lambda: _build_analyzer(request).analyze_document(text))
    return _success_payload(
        http_request,
        _source_payload("text", text, metadata),
        analysis,
    )


@app.post("/analyze/human-rights")
async def analyze_human_rights(
    http_request: Request,
    request: AnalyzeHumanRightsRequest,
    _auth: None = Depends(_verify_mobile_api_token),
) -> dict[str, Any]:
    text = _normalize_text(request.text)
    metadata = _text_metadata(text, "inline_text.txt", "text")
    analysis = await _run_analysis(
        lambda: _build_analyzer(request).analyze_human_rights_code(
            text,
            include_charter_context=request.include_charter_context,
        )
    )
    return _success_payload(
        http_request,
        _source_payload("text", text, metadata),
        analysis,
    )


@app.post("/analyze/file")
async def analyze_file(
    request: Request,
    file: UploadFile = File(...),
    options: FileAnalysisForm = Depends(),
    _auth: None = Depends(_verify_mobile_api_token),
) -> dict[str, Any]:
    filename = file.filename or "upload.txt"
    suffix = _validate_extension(filename)
    temp_path: str | None = None
    try:
        upload_bytes = await _read_upload_bytes(file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(upload_bytes)
            temp_path = temp_file.name

        processor = DocumentProcessor()
        extracted = await _run_analysis(lambda: processor.load_document(temp_path))
        text = _normalize_text(extracted["text"])
        analysis = await _run_analysis(
            lambda: _build_analyzer(options.to_options()).analyze_document(text)
        )

        return _success_payload(
            request,
            _source_payload(
                "file",
                text,
                _public_metadata(extracted["metadata"], filename or "uploaded_document"),
                processor,
            ),
            analysis,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        _raise_api_error(400, "document_processing_error", str(exc))
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@app.post("/translate")
async def translate_text(
    http_request: Request,
    request: TranslateTextRequest,
    _auth: None = Depends(_verify_mobile_api_token),
) -> dict[str, Any]:
    text = _normalize_text(request.text)
    ai = _build_ai(
        AnalyzerOptions(
            ai_api_key=request.ai_api_key,
            ai_provider=request.ai_provider,
            ai_model=request.ai_model,
            ai_reasoning_effort=request.ai_reasoning_effort,
        )
    )

    result = await _run_analysis(
        lambda: ai.translate_text(
            text=text,
            target_language=request.target_language,
            source_language=request.source_language,
        )
    )

    if result.get("error"):
        _raise_api_error(400, "translation_failed", result["error"])

    return _json_safe(
        {
            "meta": {
                "request_id": _request_id(http_request),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "translation": {
                "source_language": request.source_language or "auto",
                "target_language": request.target_language,
                "translated_text": result.get("content", ""),
            },
        }
    )
