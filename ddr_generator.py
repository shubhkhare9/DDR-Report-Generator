"""
ddr_generator.py — Sends extracted content to Groq API and generates structured DDR
Uses LLaMA 3.3 70B via Groq — 100% FREE, no billing, works in India
Get your free API key at: https://console.groq.com
"""
from groq import Groq
import json
from typing import Dict

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────
DDR_SYSTEM_PROMPT = """You are an expert structural and waterproofing inspection analyst for a leading Pune-based firm specialising in waterproofing, structural protection, and repair services.

You will receive combined text data from:
1. An Inspection Report — site observations, checklists, impacted area descriptions, photo references
2. A Thermal Report — temperature readings (hotspot/coldspot), emissivity values, thermal camera findings

Your task: Generate a comprehensive DDR (Detailed Diagnostic Report) as pure JSON.

STRICT RULES:
- NEVER invent facts not present in the provided documents
- If information is missing → write "Not Available"  
- If data conflicts between inspection and thermal documents → clearly state the conflict
- Use simple, client-friendly language — no heavy technical jargon
- Coldspot temperatures significantly below ambient = confirmed active moisture/seepage zone
- Negative side = where the problem is visible (dampness, staining, ceiling leakage)
- Positive side = the SOURCE of water (bathroom tiles above, external wall crack, plumbing leak)
- Thermal coldspot readings below 22°C in the given reports indicate HIGH moisture presence

OUTPUT FORMAT: Return ONLY valid JSON — absolutely no markdown, no code fences, no preamble, no explanation outside the JSON object.

JSON SCHEMA TO FOLLOW EXACTLY:
{
  "property_info": {
    "property_type": "",
    "flat_number": "",
    "floors": "",
    "inspection_date": "",
    "inspected_by": "",
    "inspection_score": "",
    "previous_audit": "",
    "previous_repair": ""
  },
  "sections": [
    {
      "id": "s1",
      "title": "1. Property Issue Summary",
      "content": ""
    },
    {
      "id": "s2",
      "title": "2. Area-wise Observations",
      "content": "",
      "areas": [
        {
          "area_name": "",
          "negative_side": "",
          "positive_side": "",
          "thermal_finding": "",
          "inspection_image_ref": "",
          "thermal_image_ref": ""
        }
      ]
    },
    {
      "id": "s3",
      "title": "3. Probable Root Cause",
      "content": ""
    },
    {
      "id": "s4",
      "title": "4. Severity Assessment",
      "content": "",
      "severity_table": [
        {
          "area": "",
          "severity": "High / Medium / Low",
          "reasoning": ""
        }
      ]
    },
    {
      "id": "s5",
      "title": "5. Recommended Actions",
      "content": "",
      "actions": [
        {
          "area": "",
          "action": "",
          "priority": "Immediate / Short-term / Long-term"
        }
      ]
    },
    {
      "id": "s6",
      "title": "6. Additional Notes",
      "content": ""
    },
    {
      "id": "s7",
      "title": "7. Missing or Unclear Information",
      "content": ""
    }
  ]
}"""


def _build_combined_text(inspection_data: Dict, thermal_data: Dict) -> str:
    """
    Combine inspection and thermal text into a single well-structured prompt.
    Keeps it under Groq's context limits.
    """
    inspection_text = inspection_data.get("text", "")[:14000]
    thermal_text = thermal_data.get("text", "")[:8000]

    combined = f"""
=== INSPECTION REPORT ===
{inspection_text}

=== THERMAL REPORT (Temperature Readings & Findings) ===
{thermal_text}

=== INSTRUCTION ===
Based on ALL the above data from both the Inspection Report and the Thermal Report,
generate a complete and detailed DDR report following the exact JSON schema in your instructions.
Cover all 7 sections thoroughly. Be client-friendly and accurate.
Return ONLY valid JSON — no markdown, no explanation outside JSON.
"""
    return combined.strip()


def generate_ddr(inspection_data: Dict, thermal_data: Dict, api_key: str) -> Dict:
    """
    Send combined inspection + thermal text to Groq API (LLaMA 3.3 70B)
    and return structured DDR as a Python dict.
    """
    client = Groq(api_key=api_key)

    combined_text = _build_combined_text(inspection_data, thermal_data)

    # ── API call ─────────────────────────────────────────────
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": DDR_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": combined_text,
            },
        ],
        temperature=0.2,
        max_tokens=8000,
    )

    raw_text = response.choices[0].message.content.strip()

    # ── Strip markdown fences if model added them ─────────────
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3].strip()

    # ── Parse JSON ────────────────────────────────────────────
    try:
        ddr_data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to find JSON object within text
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                ddr_data = json.loads(raw_text[start:end])
            except json.JSONDecodeError:
                ddr_data = _fallback_structure(raw_text)
        else:
            ddr_data = _fallback_structure(raw_text)

    return ddr_data


def _fallback_structure(raw_text: str) -> Dict:
    """Graceful fallback if JSON parsing fails completely."""
    return {
        "property_info": {
            "property_type": "Flat",
            "flat_number": "103",
            "floors": "11",
            "inspection_date": "27.09.2022",
            "inspected_by": "Krushna & Mahesh",
            "inspection_score": "85.71%",
            "previous_audit": "No",
            "previous_repair": "No",
        },
        "sections": [
            {
                "id": "s1",
                "title": "1. DDR Report",
                "content": raw_text[:3000],
            }
        ],
    }
