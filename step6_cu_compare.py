"""Stage 7 (optional): run the same audio through Content Understanding prebuilt-audioSearch.

One call gives you a transcript with speakers AND a generated Summary field. Compare that with
the Speech fast transcription + LLM pipeline you built in stages 2-5.
Needs Content Understanding model defaults (gpt-4.1-mini + text-embedding-3-large) configured
on the resource; see the README troubleshooting table.
Run:  python step6_cu_compare.py
"""
import difflib
import os
import re

from azure.ai.contentunderstanding import ContentUnderstandingClient

from common import CALLS, RESULTS, endpoint, load_env, manifest, save_json, sdk_credential


def similarity(a, b):
    wa, wb = re.findall(r"\w+", a.lower()), re.findall(r"\w+", b.lower())
    return difflib.SequenceMatcher(None, wa, wb).ratio()


def main():
    load_env()
    ep = os.getenv("CONTENTUNDERSTANDING_ENDPOINT") or endpoint()
    client = ContentUnderstandingClient(endpoint=ep, credential=sdk_credential())
    out = {}
    for call in manifest():
        data, content = (CALLS / call["file"]).read_bytes(), None
        for ctype in ("audio/wav", "application/octet-stream"):
            result = client.begin_analyze_binary(analyzer_id="prebuilt-audioSearch",
                                                 binary_input=data, content_type=ctype).result()
            if result.contents:
                content = result.contents[0]
                break
            warns = "; ".join(f"{getattr(w, 'code', '')} {getattr(w, 'message', w)}" for w in (result.warnings or []))
            print(f"{call['id']}  no content with content_type={ctype}. Warnings: {warns or 'none'}")
        if content is None:
            out[call["id"]] = {"speakers": [], "similarity_to_script": 0, "summary": "(no content returned)"}
            continue
        phrases = getattr(content, "transcript_phrases", None) or []
        text = " ".join(p.text for p in phrases)
        speakers = sorted({str(p.speaker) for p in phrases if getattr(p, "speaker", None) is not None})
        summary = content.fields.get("Summary").value if content.fields and content.fields.get("Summary") else ""
        ref = " ".join(t["text"] for t in call["reference"])
        out[call["id"]] = {"speakers": speakers, "similarity_to_script": round(similarity(text, ref), 3),
                           "summary": summary}
        print(f"{call['id']}  speakers={len(speakers)}  match={out[call['id']]['similarity_to_script']}\n    {summary}")
    save_json(RESULTS / "cu_audio.json", out)
    print("\nSaved results/cu_audio.json. Does the generated summary spot the scam on its own?")


if __name__ == "__main__":
    main()
