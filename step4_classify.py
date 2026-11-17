"""Stage 5: classify each call with an LLM that must answer in a fixed JSON schema (structured output).

Uses the Responses API through the Foundry project endpoint. The model only ever sees the
REDACTED English transcript from Stage 4.
Run:  python step4_classify.py
"""
import json

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from common import RESULTS, TRANSCRIPTS, env, load_env, load_json, manifest, save_json

SCAM_TYPES = ["none", "bank_impersonation_otp", "digital_arrest", "tech_support", "kyc_update",
              "lottery_fee", "utility_disconnection", "task_job", "other_scam"]
RED_FLAGS = ["urgency_or_threat", "asks_for_otp_or_pin", "asks_for_id_or_account_number",
             "asks_for_payment_or_transfer", "impersonates_bank_or_authority", "asks_for_remote_access",
             "asks_for_secrecy", "too_good_to_be_true", "moves_to_other_channel"]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["is_scam", "scam_type", "risk_score", "red_flags", "caller_asked_for", "advice"],
    "properties": {
        "is_scam": {"type": "boolean"},
        "scam_type": {"type": "string", "enum": SCAM_TYPES},
        "risk_score": {"type": "integer", "description": "0 = clearly genuine, 100 = certain scam"},
        "red_flags": {"type": "array", "items": {"type": "string", "enum": RED_FLAGS}},
        "caller_asked_for": {"type": "array", "items": {"type": "string"},
                             "description": "What the caller tried to obtain, in a few words each"},
        "advice": {"type": "string", "description": "One short sentence telling the receiver what to do now"},
    },
}

INSTRUCTIONS = (
    "You are a fraud analyst for an Indian bank. Read the redacted phone-call transcript "
    "(lines start with Caller: or Receiver:; *** marks redacted data) and decide whether the CALLER "
    "is running a scam. Genuine organisations never ask for OTPs, PINs, remote access or fees to "
    "release money. Base the verdict only on the transcript."
)


def main():
    load_env()
    project = AIProjectClient(endpoint=env("FOUNDRY_PROJECT_ENDPOINT"), credential=DefaultAzureCredential())
    oa = project.get_openai_client()
    model = env("DEPLOYMENT", "gpt-4.1-mini")

    results, correct = {}, 0
    print(f"{'id':<3} {'truth':<8} {'verdict':<8} {'risk':<5} {'type (pred / truth)':<48} red flags")
    for call in manifest():
        transcript = load_json(TRANSCRIPTS / f"{call['id']}.redacted.json")["text_redacted"]
        resp = oa.responses.create(
            model=model, instructions=INSTRUCTIONS, input=transcript, temperature=0,
            text={"format": {"type": "json_schema", "name": "call_verdict", "schema": SCHEMA, "strict": True}},
        )
        v = json.loads(resp.output_text)
        ok = v["is_scam"] == (call["label"] == "scam")
        correct += ok
        results[call["id"]] = {**v, "truth_label": call["label"], "truth_type": call["scam_type"], "correct": ok}
        types = f"{v['scam_type']} / {call['scam_type']}"
        print(f"{call['id']:<3} {call['label']:<8} {('scam' if v['is_scam'] else 'genuine'):<8} {v['risk_score']:<5} "
              f"{types:<48} {', '.join(v['red_flags'])[:60]}")
    save_json(RESULTS / "verdicts.json", results)
    print(f"\nScam / genuine accuracy: {correct}/{len(results)}. Saved results/verdicts.json")


if __name__ == "__main__":
    main()
