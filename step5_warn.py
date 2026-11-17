"""Stage 6: speak a short warning to the receiver, in the language of the call.

For every call classified as a scam: take the model's advice, translate it to Hindi when the
call was in Hindi, and synthesize it with SSML (slower rate, a pause, emphasis on the action).
Saves warnings/<id>.wav and warnings/<id>.ssml.
Run:  python step5_warn.py
"""
from xml.sax.saxutils import escape

import azure.cognitiveservices.speech as speechsdk

from common import RESULTS, TRANSCRIPTS, WARNINGS, load_env, load_json, manifest, speech_config
from step2_language import translate

VOICE = {"en": "en-IN-NeerjaNeural", "hi": "hi-IN-SwaraNeural"}
OPENER = {"en": "Warning. This call looks like a scam.", "hi": "सावधान। यह कॉल धोखाधड़ी लगती है।"}


def main():
    load_env()
    WARNINGS.mkdir(exist_ok=True)
    if not (RESULTS / "verdicts.json").exists():
        raise SystemExit("No verdicts yet. Run python step4_classify.py first, then this script.")
    verdicts = load_json(RESULTS / "verdicts.json")
    for call in manifest():
        v = verdicts.get(call["id"])
        if not v or not v["is_scam"]:
            continue
        lang = "hi" if load_json(TRANSCRIPTS / f"{call['id']}.en.json")["call_language"] == "hi" else "en"
        advice = v["advice"] if lang == "en" else translate([v["advice"]], to="hi")[0]
        ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}-IN">'
                f'<voice name="{VOICE[lang]}"><prosody rate="-10%">{escape(OPENER[lang])}<break time="700ms"/>'
                f'{escape(advice)}</prosody></voice></speak>')
        (WARNINGS / f"{call['id']}.ssml").write_text(ssml, encoding="utf-8")
        cfg = speech_config()
        synth = speechsdk.SpeechSynthesizer(
            speech_config=cfg, audio_config=speechsdk.audio.AudioOutputConfig(filename=str(WARNINGS / f"{call['id']}.wav")))
        result = synth.speak_ssml_async(ssml).get()
        status = "ok" if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted else str(result.reason)
        print(f"{call['id']}  [{lang}] {status}  {advice}")
    print(f"\nPlay the files in {WARNINGS}/")


if __name__ == "__main__":
    main()
