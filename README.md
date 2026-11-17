# Scam call analyser: a speech and language lab for Microsoft Foundry

Phone scams ("vishing") are a real fraud problem: a fake bank fraud team asking for an OTP, a
"customs officer" announcing a *digital arrest*, a KYC update that must happen tonight. In this lab you
build a pipeline that listens to a recorded call and decides whether it's a scam, what the caller
wanted, and what personal data must be redacted. Then it warns the receiver out loud, in their language.

```
Synthetic calls      Fast transcription     Language detection     PII detection     LLM classifier        Spoken warning
(TTS + SSML)    →    + diarization     →    + Translator      →    + redaction   →   (structured JSON) →   (TTS, en / hi)
make_calls.py        step1_transcribe       step2_language         step3_pii         step4_classify        step5_warn
```

**Time:** about 4 hours for the core, plus an hour for the extras. **Cost:** small. Ten calls of
about 40 seconds each, a few hundred Language and Translator calls, and ten LLM calls.

> ⚠️ **Synthetic only.** Every call is generated with text-to-speech from the scripts in
> `calls_data.py`. Names, organisations (Contoso Bank, Fabrikam Courier…), phone numbers, OTPs and
> ID numbers are made up. Never feed real call recordings into a lab like this.

## The ten calls

| # | Call | Truth | Language | Planted PII |
|---|---|---|---|---|
| 01 | Bank card delivery confirmation | genuine | English | none |
| 02 | Courier delivery slot | genuine | English | name |
| 03 | Clinic appointment reminder | genuine | Hindi | none |
| 04 | Fake bank fraud team asks for OTP | scam | English | name, card digits, OTP |
| 05 | Courier parcel and "digital arrest" | scam | English | bank account number |
| 06 | Fake tech support, remote access | scam | English | remote-access code |
| 07 | KYC update scam | scam | Hindi | Aadhaar-style number, OTP |
| 08 | Lottery prize fee | scam | Hindi caller, English reply | email address |
| 09 | Electricity disconnection tonight | scam | English | two phone numbers |
| 10 | Part-time "like and earn" job | scam | English | name |

## Sample results

One run, gpt-4.1-mini (Global Standard), November 2026:

- **Classification:** all **7 scams flagged**, **0 of 3 genuine calls** flagged. That includes call 01,
  a genuine bank call that mentions OTPs only to warn the customer.
- **Spoken warnings:** advice specific to each scam type, spoken in Hindi for the Hindi calls (07, 08) via Translator and `hi-IN-SwaraNeural`.
  For example, call 04: *"Do not share OTPs with anyone and hang up immediately; contact your bank directly using official numbers."*
- Ten calls is a small test set: it shows the pipeline works, not production accuracy. Run it and compare your own report.

## Files

| File | Stage | What it does |
|---|---|---|
| `calls_data.py` | – | The ten scripts, voices and planted PII. Add your own calls here |
| `make_calls.py` | 1 | Builds SSML per call and synthesizes 16 kHz mono WAVs |
| `step1_transcribe.py` | 2 | Fast transcription with speaker diarization; compares with the script |
| `step1b_realtime.py` | 2b | Speech SDK drill: `recognize_once_async` vs continuous recognition vs speech translation |
| `step2_language.py` | 3 | Language detection per call and per line; Translator for Hindi lines |
| `step3_pii.py` | 4 | PII detection and redaction; checks which planted values were missed |
| `step4_classify.py` | 5 | LLM classifier with a strict JSON schema (Responses API) |
| `step5_warn.py` | 6 | Spoken warning in English or Hindi with SSML |
| `step6_cu_compare.py` | 7 | Optional: Content Understanding `prebuilt-audioSearch` on the same audio |
| `step7_report.py` | 8 | Writes `results/report.md` |

---

## Step 0: Prerequisites (10 min)

- An Azure subscription, Python 3.10 or later, the Azure CLI, and `az login`
- Something to play WAV files with

## Step 1: Foundry resource, roles and model (15 min)

