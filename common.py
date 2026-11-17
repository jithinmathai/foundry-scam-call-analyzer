"""Shared helpers: paths, settings, authentication for the AI services, and the call manifest."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent
CALLS = ROOT / "calls"
TRANSCRIPTS = ROOT / "transcripts"
RESULTS = ROOT / "results"
WARNINGS = ROOT / "warnings"
MANIFEST = CALLS / "manifest.json"
COG_SCOPE = "https://cognitiveservices.azure.com/.default"


def load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise SystemExit(f"Missing setting {name}. Copy .env.example to .env and fill it in.")
    return value


def endpoint() -> str:
    return env("AI_SERVICES_ENDPOINT").rstrip("/")


def key() -> str:
    return env("AI_SERVICES_KEY", "")


_credential = None


def credential():
    global _credential
    if _credential is None:
        from azure.identity import DefaultAzureCredential
        _credential = DefaultAzureCredential()
    return _credential


def rest_headers(content_type: str | None = "application/json") -> dict:
    """Headers for REST calls (fast transcription, Translator): key or Entra ID bearer token."""
    h = {}
    if key():
        h["Ocp-Apim-Subscription-Key"] = key()
        if os.getenv("AZURE_REGION"):
            h["Ocp-Apim-Subscription-Region"] = os.getenv("AZURE_REGION")
    else:
        h["Authorization"] = "Bearer " + credential().get_token(COG_SCOPE).token
    if content_type:
        h["Content-Type"] = content_type
    return h


def sdk_credential():
    """Credential object for the Azure SDK clients (Language)."""
    if key():
        from azure.core.credentials import AzureKeyCredential
        return AzureKeyCredential(key())
    return credential()


def speech_config(translation: bool = False):
    """Speech SDK config: key + endpoint, or Entra ID token credential + custom-domain endpoint."""
    import azure.cognitiveservices.speech as speechsdk
    cls = speechsdk.translation.SpeechTranslationConfig if translation else speechsdk.SpeechConfig
    if key():
        return cls(subscription=key(), endpoint=endpoint())
    return cls(token_credential=credential(), endpoint=endpoint())


def manifest() -> list[dict]:
    if not MANIFEST.exists():
        raise SystemExit("No calls yet. Run: python make_calls.py")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
