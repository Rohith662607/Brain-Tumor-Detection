"""
llm_report.py
--------------
REPLACES backend/app/llm_report.py (v5)

Only change: generate_report() was getting cut off mid-sentence — the
150-200 word report plus 3 sections plus a long disclaimer sometimes ran
past the old max_tokens=550 budget. Fixed two ways:
  1. Explicit word cap in the prompt (under 280 words total) so the model
     itself budgets its length instead of running long.
  2. max_tokens raised to 900 as headroom, so even if it runs a bit over,
     it still finishes cleanly rather than stopping mid-sentence.
  3. Expanded to 5 bounded sections per your request: Findings, Impression,
     Recommendations, General Suggestions, Summary.
Nothing else changed from v4.
"""
import logging

from .config import settings

logger = logging.getLogger("uvicorn.error")

_client = None

APP_OVERVIEW = (
    "ArbudaScan is an AI-assisted brain tumor detection and analysis tool. "
    "It runs a YOLOv11 object-detection model over axial, coronal, and sagittal "
    "T1-weighted contrast-enhanced (T1WCE) brain MRI slices, flagging suspicious "
    "regions ('positive') versus clear tissue ('negative') with a bounding box, "
    "confidence score, and area percentage for each detection. Every scan is "
    "saved to History with a unique numeric Scan ID, can generate an on-demand "
    "AI narrative report, and has its own scoped chat for follow-up questions. "
    "This assistant can explain how the app works and discuss specific past "
    "scans by ID or filename using the scan data provided to it, but it never "
    "provides a medical diagnosis — only a qualified radiologist can confirm "
    "any finding."
)


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI  # imported lazily so the app still boots without the package during dev

        _client = OpenAI(
            base_url=settings.github_models_endpoint,
            api_key=settings.github_token,
        )
    return _client


def _require_configured():
    if not settings.enable_ai_report:
        raise RuntimeError("AI features are disabled (APP_ENABLE_AI_REPORT=false in backend/.env).")
    if not settings.github_token:
        raise RuntimeError("No AI API key is set in backend/.env (APP_GITHUB_TOKEN).")


def _chat(messages: list[dict], max_tokens: int = 500, temperature: float = 0.4) -> str:
    client = _get_client()
    logger.info(f"Calling AI model={settings.github_model} endpoint={settings.github_models_endpoint} max_tokens={max_tokens}")
    response = client.chat.completions.create(
        model=settings.github_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    choice = response.choices[0]
    content = choice.message.content
    if not content or not content.strip():
        raise RuntimeError("The model returned an empty response.")
    if getattr(choice, "finish_reason", None) == "length":
        logger.warning("AI response was truncated by max_tokens — consider raising it further.")
    return content.strip()


def _detections_block(summary: dict) -> str:
    detections = summary.get("detections", [])
    lines = []
    for i, d in enumerate(detections, start=1):
        lines.append(
            f"{i}. class={d['class_name']} confidence={d['confidence']:.2f} "
            f"bbox_xyxy={d['bbox_xyxy']} area_pct_of_image={d['area_pct_of_image']}"
        )
    return "\n".join(lines) if lines else "(no regions above the confidence threshold)"


def scan_facts_text(summary: dict) -> str:
    return (
        f"Tumor detected: {summary['tumor_detected']}\n"
        f"Number of detections: {summary['num_detections']}\n"
        f"Total tumor area: {summary['total_tumor_area_pct']}% of the image\n\n"
        f"Detections:\n{_detections_block(summary)}"
    )


def generate_report(summary: dict) -> str:
    _require_configured()

    prompt = (
        "You are assisting a radiology workflow demo tool. Below is structured "
        "output from an object-detection model that scanned a single brain MRI "
        f"slice for tumor regions.\n\n{scan_facts_text(summary)}\n\n"
        "Write a structured report using exactly these section headers, each on "
        "its own line: 'Findings:', 'Impression:', 'Recommendations:', "
        "'General Suggestions:', 'Summary:'.\n"
        "- Findings: 2-4 short bullet points (one per detection, or one per "
        "notable pattern) describing location (left/right, central) and "
        "relative size in plain language based on the bounding box "
        "coordinates and area percentage, noting each one's confidence.\n"
        "- Impression: 1-2 sentences on what this detection pattern likely "
        "means, without diagnosing a specific tumor type or grade.\n"
        "- Recommendations: exactly 3 numbered, clinically sensible next "
        "steps (e.g. radiologist review, clinical correlation, follow-up "
        "imaging).\n"
        "- General Suggestions: exactly 2 numbered general, practical "
        "suggestions for the patient/care team (e.g. keeping prior scans "
        "for comparison, scheduling a specialist consultation).\n"
        "- Summary: 1-2 plain-language sentences wrapping up the overall "
        "finding for a quick read.\n"
        "After Summary, end with exactly this sentence on its own line: "
        "\"This is an AI-generated summary from an automated detection model "
        "and is not a medical diagnosis — findings must be confirmed by a "
        "qualified radiologist.\"\n"
        "IMPORTANT: keep the entire report under 280 words total so nothing "
        "gets cut off — be concise in every section. Do not invent clinical "
        "details (tumor type, grade, patient history) that aren't derivable "
        "from the detection data above."
    )
    return _chat(
        messages=[
            {"role": "system", "content": "You are a concise, careful clinical-support writing assistant. You always finish every section you start and never stop mid-sentence."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=900,
    )


def answer_question(summary: dict, history: list[dict], question: str) -> str:
    _require_configured()

    system_msg = {
        "role": "system",
        "content": (
            "You are a concise, careful clinical-support assistant answering "
            "questions about ONE brain MRI scan's automated detection results. "
            "Only use the scan data given to you. If asked for a diagnosis, "
            "tumor type, grade, or treatment recommendation, say plainly that "
            "you can only describe what the detection model output, not "
            "provide a medical diagnosis, and that a qualified radiologist "
            "must confirm any finding. Keep answers brief (2-5 sentences) "
            "unless the user asks for more detail."
        ),
    }
    context_msg = {"role": "system", "content": f"Scan data for this conversation:\n\n{scan_facts_text(summary)}"}
    messages = [system_msg, context_msg] + history + [{"role": "user", "content": question}]
    return _chat(messages=messages, max_tokens=400)


def assistant_reply(history: list[dict], question: str, history_index: str, matched_details: str = "") -> str:
    """Powers the global sidebar Assistant. Answers app/scan questions using
    the grounded data below; for anything else, it still answers from
    general knowledge but flags that it's outside the app's scope — it
    never just refuses."""
    _require_configured()

    system_msg = {
        "role": "system",
        "content": (
            APP_OVERVIEW + "\n\n"
            "You'll get two kinds of questions:\n"
            "1. About ArbudaScan itself, or about a specific past scan (by ID or "
            "filename) — answer these using the app description and scan data "
            "given to you below.\n"
            "2. General-knowledge questions unrelated to the app — answer these "
            "normally and accurately using your own knowledge. After answering, "
            "add one short closing line noting this is outside what ArbudaScan "
            "itself covers, and that you're happy to help with the app or a scan "
            "instead. Never refuse or deflect a general question without "
            "answering it first.\n"
            "Keep answers concise (2-6 sentences) unless asked for more detail."
        ),
    }
    index_msg = {
        "role": "system",
        "content": f"Scan history index (id | filename | date | verdict | detections | area):\n{history_index}",
    }
    messages = [system_msg, index_msg]
    if matched_details:
        messages.append({"role": "system", "content": f"Relevant scan detail:\n{matched_details}"})
    messages += history + [{"role": "user", "content": question}]
    return _chat(messages, max_tokens=450)
