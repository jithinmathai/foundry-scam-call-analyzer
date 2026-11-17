"""Stage 1: turn the scripts in calls_data.py into SSML and synthesize each call to a 16 kHz mono WAV.

Saves calls/<id>.ssml (open it to study the markup), calls/<id>.wav and calls/manifest.json.
Run:  python make_calls.py            # all calls
      python make_calls.py --ssml-only   # write SSML without calling Azure
      python make_calls.py --only 04 07
"""
import argparse
import re
from xml.sax.saxutils import escape

from calls_data import CALLS
from common import CALLS as CALLS_DIR, MANIFEST, load_env, save_json, speech_config

TOKEN = re.compile(r"\{(digits|tel|break):([^}]+)\}")


def to_ssml_text(text: str) -> str:
    out, pos = [], 0
    for m in TOKEN.finditer(text):
        out.append(escape(text[pos:m.start()]))
        kind, val = m.groups()
        if kind == "break":
            out.append(f'<break time="{int(val)}ms"/>')
        elif kind == "digits":
            out.append(f'<say-as interpret-as="digits">{val}</say-as>')
        else:
            out.append(f'<say-as interpret-as="telephone">{val}</say-as>')
        pos = m.end()
    out.append(escape(text[pos:]))
    return "".join(out)


def to_plain(text: str) -> str:
    """Reference transcript: markup removed, numbers kept as written."""
    return TOKEN.sub(lambda m: "" if m.group(1) == "break" else m.group(2), text)


def build_ssml(call: dict) -> str:
    parts = []
    for role, text in call["turns"]:
        voice = call["voices"][role]
        inner = to_ssml_text(text)
        if call.get("urgent") == role:
            inner = f'<prosody rate="+12%" pitch="+5%">{inner}</prosody>'   # pushy, hurried caller
        style = call.get("styles", {}).get(role)
        if style:
            inner = f'<mstts:express-as style="{style}">{inner}</mstts:express-as>'
        parts.append(f'  <voice name="{voice}">{inner}<break time="500ms"/></voice>')
    lang = call["locales"][0]
    return ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            f'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{lang}">\n' + "\n".join(parts) + "\n</speak>")


def synthesize(ssml: str, path):
    import azure.cognitiveservices.speech as speechsdk
    cfg = speech_config()
    cfg.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    synth = speechsdk.SpeechSynthesizer(speech_config=cfg,
                                        audio_config=speechsdk.audio.AudioOutputConfig(filename=str(path)))
    result = synth.speak_ssml_async(ssml).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = result.cancellation_details
        raise SystemExit(f"Synthesis failed for {path.name}: {result.reason} {details.error_details if details else ''}")
    return result.audio_duration.total_seconds()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssml-only", action="store_true")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    load_env()
    CALLS_DIR.mkdir(exist_ok=True)

    manifest = []
    for call in CALLS:
        ssml = build_ssml(call)
        (CALLS_DIR / f"{call['id']}.ssml").write_text(ssml, encoding="utf-8")
        reference = [{"role": r, "text": to_plain(t)} for r, t in call["turns"]]
        entry = {k: call[k] for k in ("id", "title", "label", "scam_type", "locales", "pii")}
        entry.update(file=f"{call['id']}.wav", reference=reference)
        manifest.append(entry)
        if args.ssml_only or (args.only and call["id"] not in args.only):
            print(f"{call['id']}  SSML written            {call['title']}")
            continue
        secs = synthesize(ssml, CALLS_DIR / entry["file"])
        print(f"{call['id']}  {secs:5.1f}s  {call['label']:<8} {call['title']}")
    save_json(MANIFEST, manifest)
    print(f"\nWrote {MANIFEST}")


if __name__ == "__main__":
    main()
