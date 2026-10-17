"""
Symptom Classifier Engine
--------------------------
Uses a weighted scoring system:

  raw_score      = sum of weights for matched symptoms
  coverage_score = matched_symptoms / total_symptoms_in_condition  (penalises partial matches)
  final_score    = raw_score * coverage_score

Triage escalation:
  1. If ANY red-flag symptom is present → emergency (overrides everything)
  2. Special case: neck_stiffness + fever together → emergency (meningitis suspicion)
  3. Otherwise use the top-matched condition's triage level
"""

from knowledge_base import CONDITIONS, RED_FLAG_SYMPTOMS, SYMPTOM_CATALOGUE


def classify(user_symptoms: list[str]) -> dict:
    """
    Parameters
    ----------
    user_symptoms : list of symptom keys from SYMPTOM_CATALOGUE

    Returns
    -------
    dict with keys:
        triage          : "self_care" | "see_doctor" | "emergency"
        triage_label    : Human-readable label
        triage_color    : CSS color class name
        top_conditions  : list of top-3 matched condition dicts
        red_flags       : list of red-flag symptom labels detected
        matched_count   : how many symptoms were matched across all conditions
        disclaimer      : legal disclaimer string
    """
    user_set = set(user_symptoms)

    # --- 1. Red-flag check ---
    red_flags_found = user_set & RED_FLAG_SYMPTOMS
    # Special combo: neck stiffness + fever is always emergency
    if "neck_stiffness" in user_set and "fever" in user_set:
        red_flags_found.add("neck_stiffness")
        red_flags_found.add("fever")

    # --- 2. Score every condition ---
    scored = []
    for condition in CONDITIONS:
        condition_symptoms = condition["symptoms"]
        matched = {s: w for s, w in condition_symptoms.items() if s in user_set}
        if not matched:
            continue

        raw_score = sum(matched.values())
        coverage = len(matched) / len(condition_symptoms)
        final_score = raw_score * coverage

        # Boost emergency conditions when any of their symptoms match red flags
        if condition["triage"] == "emergency" and (user_set & set(condition_symptoms.keys())):
            final_score *= 1.4

        scored.append({
            "id": condition["id"],
            "name": condition["name"],
            "triage": condition["triage"],
            "description": condition["description"],
            "advice": condition["advice"],
            "icd_hint": condition["icd_hint"],
            "matched_symptoms": [
                SYMPTOM_CATALOGUE.get(s, s) for s in matched.keys()
            ],
            "score": round(final_score, 2),
            "match_percent": round(coverage * 100),
        })

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_conditions = scored[:5]  # keep top 5 for display

    # --- 3. Determine triage ---
    if red_flags_found:
        triage = "emergency"
    elif top_conditions:
        triage = top_conditions[0]["triage"]
    else:
        triage = "see_doctor"  # unknown combination → err on side of caution

    # If no match but user has a fair number of symptoms, suggest doctor
    if not top_conditions:
        triage = "see_doctor"

    # Triage metadata
    triage_meta = {
        "self_care": {
            "label": "Self-Care at Home",
            "color": "green",
            "icon": "🏠",
            "message": (
                "Your symptoms suggest a condition that can likely be managed at home. "
                "Rest, stay hydrated, and monitor for any worsening."
            ),
        },
        "see_doctor": {
            "label": "See a Doctor",
            "color": "orange",
            "icon": "🩺",
            "message": (
                "Your symptoms warrant a consultation with a healthcare professional. "
                "Book an appointment within the next 24–48 hours."
            ),
        },
        "emergency": {
            "label": "Seek Emergency Care",
            "color": "red",
            "icon": "🚨",
            "message": (
                "Your symptoms may indicate a serious or life-threatening condition. "
                "Go to the nearest emergency room or call emergency services (911/999/112) NOW."
            ),
        },
    }

    red_flag_labels = [SYMPTOM_CATALOGUE.get(s, s) for s in red_flags_found]

    return {
        "triage": triage,
        "triage_label": triage_meta[triage]["label"],
        "triage_color": triage_meta[triage]["color"],
        "triage_icon": triage_meta[triage]["icon"],
        "triage_message": triage_meta[triage]["message"],
        "top_conditions": top_conditions[:3],
        "red_flags": red_flag_labels,
        "matched_count": len(user_set),
        "disclaimer": (
            "⚠️ This tool is for informational purposes only and does not constitute "
            "medical advice. Always consult a qualified healthcare professional for "
            "diagnosis and treatment."
        ),
    }