1. Use your Foundry resource from the first lab, or create one at **ai.azure.com**. The region must
   support **fast transcription** and the **en-IN / hi-IN neural voices**. Check the Speech region and
   language support pages on Microsoft Learn. East US and Central India are reasonable choices.
2. In the Azure portal, open the resource's **Keys and Endpoint** page and copy the
   **Azure AI services** endpoint: `https://<res>.cognitiveservices.azure.com/`. Speech, Language and
   Translator all use this custom-domain endpoint.
3. **Roles:** assign yourself **Cognitive Services User** on the resource (needed for Speech, Language
   and Translator with Entra ID), plus **Foundry User** on the project.
4. Deploy **gpt-4.1-mini** (Global Standard) if you don't have it already.

> **AI-103:** Entra ID authentication for Speech and Translator needs a **custom subdomain** endpoint.
> The shared regional endpoint only works with keys.

## Step 2: Set up locally (10 min)

```powershell
pip install -r requirements.txt
copy .env.example .env      # then fill in AI_SERVICES_ENDPOINT and FOUNDRY_PROJECT_ENDPOINT
```
Leave `AI_SERVICES_KEY` empty to use `az login`. If you use a key, also set `AZURE_REGION`.

## Step 3: Make the calls with SSML (20 min)

```bash
python make_calls.py
```

Open `calls/04.ssml` and `calls/03.ssml` to see what was sent. Then play a few WAVs.

| SSML you'll see | What it does |
|---|---|
| Several `<voice name="…">` elements in one `<speak>` | Two people in one conversation |
| `<prosody rate="+12%" pitch="+5%">` | The scam caller sounds hurried and pushy |
| `<break time="500ms"/>` | Pauses between turns, which also helps diarization |
| `<say-as interpret-as="digits">` / `"telephone"` | OTPs read digit by digit; phone numbers read as phone numbers |
| `<mstts:express-as style="empathetic">` | A speaking style. It needs the `mstts` namespace and a voice that supports the style (`hi-IN-SwaraNeural` does) |

> **AI-103:** `speak_ssml_async` vs `speak_text_async`; output format with
> `set_speech_synthesis_output_format`; `AudioOutputConfig(filename=…)` to write a file.
> **Custom voice** is for synthesis, while **custom speech** is for recognition.

## Step 4: Transcribe with diarization (20 min)

```bash
python step1_transcribe.py
```

Each call goes to `POST /speechtotext/transcriptions:transcribe?api-version=2025-10-15` as multipart
form data: the audio plus a `definition` with `locales` and `"diarization": {"enabled": true, "maxSpeakers": 2}`.
The table shows the speakers found, the locales detected per phrase, and a 0–1 match against the script.

**What to look for**
- Did every call get exactly **2** speakers? Same-gender voice pairs are harder to separate.
- Call 08 sends two candidate locales (`en-IN`, `hi-IN`). Check the per-phrase `locale` in `transcripts/08.json`.
- How do OTPs come out: `739154`, `7 3 9 1 5 4`, or words?

**Drill (10 min):**
```bash
python step1b_realtime.py --call 04
python step1b_realtime.py --call 07 --translate
```

> **AI-103:** real-time vs **fast** (synchronous, files) vs **batch** (asynchronous, large volumes)
> transcription. `recognize_once_async` stops after one utterance, so use continuous recognition for
> a whole call. Diarization needs **mono** audio. Speech translation uses `SpeechTranslationConfig`,
> `speech_recognition_language` and `add_target_language`.

## Step 5: Language detection and translation (15 min)

```bash
python step2_language.py
```

This calls `detect_language` (with `country_hint="IN"`) on the whole call and on each line, then
sends non-English lines to Translator at `/translator/text/v3.0/translate?api-version=3.0&to=en` on
your custom domain.

**What to look for:** call 08 gets **one** primary language for the whole call, even though half of
it is Hindi. Document-level detection hides code-switching, so detect per line.

