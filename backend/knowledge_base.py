"""
Symptom Checker Knowledge Base
--------------------------------
Each condition entry contains:
  - name          : Display name
  - symptoms      : dict of symptom_key -> weight (1-10, higher = more diagnostic)
  - triage        : default triage if this condition is top match
                    ("self_care" | "see_doctor" | "emergency")
  - description   : Brief patient-friendly description
  - advice        : Specific action advice
  - icd_hint      : Rough ICD-10 category (informational only)

Triage escalation rules (applied AFTER scoring):
  - Any RED-FLAG symptom present  → emergency
  - Score threshold logic per condition overrides default triage
"""

# ---------------------------------------------------------------------------
# Symptom catalogue (canonical keys used across the whole app)
# ---------------------------------------------------------------------------
SYMPTOM_CATALOGUE = {
    # --- General / Systemic ---
    "fever": "Fever (temperature ≥ 38 °C / 100.4 °F)",
    "high_fever": "High fever (≥ 39.5 °C / 103 °F)",
    "chills": "Chills or shivering",
    "fatigue": "Fatigue or extreme tiredness",
    "night_sweats": "Night sweats",
    "weight_loss": "Unexplained weight loss",
    "loss_of_appetite": "Loss of appetite",

    # --- Head / Neuro ---
    "headache": "Headache",
    "severe_headache": "Sudden or severe headache (worst of life)",
    "dizziness": "Dizziness or light-headedness",
    "confusion": "Confusion or altered mental state",
    "fainting": "Fainting or loss of consciousness",
    "seizure": "Seizure or convulsion",
    "vision_changes": "Vision changes or blurring",
    "facial_drooping": "Facial drooping or asymmetry",
    "speech_difficulty": "Difficulty speaking or slurred speech",
    "numbness": "Numbness or tingling in limbs",
    "neck_stiffness": "Neck stiffness",
    "sensitivity_to_light": "Sensitivity to light (photophobia)",

    # --- Respiratory ---
    "cough": "Cough",
    "dry_cough": "Dry cough",
    "productive_cough": "Cough with mucus/phlegm",
    "sore_throat": "Sore throat",
    "runny_nose": "Runny or stuffy nose",
    "sneezing": "Sneezing",
    "shortness_of_breath": "Shortness of breath",
    "rapid_breathing": "Rapid or laboured breathing",
    "wheezing": "Wheezing",
    "chest_tightness": "Chest tightness",
    "loss_of_smell": "Loss of smell (anosmia)",
    "loss_of_taste": "Loss of taste (ageusia)",
    "coughing_blood": "Coughing up blood",

    # --- Cardiovascular ---
    "chest_pain": "Chest pain or pressure",
    "palpitations": "Heart palpitations or racing heart",
    "rapid_heart_rate": "Rapid heart rate",
    "irregular_heartbeat": "Irregular heartbeat",
    "leg_swelling": "Leg or ankle swelling",
    "calf_pain": "Calf pain or tenderness",
    "bluish_lips": "Bluish lips or fingertips (cyanosis)",

    # --- GI ---
    "nausea": "Nausea",
    "vomiting": "Vomiting",
    "diarrhea": "Diarrhoea",
    "blood_in_stool": "Blood in stool",
    "abdominal_pain": "Abdominal pain or cramps",
    "severe_abdominal_pain": "Severe or sudden abdominal pain",
    "bloating": "Bloating or gas",
    "constipation": "Constipation",
    "jaundice": "Yellowing of skin/eyes (jaundice)",
    "heartburn": "Heartburn or acid reflux",

    # --- Urinary ---
    "frequent_urination": "Frequent urination",
    "painful_urination": "Painful or burning urination",
    "blood_in_urine": "Blood in urine",
    "dark_urine": "Dark or cola-coloured urine",
    "reduced_urine": "Reduced urine output",

    # --- Musculoskeletal ---
    "joint_pain": "Joint pain or swelling",
    "muscle_aches": "Muscle aches or myalgia",
    "back_pain": "Back pain",
    "severe_back_pain": "Severe back pain radiating to leg",
    "stiff_joints": "Stiff joints (especially morning)",
    "swollen_joints": "Swollen or red joints",

    # --- Skin ---
    "rash": "Skin rash",
    "hives": "Hives or urticaria",
    "itching": "Itching or pruritus",
    "pale_skin": "Pale or ashen skin",
    "flushing": "Flushing or redness of face",
    "bruising": "Easy bruising",
    "non_blanching_rash": "Non-blanching spots or petechiae",

    # --- Eyes / ENT ---
    "red_eyes": "Red or pink eyes",
    "eye_discharge": "Eye discharge or crusting",
    "ear_pain": "Ear pain",
    "hearing_loss": "Hearing loss",

    # --- Mental / Psychological ---
    "anxiety": "Anxiety or panic",
    "depression": "Low mood or depression",
    "insomnia": "Insomnia or sleep disturbance",

    # --- Other ---
    "swollen_lymph_nodes": "Swollen lymph nodes",
    "excessive_thirst": "Excessive thirst",
    "blurred_vision": "Blurred vision",
    "cold_sweats": "Cold sweats",
    "weakness": "General weakness",
    "arm_weakness": "Arm or leg weakness (sudden)",
    "throat_swelling": "Throat swelling or difficulty swallowing",
    "severe_allergic_reaction": "Severe allergic reaction signs",
}

