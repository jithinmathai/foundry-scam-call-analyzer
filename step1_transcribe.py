"""Stage 2: transcribe every call with the fast transcription API and speaker diarization.

POST {endpoint}/speechtotext/transcriptions:transcribe?api-version=2025-10-15  (multipart: audio + definition)
definition = {"locales": [...], "diarization": {"enabled": true, "maxSpeakers": 2}}

Saves transcripts/<id>.json with phrases (speaker, locale, text) and prints, per call:
speakers found, locales detected, and how close the transcript is to the script.
Run:  python step1_transcribe.py
"""
import difflib
import json
import re

import requests

from common import CALLS, TRANSCRIPTS, endpoint, load_env, manifest, rest_headers, save_json

API = "/speechtotext/transcriptions:transcribe?api-version=2025-10-15"


def similarity(a: str, b: str) -> float:
    wa, wb = re.findall(r"\w+", a.lower()), re.findall(r"\w+", b.lower())
    return difflib.SequenceMatcher(None, wa, wb).ratio()


def transcribe(path, locales):
    definition = {"locales": locales, "diarization": {"enabled": True, "maxSpeakers": 2}}
    with open(path, "rb") as f:
        r = requests.post(endpoint() + API, headers=rest_headers(content_type=None),
                          files={"audio": (path.name, f, "audio/wav"),
                                 "definition": (None, json.dumps(definition), "application/json")},
                          timeout=120)
    if r.status_code >= 400:
        raise SystemExit(f"{path.name}: HTTP {r.status_code} {r.text[:300]}")
    return r.json()


def main():
    load_env()
    print(f"{'id':<3} {'speakers':<9} {'locales':<16} {'match':<6} title")
    for call in manifest():
        body = transcribe(CALLS / call["file"], call["locales"])
        phrases = [{"speaker": p.get("speaker"), "locale": p.get("locale"), "text": p["text"],
                    "offset_ms": p.get("offsetMilliseconds")} for p in body.get("phrases", [])]
        full = " ".join(p["text"] for p in phrases)
        ref = " ".join(t["text"] for t in call["reference"])
        out = {"id": call["id"], "duration_ms": body.get("durationMilliseconds"), "phrases": phrases,
               "text": full, "similarity_to_script": round(similarity(full, ref), 3)}
        save_json(TRANSCRIPTS / f"{call['id']}.json", out)
        speakers = sorted({p["speaker"] for p in phrases if p["speaker"] is not None})
        locales = sorted({p["locale"] for p in phrases if p["locale"]})
        print(f"{call['id']:<3} {len(speakers):<9} {','.join(locales):<16} {out['similarity_to_script']:<6} {call['title']}")
    print(f"\nSaved transcripts to {TRANSCRIPTS}/  (open one to see speaker labels per phrase)")


if __name__ == "__main__":
    main()