> **AI-103:** Language detection returns one primary language per document. Translator can
> auto-detect the source if you omit `from`. **Document translation** (whole files, batch, blob
> storage) is a different API. Custom Translator quality is measured as **BLEU** (0–100).

## Step 6: Detect and redact PII (20 min)

```bash
python step3_pii.py
python step3_pii.py --extra-otp-rule
```

`recognize_pii_entities` returns `redacted_text` and entities with a category and confidence. The
script checks every value planted in the scripts and lists any that are **still visible** after redaction.

**What to look for**
- Which categories did it find? Look for things like Person, PhoneNumber, Email, and bank or ID number categories.
- Were the **OTPs** and the remote-access code redacted? A one-time password isn't a standard PII
  category, so an app-side rule (`--extra-otp-rule`) may be needed. Compare the two runs.
- The LLM in the next step only ever sees the redacted text. That's the point of this stage.

> **AI-103:** PII detection vs NER; `redacted_text`; filtering by category; PHI uses
> Text Analytics for health. Features scheduled for retirement (such as sentiment and key phrases)
> point toward an **LLM with structured output**, which is the next step.

## Step 7: Classify with structured output (20 min)

```bash
python step4_classify.py
```

The Responses API is called with `text={"format": {"type": "json_schema", "strict": True, ...}}`.
The model must return `is_scam`, `scam_type` (an enum), `risk_score`, `red_flags` (an enum list),
`caller_asked_for` and `advice`. Invalid JSON isn't possible in strict mode.

**What to look for:** false positives on the genuine calls, especially 01, which *mentions* OTPs
in order to warn about them. Check whether the predicted `scam_type` matches the truth, and which red flags appear.

## Step 8: Speak the warning (10 min)

```bash
python step5_warn.py
```

For each scam, the model's advice is translated to Hindi for Hindi calls, wrapped in SSML at a
slower rate after a pause, and saved to `warnings/<id>.wav`.

## Step 9 (optional): Content Understanding on audio (20 min)

```bash
python step6_cu_compare.py
```

`prebuilt-audioSearch` returns a transcript with speakers **and** a generated summary in one call.
It needs Content Understanding model defaults (gpt-4.1-mini and text-embedding-3-large) set on the
resource; see the SDK's `sample_update_defaults.py`. Compare: what do you get for free, and what
does the custom pipeline (redaction, enums, risk score) do that it doesn't?

## Step 10: Report and clean up (10 min)

```bash
python step7_report.py
```

Open `results/report.md`, answer the five findings questions, then delete the resource group if you
created one just for this lab.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `401` on Speech, Language or Translator | Assign **Cognitive Services User** on the resource, wait a few minutes, then `az login` again. Use the `cognitiveservices.azure.com` endpoint |
| Synthesis failed: voice not found | The voice isn't in your region. Pick another `en-IN` / `hi-IN` voice from the voice gallery and change `calls_data.py` |
| Fast transcription `404` / `400` | Check the region supports fast transcription, and that the audio is WAV, mono, under the size limit |
| Translator `401` with a key | Set `AZURE_REGION` in `.env` |
| Every call shows 1 speaker | Use voices of different genders for the two roles, or increase the `<break>` between turns |
| Content Understanding "default model deployment" error | Configure the model defaults (Step 9) or skip this optional stage |

## AI-103 exam topics covered

| Area | Topics |
|---|---|
| Speech | SSML (`voice`, `prosody`, `break`, `say-as`, `express-as`), neural voices, output formats, real-time vs fast vs batch, diarization, `recognize_once_async`, continuous recognition, speech translation |
| Language | Language detection, PII detection and redaction, entity categories, LLM structured output as the replacement for retiring features |
| Translator | Text translation, custom-domain endpoint with Entra ID, document translation vs text translation |
| Generative AI | Responses API, strict JSON schema, enums |
| Information extraction | Content Understanding `prebuilt-audioSearch` vs a custom pipeline |

## License

MIT, see [LICENSE](LICENSE). Independent learning project, not affiliated with or endorsed by Microsoft.
