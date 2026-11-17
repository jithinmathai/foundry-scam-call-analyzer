"""Stage 4: detect and redact PII in the English transcript before anything is stored or sent to an LLM.

Uses Azure Language recognize_pii_entities -> redacted_text + entities (category, confidence).
Then checks every value planted in the script (names, OTPs, card digits, account numbers,
phone numbers, Aadhaar) and reports which ones are STILL visible after redaction.

Run:  python step3_pii.py
      python step3_pii.py --extra-otp-rule     # add a simple app-side rule for 4-12 digit codes
"""
import argparse
import re

from azure.ai.textanalytics import TextAnalyticsClient

from common import RESULTS, TRANSCRIPTS, endpoint, load_env, load_json, manifest, save_json, sdk_credential

DIGIT_CODE = re.compile(r"(?<!\w)(?:\d[\s-]?){4,12}(?!\w)")


def digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def still_visible(value: str, text: str) -> bool:
    if digits(value) and len(digits(value)) >= 4:
        return digits(value) in digits(text)
    return value.lower() in text.lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra-otp-rule", action="store_true")
    args = ap.parse_args()
    load_env()
    client = TextAnalyticsClient(endpoint=endpoint(), credential=sdk_credential())

    summary = {}
    print(f"{'id':<3} {'entities found':<40} {'planted':<8} {'missed':<7} missed values")
    for call in manifest():
        t = load_json(TRANSCRIPTS / f"{call['id']}.en.json")
        text = t["text_en"][:5000]
        doc = client.recognize_pii_entities([text], language="en")[0]
        if doc.is_error:
            raise SystemExit(f"{call['id']}: {doc.error}")
        redacted = doc.redacted_text
        if args.extra_otp_rule:
            redacted = DIGIT_CODE.sub(lambda m: "*" * len(m.group(0)), redacted)
        cats = sorted({e.category for e in doc.entities})
        missed = [v for v in call["pii"] if still_visible(v, redacted)]
        summary[call["id"]] = {"categories": cats, "planted": call["pii"], "missed": missed,
                               "entities": [{"text": e.text, "category": e.category,
                                             "confidence": round(e.confidence_score, 2)} for e in doc.entities]}
        save_json(TRANSCRIPTS / f"{call['id']}.redacted.json", {"id": call["id"], "text_redacted": redacted})
        print(f"{call['id']:<3} {', '.join(cats)[:40]:<40} {len(call['pii']):<8} {len(missed):<7} {', '.join(missed)}")

    name = "pii_with_rule.json" if args.extra_otp_rule else "pii.json"
    save_json(RESULTS / name, summary)
    print(f"\nSaved results/{name}. Redacted transcripts: transcripts/<id>.redacted.json")
    print("Look at which categories caught card digits, OTPs and account numbers, and which values slipped through.")


if __name__ == "__main__":
    main()
