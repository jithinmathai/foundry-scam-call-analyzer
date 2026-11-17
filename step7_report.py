"""Stage 8: combine all results into results/report.md.

Run:  python step7_report.py
"""
from common import RESULTS, TRANSCRIPTS, load_json, manifest


def opt(path):
    return load_json(path) if path.exists() else {}


def main():
    calls = manifest()
    pii, pii_rule = opt(RESULTS / "pii.json"), opt(RESULTS / "pii_with_rule.json")
    verdicts, cu = opt(RESULTS / "verdicts.json"), opt(RESULTS / "cu_audio.json")

    lines = ["# Scam call analyser: results", "",
             "## 1. Transcription and language", "",
             "| # | Call | Truth | Speakers | Match to script | Call language |",
             "|---|---|---|---|---|---|"]
    for c in calls:
        t = opt(TRANSCRIPTS / f"{c['id']}.json")
        en = opt(TRANSCRIPTS / f"{c['id']}.en.json")
        spk = len({p["speaker"] for p in t.get("phrases", []) if p.get("speaker") is not None}) if t else "–"
        lines.append(f"| {c['id']} | {c['title']} | {c['label']} | {spk} | "
                     f"{t.get('similarity_to_script', '–')} | {en.get('call_language', '–')} |")

    lines += ["", "## 2. PII redaction", "",
              "| # | Planted values | Missed by Language PII | Missed with extra digit rule | Categories found |",
              "|---|---|---|---|---|"]
    for c in calls:
        p, r = pii.get(c["id"], {}), pii_rule.get(c["id"], {})
        fmt = lambda d: "–" if not d else ("✅ none" if not d["missed"] else "❌ " + ", ".join(d["missed"]))
        lines.append(f"| {c['id']} | {', '.join(c['pii']) or '—'} | {fmt(p)} | {fmt(r)} | {', '.join(p.get('categories', []))} |")

    if verdicts:
        ok = sum(v["correct"] for v in verdicts.values())
        lines += ["", f"## 3. Scam classification ({ok}/{len(verdicts)} correct)", "",
                  "| # | Truth | Verdict | Risk | Predicted type | Red flags |", "|---|---|---|---|---|---|"]
        for c in calls:
            v = verdicts.get(c["id"])
            if v:
                mark = "✅" if v["correct"] else "❌"
                lines.append(f"| {c['id']} | {c['label']} ({c['scam_type']}) | {mark} {'scam' if v['is_scam'] else 'genuine'} | "
                             f"{v['risk_score']} | {v['scam_type']} | {', '.join(v['red_flags'])} |")

    if cu:
        lines += ["", "## 4. Content Understanding prebuilt-audioSearch", "",
                  "| # | Speakers | Match to script | Generated summary |", "|---|---|---|---|"]
        for c in calls:
            r = cu.get(c["id"])
            if r:
                lines.append(f"| {c['id']} | {len(r['speakers'])} | {r['similarity_to_script']} | {r['summary']} |")

    lines += ["", "## 5. Findings (fill in)", "",
              "- Did diarization find exactly two speakers on every call? Where did it merge or split them?",
              "- How did the Hindi and mixed-language calls (03, 07, 08) transcribe and translate?",
              "- Which planted values did PII redaction miss (OTPs? card digits? Aadhaar?), and why?",
              "- Did the classifier flag any genuine call (01-03)? Which red flags drove each verdict?",
              "- What does Content Understanding give you in one call, and what does the custom pipeline do better?"]
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
