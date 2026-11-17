"""Stage 2b (exam drill): real-time Speech SDK recognition on one call.

Shows three things the exam likes to test:
  1. recognize_once_async() returns only the FIRST utterance (stops at the first pause)
  2. continuous recognition (start_continuous_recognition + 'recognized' events) gets the whole call
  3. speech translation: TranslationRecognizer with speech_recognition_language + add_target_language

Run:  python step1b_realtime.py --call 04
      python step1b_realtime.py --call 07 --translate      # Hindi call, translated to English live
"""
import argparse
import threading

import azure.cognitiveservices.speech as speechsdk

from common import CALLS, load_env, manifest, speech_config


def once(path, lang):
    cfg = speech_config()
    cfg.speech_recognition_language = lang
    rec = speechsdk.SpeechRecognizer(speech_config=cfg, audio_config=speechsdk.audio.AudioConfig(filename=str(path)))
    return rec.recognize_once_async().get().text


def continuous(path, lang):
    cfg = speech_config()
    cfg.speech_recognition_language = lang
    rec = speechsdk.SpeechRecognizer(speech_config=cfg, audio_config=speechsdk.audio.AudioConfig(filename=str(path)))
    lines, done = [], threading.Event()
    rec.recognized.connect(lambda evt: lines.append(evt.result.text))
    rec.session_stopped.connect(lambda evt: done.set())
    rec.canceled.connect(lambda evt: done.set())
    rec.start_continuous_recognition()
    done.wait(timeout=180)
    rec.stop_continuous_recognition()
    return lines


def translate(path, lang, target="en"):
    cfg = speech_config(translation=True)
    cfg.speech_recognition_language = lang
    cfg.add_target_language(target)
    rec = speechsdk.translation.TranslationRecognizer(translation_config=cfg,
                                                      audio_config=speechsdk.audio.AudioConfig(filename=str(path)))
    lines, done = [], threading.Event()
    rec.recognized.connect(lambda evt: lines.append((evt.result.text, evt.result.translations.get(target, ""))))
    rec.session_stopped.connect(lambda evt: done.set())
    rec.canceled.connect(lambda evt: done.set())
    rec.start_continuous_recognition()
    done.wait(timeout=180)
    rec.stop_continuous_recognition()
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--call", default="04")
    ap.add_argument("--translate", action="store_true")
    args = ap.parse_args()
    load_env()
    call = next(c for c in manifest() if c["id"] == args.call)
    path, lang = CALLS / call["file"], call["locales"][-1] if args.translate else call["locales"][0]

    if args.translate:
        print(f"== Speech translation {lang} -> en, call {call['id']} ==")
        for src, en in translate(path, lang):
            print(f"  {src}\n    -> {en}")
        return
    print(f"== recognize_once_async, call {call['id']} ==\n  {once(path, lang)}")
    print("\n== continuous recognition ==")
    for line in continuous(path, lang):
        print("  " + line)
    print("\nNotice: recognize_once stopped after the first utterance. Fast transcription (step 1) "
          "also labels who spoke; real-time diarization needs ConversationTranscriber.")


if __name__ == "__main__":
    main()