# ---------------------------------------------------------------------------
# Red-flag symptoms → always escalate to EMERGENCY
# ---------------------------------------------------------------------------
RED_FLAG_SYMPTOMS = {
    "severe_headache",
    "confusion",
    "fainting",
    "seizure",
    "facial_drooping",
    "speech_difficulty",
    "arm_weakness",
    "coughing_blood",
    "chest_pain",
    "bluish_lips",
    "rapid_breathing",
    "severe_abdominal_pain",
    "blood_in_stool",
    "non_blanching_rash",
    "reduced_urine",
    "throat_swelling",
    "severe_allergic_reaction",
    "high_fever",  # in adults; especially with stiff neck
    "neck_stiffness",  # combined with fever
}

# ---------------------------------------------------------------------------
# Conditions knowledge base
# ---------------------------------------------------------------------------
CONDITIONS = [
    {
        "id": "common_cold",
        "name": "Common Cold",
        "triage": "self_care",
        "description": "A viral infection of the upper respiratory tract, usually mild and self-limiting.",
        "advice": "Rest, stay hydrated, and use over-the-counter decongestants or pain relievers as needed. Symptoms typically resolve in 7–10 days.",
        "icd_hint": "J00",
        "symptoms": {
            "runny_nose": 9, "sneezing": 8, "sore_throat": 7, "cough": 6,
            "dry_cough": 5, "headache": 4, "fatigue": 4, "fever": 3,
            "loss_of_appetite": 2, "muscle_aches": 2,
        },
    },
    {
        "id": "influenza",
        "name": "Influenza (Flu)",
        "triage": "self_care",
        "description": "A contagious respiratory illness caused by influenza viruses, more severe than a cold.",
        "advice": "Rest and fluids are key. Antivirals (e.g., oseltamivir) are most effective within 48 h of onset. Seek care if symptoms worsen rapidly, you are elderly, pregnant, or immunocompromised.",
        "icd_hint": "J10",
        "symptoms": {
            "fever": 9, "chills": 8, "muscle_aches": 9, "fatigue": 8,
            "headache": 7, "dry_cough": 7, "sore_throat": 5,
            "runny_nose": 4, "loss_of_appetite": 5, "vomiting": 3,
        },
    },
    {
        "id": "covid19",
        "name": "COVID-19",
        "triage": "see_doctor",
        "description": "Infection caused by SARS-CoV-2. Ranges from mild to severe respiratory illness.",
        "advice": "Isolate immediately. Take an antigen/PCR test. Contact your healthcare provider, especially if you have shortness of breath, persistent chest pain, or confusion.",
        "icd_hint": "U07.1",
        "symptoms": {
            "fever": 8, "dry_cough": 9, "fatigue": 7, "loss_of_smell": 10,
            "loss_of_taste": 10, "shortness_of_breath": 8, "headache": 6,
            "sore_throat": 5, "muscle_aches": 6, "chills": 5,
            "chest_tightness": 6, "diarrhea": 4, "vomiting": 3,
        },
    },
    {
        "id": "strep_throat",
        "name": "Strep Throat",
        "triage": "see_doctor",
        "description": "Bacterial throat infection (Group A Streptococcus) requiring antibiotic treatment.",
        "advice": "See a doctor for a rapid strep test. If positive, a full course of antibiotics is needed to prevent complications like rheumatic fever.",
        "icd_hint": "J02.0",
        "symptoms": {
            "sore_throat": 10, "fever": 8, "swollen_lymph_nodes": 7,
            "headache": 5, "loss_of_appetite": 5, "nausea": 4,
            "rash": 3, "chills": 4,
        },
    },
    {
        "id": "pneumonia",
        "name": "Pneumonia",
        "triage": "see_doctor",
        "description": "Infection causing inflammation of the air sacs in one or both lungs.",
        "advice": "See a doctor promptly. Treatment depends on the cause (bacterial vs viral). Hospitalisation may be needed for severe cases.",
        "icd_hint": "J18",
        "symptoms": {
            "fever": 8, "productive_cough": 9, "shortness_of_breath": 8,
            "chest_pain": 7, "chills": 7, "fatigue": 6, "rapid_breathing": 7,
            "loss_of_appetite": 5, "nausea": 4,
        },
    },
    {
        "id": "asthma",
        "name": "Asthma",
        "triage": "see_doctor",
        "description": "Chronic condition causing airway inflammation and narrowing.",
        "advice": "Use your rescue inhaler. If symptoms do not improve within 20 minutes or worsen, seek emergency care immediately.",
        "icd_hint": "J45",
        "symptoms": {
            "wheezing": 10, "shortness_of_breath": 9, "chest_tightness": 8,
            "cough": 7, "dry_cough": 6, "rapid_breathing": 6,
        },
    },
    {
        "id": "heart_attack",
        "name": "Heart Attack (Myocardial Infarction)",
        "triage": "emergency",
        "description": "A life-threatening blockage of blood flow to the heart muscle.",
        "advice": "Call emergency services (911/112) IMMEDIATELY. Chew an aspirin (325 mg) if available and not allergic. Do not drive yourself.",
        "icd_hint": "I21",
        "symptoms": {
            "chest_pain": 10, "arm_weakness": 7, "shortness_of_breath": 8,
            "nausea": 6, "cold_sweats": 8, "fatigue": 6, "palpitations": 5,
            "dizziness": 5, "rapid_heart_rate": 5, "jaw_pain": 6,
        },
    },
    {
        "id": "stroke",
        "name": "Stroke",
        "triage": "emergency",
        "description": "A medical emergency where blood supply to part of the brain is cut off.",
        "advice": "Call emergency services NOW. Remember FAST: Face drooping, Arm weakness, Speech difficulty, Time to call 999/911. Every minute counts.",
        "icd_hint": "I63",
        "symptoms": {
            "facial_drooping": 10, "arm_weakness": 10, "speech_difficulty": 10,
            "severe_headache": 8, "confusion": 8, "vision_changes": 7,
            "numbness": 7, "dizziness": 5, "fainting": 5,
        },
    },
    {
        "id": "meningitis",
        "name": "Meningitis",
        "triage": "emergency",
        "description": "Inflammation of the membranes surrounding the brain and spinal cord — can be life-threatening.",
        "advice": "Go to the emergency room immediately. Bacterial meningitis is life-threatening and requires IV antibiotics urgently.",
        "icd_hint": "G03",
        "symptoms": {
            "severe_headache": 9, "neck_stiffness": 10, "high_fever": 9,
            "sensitivity_to_light": 8, "non_blanching_rash": 9,
            "confusion": 8, "nausea": 5, "vomiting": 5, "seizure": 7,
        },
    },
    {
        "id": "appendicitis",
        "name": "Appendicitis",
        "triage": "emergency",
        "description": "Inflammation of the appendix requiring urgent surgical evaluation.",
        "advice": "Go to the emergency room immediately. Do not eat, drink, or take pain relievers before being evaluated by a doctor.",
        "icd_hint": "K37",
        "symptoms": {
            "severe_abdominal_pain": 10, "fever": 7, "nausea": 7,
            "vomiting": 6, "loss_of_appetite": 7, "abdominal_pain": 8,
        },
    },
    {
        "id": "uti",
        "name": "Urinary Tract Infection (UTI)",
        "triage": "see_doctor",
        "description": "Bacterial infection of the urinary system, most commonly the bladder.",
        "advice": "See your doctor for a urine test and possible antibiotic prescription. Drink plenty of water. Cranberry juice may help.",
        "icd_hint": "N39.0",
        "symptoms": {
            "painful_urination": 10, "frequent_urination": 9, "blood_in_urine": 7,
            "abdominal_pain": 5, "fever": 4, "dark_urine": 5, "fatigue": 3,
        },
    },
    {
        "id": "diabetes_type2",
        "name": "Type 2 Diabetes (Possible)",
        "triage": "see_doctor",
        "description": "A condition where the body doesn't use insulin properly, leading to high blood sugar.",
        "advice": "Book a fasting blood glucose or HbA1c test with your doctor. Lifestyle changes (diet, exercise) are the first line of management.",
        "icd_hint": "E11",
        "symptoms": {
            "excessive_thirst": 10, "frequent_urination": 9, "fatigue": 7,
            "blurred_vision": 6, "weight_loss": 6, "slow_healing": 5,
            "numbness": 5, "loss_of_appetite": 3,
        },
    },
    {
        "id": "migraine",
        "name": "Migraine",
        "triage": "self_care",
        "description": "A neurological condition causing intense, recurring headaches often with nausea and light sensitivity.",
        "advice": "Rest in a dark, quiet room. Over-the-counter pain relievers (ibuprofen, aspirin) help if taken early. See a doctor if migraines are frequent or disabling.",
        "icd_hint": "G43",
        "symptoms": {
            "headache": 9, "nausea": 7, "vomiting": 5, "sensitivity_to_light": 8,
            "vision_changes": 6, "dizziness": 5, "fatigue": 4,
        },
    },
    {
        "id": "allergic_reaction",
        "name": "Allergic Reaction",
        "triage": "see_doctor",
        "description": "An immune response to an allergen, ranging from mild to severe (anaphylaxis).",
        "advice": "For mild reactions: antihistamines. If throat swelling, difficulty breathing, or collapse — use an EpiPen if available and call 911/999 immediately.",
        "icd_hint": "T78.4",
        "symptoms": {
            "hives": 9, "itching": 8, "rash": 7, "swollen_lymph_nodes": 4,
            "sneezing": 5, "runny_nose": 5, "red_eyes": 5,
            "throat_swelling": 9, "shortness_of_breath": 7,
            "severe_allergic_reaction": 10,
        },
    },
    {
        "id": "gerd",
        "name": "GERD / Acid Reflux",
        "triage": "self_care",
        "description": "Chronic acid reflux where stomach acid frequently flows back into the oesophagus.",
        "advice": "Avoid trigger foods (spicy, fatty, caffeine). Eat smaller meals, don't lie down after eating. OTC antacids or H2 blockers can help. See a doctor if symptoms persist.",
        "icd_hint": "K21",
        "symptoms": {
            "heartburn": 10, "chest_pain": 5, "nausea": 5,
            "bloating": 6, "sore_throat": 4, "cough": 3,
        },
    },
    {
        "id": "depression",
        "name": "Depression",
        "triage": "see_doctor",
        "description": "A mood disorder causing persistent sadness, loss of interest, and impaired daily functioning.",
        "advice": "Speak with a GP or mental health professional. Treatment includes therapy, medication, or both. If you have thoughts of self-harm, contact a crisis line immediately.",
        "icd_hint": "F32",
        "symptoms": {
            "depression": 10, "fatigue": 7, "insomnia": 7,
            "weight_loss": 5, "loss_of_appetite": 6,
            "anxiety": 5, "headache": 3,
        },
    },
    {
        "id": "anemia",
        "name": "Anaemia",
        "triage": "see_doctor",
        "description": "A condition where you lack enough healthy red blood cells to carry adequate oxygen.",
        "advice": "See a doctor for a blood test (CBC). Treatment depends on the cause — iron supplements, B12 injections, or treating the underlying condition.",
        "icd_hint": "D64",
        "symptoms": {
            "fatigue": 8, "pale_skin": 9, "shortness_of_breath": 7,
            "dizziness": 7, "weakness": 8, "rapid_heart_rate": 5,
            "cold_sweats": 4, "headache": 4,
        },
    },
    {
        "id": "gastroenteritis",
        "name": "Gastroenteritis (Stomach Flu)",
        "triage": "self_care",
        "description": "Inflammation of the stomach and intestines, usually caused by a viral or bacterial infection.",
        "advice": "Stay hydrated with oral rehydration salts. Rest and eat bland foods (BRAT diet). See a doctor if vomiting/diarrhoea persists > 48 h, or if you see blood.",
        "icd_hint": "A09",
        "symptoms": {
            "nausea": 8, "vomiting": 9, "diarrhea": 9, "abdominal_pain": 7,
            "fever": 5, "fatigue": 5, "loss_of_appetite": 6,
        },
    },
]
