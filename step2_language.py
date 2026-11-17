"""Stage 3: language detection (Azure Language) and translation of Hindi lines to English (Translator).

- detect_language on the whole call (one primary language per document) and on each line
- Translator REST: POST {endpoint}/translator/text/v3.0/translate?api-version=3.0&to=en
  (custom-domain path, so Entra ID works; with a key, set AZURE_REGION too)

Saves transcripts/<id>.en.json: one line per phrase with speaker role, detected language,
original text and English text.
Run:  python step2_language.py
"""
import requests
from azure.ai.textanalytics import TextAnalyticsClient

from common import TRANSCRIPTS, endpoint, load_env, load_json, manifest, rest_headers, save_json, sdk_credential

BATCH = 5


def detect(client, texts):
    out = []
    for i in range(0, len(texts), BATCH):
        for doc in client.detect_language(texts[i:i + BATCH], country_hint="IN"):
            out.append(doc.primary_language.iso6391_name if not doc.is_error else "?")
    return out


def translate(texts, to="en"):
    if not texts:
        return []
    url = endpoint() + f"/translator/text/v3.0/translate?api-version=3.0&to={to}"
    r = requests.post(url, headers=rest_headers(), json=[{"Text": t} for t in texts], timeout=30)
    if r.status_code >= 400:
        raise SystemExit(f"Translator HTTP {r.status_code}: {r.text[:300]}")
    return [item["translations"][0]["text"] for item in r.json()]


def main():
    load_env()
    client = TextAnalyticsClient(endpoint=endpoint(), credential=sdk_credential())
    print(f"{'id':<3} {'call language':<14} {'lines hi/en':<12} title")
    for call in manifest():
        t = load_json(TRANSCRIPTS / f"{call['id']}.json")
        phrases = [p for p in t["phrases"] if p["text"].strip()]
        texts = [p["text"] for p in phrases]
        call_lang = detect(client, [t["text"][:5000]])[0]
        line_langs = detect(client, texts)

        to_translate = [i for i, lang in enumerate(line_langs) if lang != "en"]
        translated = dict(zip(to_translate, translate([texts[i] for i in to_translate])))

        first_speaker = phrases[0]["speaker"] if phrases else None
        lines = [{"role": "Caller" if p["speaker"] == first_speaker else "Receiver",
                  "speaker": p["speaker"], "language": line_langs[i],
                  "text": p["text"], "text_en": translated.get(i, p["text"])}
                 for i, p in enumerate(phrases)]
        save_json(TRANSCRIPTS / f"{call['id']}.en.json",
                  {"id": call["id"], "call_language": call_lang, "lines": lines,
                   "text_en": "\n".join(f"{l['role']}: {l['text_en']}" for l in lines)})
        hi = sum(1 for l in lines if l["language"] != "en")
        print(f"{call['id']:<3} {call_lang:<14} {f'{hi}/{len(lines) - hi}':<12} {call['title']}")
    print("\nNote how a mixed call (08) still gets ONE primary language at document level,"
          " while per-line detection splits it. Saved transcripts/<id>.en.json")


if __name__ == "__main__":
    main()
