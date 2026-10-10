"""
Emergency Triage Constants
=========================
Keywords, scoring weights, triage levels, and configuration for emergency detection.
"""

from typing import Dict, List, Any

# =============================================================================
# TRIAGE LEVELS (ESI-like 5-level system)
# =============================================================================

TRIAGE_LEVELS: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "critical",
        "display_name": "CRITICAL",
        "display_name_hindi": "गंभीर",
        "display_name_marathi": "गंभीर",
        "color": "#DC2626",  # Red
        "bg_color": "#FEE2E2",
        "description": "Immediate life-threatening condition",
        "description_hindi": "तत्काल जीवन-घातक स्थिति",
        "action": "CALL 108 IMMEDIATELY",
        "action_hindi": "तुरंत 108 पर कॉल करें",
        "action_marathi": "लगेच 108 वर कॉल करा",
        "time_to_care": "Immediate",
        "max_wait_minutes": 0,
        "call_108": True,
        "icon": "🚨",
        "pulse_animation": True
    },
    2: {
        "name": "emergency",
        "display_name": "EMERGENCY",
        "display_name_hindi": "आपातकाल",
        "display_name_marathi": "आणीबाणी",
        "color": "#EA580C",  # Orange
        "bg_color": "#FFEDD5",
        "description": "High risk, needs immediate attention",
        "description_hindi": "उच्च जोखिम, तत्काल ध्यान आवश्यक",
        "action": "Go to Emergency Room NOW",
        "action_hindi": "अभी इमरजेंसी रूम जाएं",
        "action_marathi": "आत्ताच इमर्जन्सी रूममध्ये जा",
        "time_to_care": "Within 10 minutes",
        "max_wait_minutes": 10,
        "call_108": True,
        "icon": "⚠️",
        "pulse_animation": True
    },
    3: {
        "name": "urgent",
        "display_name": "URGENT",
        "display_name_hindi": "तत्काल",
        "display_name_marathi": "तातडीचे",
        "color": "#FACC15",  # Yellow
        "bg_color": "#FEF9C3",
        "description": "Needs prompt medical attention",
        "description_hindi": "शीघ्र चिकित्सा ध्यान आवश्यक",
        "action": "Seek care within 1-2 hours",
        "action_hindi": "1-2 घंटे में देखभाल लें",
        "action_marathi": "1-2 तासात काळजी घ्या",
        "time_to_care": "Within 1-2 hours",
        "max_wait_minutes": 120,
        "call_108": False,
        "icon": "⏰",
        "pulse_animation": False
    },
    4: {
        "name": "standard",
        "display_name": "STANDARD",
        "display_name_hindi": "सामान्य",
        "display_name_marathi": "सामान्य",
        "color": "#22C55E",  # Green
        "bg_color": "#DCFCE7",
        "description": "Can be seen within 24 hours",
        "description_hindi": "24 घंटे में देखा जा सकता है",
        "action": "Schedule appointment",
        "action_hindi": "अपॉइंटमेंट शेड्यूल करें",
        "action_marathi": "भेटीचे वेळापत्रक करा",
        "time_to_care": "Within 24 hours",
        "max_wait_minutes": 1440,
        "call_108": False,
        "icon": "✅",
        "pulse_animation": False
    },
    5: {
        "name": "self_care",
        "display_name": "SELF-CARE",
        "display_name_hindi": "स्वयं-देखभाल",
        "display_name_marathi": "स्वत:ची काळजी",
        "color": "#3B82F6",  # Blue
        "bg_color": "#DBEAFE",
        "description": "Home care appropriate",
        "description_hindi": "घर पर देखभाल उचित",
        "action": "Home care with monitoring",
        "action_hindi": "निगरानी के साथ घर पर देखभाल",
        "action_marathi": "देखरेखीसह घरी काळजी",
        "time_to_care": "When convenient",
        "max_wait_minutes": 10080,  # 7 days
        "call_108": False,
        "icon": "ℹ️",
        "pulse_animation": False
    }
}

# =============================================================================
# EMERGENCY KEYWORDS (Keyword-based detection - works even if AI fails)
# =============================================================================

# LEVEL 1 - CRITICAL: Immediate life-threatening
CRITICAL_KEYWORDS: List[str] = [
    # Cardiac arrest / Heart attack
    "cardiac arrest", "heart stopped", "not breathing", "no pulse",
    "heart attack", "severe chest pain", "crushing chest pain",
    
    # Stroke
    "stroke", "face drooping", "face droop", "can't move arm",
    "slurred speech", "sudden confusion", "worst headache of my life",
    
    # Respiratory failure
    "can't breathe", "cannot breathe", "stopped breathing",
    "choking", "drowning", "suffocating", "turning blue", "blue lips",
    
    # Severe bleeding / Trauma
    "severe bleeding", "won't stop bleeding", "massive blood loss",
    "major accident", "severe trauma", "head injury unconscious",
    
    # Unconsciousness
    "unconscious", "not responding", "won't wake up", "collapsed",
    "passed out", "fainted and not waking",
    
    # Allergic reaction
    "anaphylaxis", "throat closing", "severe allergic reaction",
    "can't swallow", "face swelling",
    
    # Poisoning / Overdose
    "overdose", "poison", "poisoning", "suicide attempt",
    
    # Hindi keywords
    "सांस नहीं ले पा रहा", "बेहोश", "दिल का दौरा", "खून नहीं रुक रहा",
    "गला बंद हो रहा", "सांस रुक गई", "सांस फूलना", "सांस फूल रही", "दम घुट रहा",
    "बेहोशी", "अत्यधिक रक्तस्राव", "सांस बंद", "अटैक",
    
    # Marathi keywords
    "श्वास घेता येत नाही", "बेशुद्ध", "हृदयविकाराचा झटका", "श्वास कोंडणे", "दम लागतोय",
    "रक्तस्राव", "श्वास बंद", "अटॅक", "बेशुद्धावस्था"
]

# LEVEL 2 - EMERGENCY: High risk, needs immediate attention
EMERGENCY_KEYWORDS: List[str] = [
    # Cardiac concerns (not yet critical)
    "chest pain", "chest tightness", "chest pressure", "heart pain", "pain in heart",
    "heart racing", "palpitations severe", "arm pain with chest",
    "jaw pain with chest", "sweating with chest pain",
    
    # Neurological
    "sudden severe headache", "thunderclap headache",
    "vision loss sudden", "can't see", "double vision sudden",
    "weakness one side", "numbness one side", "confusion sudden",
    "seizure", "convulsion", "fitting",
    
    # Respiratory
    "difficulty breathing", "shortness of breath severe", "breathlessness",
    "breathing fast", "gasping", "wheezing severe",
    "asthma attack severe", "cannot catch breath",
    
    # Bleeding
    "bleeding heavily", "blood in stool large amount",
    "vomiting blood", "coughing blood",
    
    # Trauma
    "head injury", "car accident", "fall from height",
    "broken bone visible", "deformity after injury",
    
    # Abdominal
    "severe abdominal pain", "stomach pain unbearable",
    "rigid abdomen", "abdominal swelling sudden",
    
    # Pediatric
    "child not responding", "baby not breathing well",
    "high fever in infant", "newborn emergency",
    
    # Obstetric
    "heavy bleeding pregnancy", "labor complications",
    "water broke early", "baby not moving",
    
    # Hindi
    "सीने में दर्द", "सांस लेने में तकलीफ", "तेज बुखार बच्चे को", "दिल में दर्द",
    "सांस फूलना", "सांस फूल रही", "चक्कर आना", "दर्द दिल में", "छाती में दर्द",
    "सांस की कमी", "घबराहट", "पसीना और दर्द",
    
    # Marathi
    "छातीत दुखणे", "श्वास घेण्यास त्रास", "हृदयात वेदना", "दम लागतो",
    "चक्कर येणे", "हृदय वेदना", "श्वास घेण्यास अडचण", "छातीवर दडपण"
]

# =============================================================================
# TOXIN / POISON FAST-LANE KEYWORDS
# =============================================================================

TOXIN_FAST_LANE_KEYWORDS: Dict[str, List[str]] = {
    "ingestion": [
        "overdose", "too many pills", "took too much", "swallowed bleach", "drank bleach",
        "bleach ingestion", "ingested bleach",
        "drank detergent", "household cleaner", "drain cleaner", "toilet cleaner",
        "pesticide", "rat poison", "poison", "poisoning", "mushroom poisoning",
        "contaminated food", "spoiled food", "food poisoning", "chemical ingestion",
        "medication overdose", "pill overdose", "drug overdose", "alcohol poisoning",
        # Hindi
        "जहर", "ज़हर", "विष", "विषाक्त", "पॉइज़न", "पॉइजन",
        "कीटनाशक", "चूहा मार दवा", "रैट पॉइज़न", "रैट पॉइजन",
        "ब्लीच पी", "ब्लीच पी लिया", "ब्लीच निगला", "ब्लीच सेवन", "ब्लीच का सेवन",
        "डिटर्जेंट पी", "दवा ज्यादा", "ज्यादा गोलियां",
        "ओवरडोज", "अल्कोहल पॉइजनिंग", "फूड पॉइजनिंग",
        # Marathi
        "जहर", "विष", "विषबाधा", "पॉइझन", "पॉइजन",
        "कीटकनाशक", "उंदीर मारण्याची औषध", "रॅट पॉइझन",
        "ब्लीच पिले", "ब्लीच गिळले", "ब्लीच सेवन", "ब्लीचचे सेवन",
        "डिटर्जेंट पिले", "औषध जास्त", "जास्त गोळ्या",
        "ओव्हरडोस", "अन्न विषबाधा",
    ],
    "exposure": [
        "chemical exposure", "chemical burn", "skin exposure", "eyes exposed",
        "cleaner splash", "bleach splash", "pesticide exposure", "toxic exposure",
        "gas exposure", "gas inhalation", "carbon monoxide", "smoke inhalation",
        "fumes", "vapors", "insecticide", "fertilizer exposure",
        # Hindi
        "रसायन संपर्क", "केमिकल लग गया", "रासायनिक जलन", "केमिकल बर्न",
        "आंख में केमिकल", "त्वचा पर केमिकल", "गैस के संपर्क", "धुआं", "धुएं",
        "फ्यूम्स", "वाष्प", "कीटनाशक संपर्क", "विषाक्त संपर्क",
        # Marathi
        "रसायन संपर्क", "केमिकल लागले", "रासायनिक भाज", "केमिकल बर्न",
        "डोळ्यात केमिकल", "त्वचेवर केमिकल", "गॅसचा संपर्क", "धूर", "वाफ",
        "विषारी संपर्क", "कीटकनाशक संपर्क",
    ],
    "inhalation": [
        "gas leak", "carbon monoxide", "carbon monoxide poisoning", "natural gas",
        "fumes", "vapors", "inhaled chemicals", "breathing chemicals",
        # Hindi
        "गैस लीक", "गैस रिसाव", "कार्बन मोनोऑक्साइड", "जहरीली गैस",
        "धुआं सांस में", "धुआँ सांस में", "रसायन सांस में", "गैस इनहेल",
        # Marathi
        "गॅस गळती", "गॅस लीक", "कार्बन मोनॉक्साइड", "विषारी वायू",
        "धूर श्वासात", "रसायन श्वासात", "गॅस इनहेल", "वाफ श्वासात",
    ],
}

# LEVEL 3 - URGENT: Needs prompt attention
URGENT_KEYWORDS: List[str] = [
    # Moderate pain
    "severe pain", "pain score 8", "pain score 9", "unbearable pain",
    "moderate chest discomfort", "chest discomfort",
    
    # Fever
    "high fever", "fever 103", "fever 104", "fever 39", "fever 40",
    "fever with rash", "fever with stiff neck",
    
    # Infection signs
    "infection spreading", "red streaks", "pus", "abscess",
    "wound infected", "swollen lymph nodes",
    
    # Dehydration
    "severe dehydration", "not urinating", "very thirsty",
    "sunken eyes", "dry mouth extreme",
    
    # Mental health
    "suicidal thoughts", "self harm", "panic attack severe",
    "psychotic symptoms", "hallucinations",
    
    # Injuries
    "possible fracture", "can't bear weight", "joint swelling severe",
    "deep cut", "needs stitches",
    
    # GI issues
    "severe vomiting", "can't keep water down",
    "diarrhea with blood", "severe diarrhea",
    
    # Eye
    "eye injury", "chemical in eye", "sudden vision change",
    
    # Hindi
    "तेज बुखार", "उल्टी नहीं रुक रही", "गंभीर दर्द",
    
    # Marathi
    "तीव्र ताप", "उलट्या थांबत नाहीत"
]

# =============================================================================
# HEART SCORE CONFIGURATION (Chest Pain Assessment)
# =============================================================================

HEART_SCORE_CONFIG = {
    "highly_suspicious_history": [
        "crushing", "squeezing", "pressure", "tightness",
        "radiating to arm", "radiating to jaw", "radiating to back",
        "with sweating", "with nausea", "with vomiting",
        "worse with exertion", "woke up from sleep",
        # Hindi
        "सीने में दबाव", "सीने में जकड़न", "बाएं हाथ में दर्द", "जबड़े में दर्द",
        "पीठ तक दर्द", "पसीना", "मतली", "उल्टी", "मेहनत से बढ़ता", "नींद से उठा",
        # Marathi
        "छातीत दडपण", "छातीत घट्टपणा", "डाव्या हातात वेदना", "जबड्यात वेदना",
        "पाठीत पसरते", "घाम", "मळमळ", "उलटी", "मेहनत केल्यावर वाढते", "झोपेतून उठवले"
    ],
    "moderately_suspicious_history": [
        "chest pain", "chest discomfort", "burning chest",
        "heaviness in chest", "dull ache",
        # Hindi
        "सीने में दर्द", "सीने में जलन", "सीने में भारीपन",
        # Marathi
        "छातीत दुखणे", "छातीत जळजळ", "छातीत जडपणा"
    ],
    "low_suspicious_history": [
        "sharp pain", "stabbing", "pinpoint pain",
        "worse with breathing", "worse with movement",
        "reproduced by pressing"
    ],
    "risk_factors": [
        "diabetes", "diabetic", "hypertension", "high blood pressure",
        "high cholesterol", "smoking", "smoker", "family history of heart",
        "previous heart attack", "coronary artery disease", "obesity",
        # Hindi
        "मधुमेह", "डायबिटीज", "उच्च रक्तचाप", "हाई ब्लड प्रेशर",
        "कोलेस्ट्रॉल", "धूम्रपान", "परिवार में दिल की बीमारी", "पहले हार्ट अटैक",
        "हृदय रोग", "मोटापा",
        # Marathi
        "मधुमेह", "डायबेटीस", "उच्च रक्तदाब", "हाय ब्लड प्रेशर",
        "कोलेस्ट्रॉल", "धूम्रपान", "कुटुंबात हृदयाचा आजार", "पूर्वी हार्ट अटॅक",
        "हृदय रोग", "लठ्ठपणा"
    ],
    "severity_indicators": [
        "severe", "worst", "unbearable", "10 out of 10",
        "can't tolerate", "excruciating",
        # Hindi
        "बहुत तेज", "सबसे ज्यादा", "असहनीय", "सह नहीं पा रहा",
        # Marathi
        "खूप तीव्र", "असह्य", "सहन होत नाही", "फार त्रास"
    ],
    "age_thresholds": {
        "high_risk": 65,
        "moderate_risk": 45,
        "low_risk": 0
    }
}

# =============================================================================
# BE-FAST KEYWORDS (Stroke Assessment)
# =============================================================================

BEFAST_KEYWORDS = {
    "balance": [
        "balance problem", "loss of balance", "unsteady", "dizzy",
        "dizziness sudden", "vertigo sudden", "falling", "coordination problem",
        "can't walk straight", "stumbling",
        # Hindi
        "चक्कर", "अचानक चक्कर", "संतुलन बिगड़ा", "लड़खड़ाना", "सीधा चल नहीं पा रहा",
        # Marathi
        "चक्कर येणे", "अचानक चक्कर", "तोल गेला", "लडखडणे", "सरळ चालता येत नाही"
    ],
    "eyes": [
        "vision problem", "blurry vision sudden", "double vision",
        "vision loss", "can't see", "blind spot", "visual disturbance",
        # Hindi
        "धुंधला दिखना", "दोहरा दिखना", "दिखाई नहीं दे रहा", "दृष्टि चली गई",
        # Marathi
        "धुसर दिसणे", "दुहेरी दिसणे", "दिसत नाही", "दृष्टी कमी"
    ],
    "face": [
        "face droop", "face drooping", "facial weakness", "smile uneven",
        "one side of face", "face numb", "facial numbness", "drooping",
        # Hindi
        "चेहरा टेढ़ा", "चेहरा लटकना", "चेहरा सुन्न", "चेहरे का एक तरफ",
        # Marathi
        "चेहरा वाकडा", "चेहरा लटकणे", "चेहरा सुन्न", "चेहऱ्याचा एक भाग"
    ],
    "arm": [
        "arm weakness", "arm numb", "can't lift arm", "arm tingling",
        "arm weak", "one arm weak", "one side weak", "weakness one side",
        "can't grip", "dropping things", "can't lift my right arm", "can't lift my left arm",
        # Hindi
        "बांह कमजोर", "हाथ कमजोर", "हाथ सुन्न", "एक तरफ कमजोरी",
        "हाथ ऊपर नहीं उठा", "पकड़ नहीं",
        # Marathi
        "हात कमजोर", "हात सुन्न", "एक बाजू कमजोर", "हात वर उचलता येत नाही",
        "पकड नाही"
    ],
    "speech": [
        "slurred speech", "can't speak", "speech difficulty",
        "confused speech", "garbled words", "trouble speaking",
        "word finding difficulty", "aphasia", "speech is slurred",
        # Hindi
        "बोली अस्पष्ट", "बोल नहीं पा रहा", "बात करने में दिक्कत",
        "शब्द नहीं निकल रहे", "लड़खड़ाती बोली",
        # Marathi
        "बोली अस्पष्ट", "बोलता येत नाही", "बोलण्यात अडचण",
        "शब्द सापडत नाही", "अस्पष्ट बोलणे"
    ],
    "time_indicators": [
        "just started", "started suddenly", "happened suddenly",
        "came on fast", "within the hour", "just now",
        # Hindi
        "अभी-अभी", "अचानक", "अभी अभी", "बस शुरू हुआ",
        # Marathi
        "आत्ताच", "अचानक", "ताजेच", "एकदम"
    ]
}

# =============================================================================
# TRAUMA KEYWORDS
# =============================================================================

TRAUMA_KEYWORDS = {
    "mechanism_severe": [
        "car accident", "motorcycle accident", "high speed",
        "fall from height", "fell from", "pedestrian hit",
        "ejected from vehicle", "major trauma", "crushed",
        # Hindi
        "कार एक्सीडेंट", "गाड़ी दुर्घटना", "मोटरसाइकिल दुर्घटना",
        "ऊंचाई से गिरा", "ऊँचाई से गिरा", "पैदल को टक्कर", "वाहन से बाहर फेंका", "कुचल गया",
        # Marathi
        "कार अपघात", "गाडी अपघात", "मोटरसायकल अपघात",
        "उंचीवरून पडला", "पादचारीला धडक", "वाहनातून फेकला", "चिरडला"
    ],
    "bleeding": [
        "bleeding", "blood", "won't stop bleeding", "hemorrhage",
        "blood loss", "bleeding heavily", "soaked in blood",
        # Hindi
        "खून बह रहा", "खून नहीं रुक रहा", "अधिक रक्तस्राव", "बहुत खून",
        # Marathi
        "रक्तस्राव", "खून थांबत नाही", "खूप रक्त", "रक्त वाहत आहे"
    ],
    "consciousness": [
        "unconscious", "knocked out", "blacked out", "lost consciousness",
        "confused after", "doesn't remember", "amnesia",
        # Hindi
        "बेहोश", "होश नहीं", "होश में नहीं", "याद नहीं", "भ्रमित",
        # Marathi
        "बेशुद्ध", "होश नाही", "आठवत नाही", "गोंधळ", "शुद्ध हरपली"
    ],
    "injuries": [
        "broken bone", "fracture", "deformity", "bone sticking out",
        "open wound", "deep wound", "multiple injuries",
        "spinal injury", "neck injury", "back injury",
        # Hindi
        "हड्डी टूट", "फ्रैक्चर", "हड्डी बाहर", "गहरा घाव", "खुला घाव",
        "कई चोटें", "रीढ़ की चोट", "गर्दन की चोट", "पीठ की चोट",
        # Marathi
        "हाड मोडणे", "फ्रॅक्चर", "हाड बाहेर", "खोल जखम", "उघडी जखम",
        "अनेक जखमा", "कणा दुखापत", "मान दुखापत", "पाठीची दुखापत"
    ]
}

# =============================================================================
# VITAL SIGNS THRESHOLDS
# =============================================================================

VITAL_SIGNS_CRITICAL = {
    "heart_rate_low": 40,
    "heart_rate_high": 150,
    "systolic_bp_low": 80,
    "systolic_bp_high": 200,
    "diastolic_bp_high": 120,
    "oxygen_saturation_low": 88,
    "temperature_high": 40.5,  # Celsius
    "temperature_low": 35.0,
    "respiratory_rate_low": 8,
    "respiratory_rate_high": 30
}

VITAL_SIGNS_CONCERNING = {
    "heart_rate_low": 50,
    "heart_rate_high": 120,
    "systolic_bp_low": 90,
    "systolic_bp_high": 160,
    "diastolic_bp_high": 100,
    "oxygen_saturation_low": 92,
    "temperature_high": 39.0,
    "respiratory_rate_high": 24
}

# =============================================================================
# EMERGENCY NUMBERS (India)
# =============================================================================

EMERGENCY_NUMBERS = {
    "ambulance": "108",
    "emergency": "112",
    "police": "100",
    "fire": "101",
    "women_helpline": "1091",
    "child_helpline": "1098",
    "mental_health": "9152987821"  # NIMHANS helpline
}

# =============================================================================
# SPECIALIST MAPPING FOR EMERGENCIES
# =============================================================================

EMERGENCY_SPECIALIST_MAPPING = {
    "cardiac": ["Cardiologist", "Emergency Medicine", "Interventional Cardiologist"],
    "stroke": ["Neurologist", "Emergency Medicine", "Stroke Specialist"],
    "trauma": ["Trauma Surgeon", "Emergency Medicine", "Orthopedic Surgeon"],
    "respiratory": ["Pulmonologist", "Emergency Medicine", "Critical Care"],
    "pediatric": ["Pediatrician", "Pediatric Emergency Medicine"],
    "obstetric": ["Obstetrician", "Gynecologist", "Emergency Medicine"],
    "psychiatric": ["Psychiatrist", "Emergency Psychiatry"],
    "general": ["Emergency Medicine", "General Physician"]
}

# =============================================================================
# HOSPITAL CAPABILITY REQUIREMENTS BY EMERGENCY TYPE
# =============================================================================

HOSPITAL_REQUIREMENTS = {
    "cardiac": ["emergency_room", "cardiac_care", "icu", "24x7"],
    "stroke": ["emergency_room", "stroke_unit", "icu", "24x7"],
    "trauma": ["emergency_room", "trauma_center", "surgery", "icu", "24x7"],
    "respiratory": ["emergency_room", "icu", "24x7"],
    "general": ["emergency_room", "24x7"]
}

# =============================================================================
# FAIRNESS GROUP DEFINITIONS
# =============================================================================

FAIRNESS_AGE_GROUPS: List[Dict[str, Any]] = [
    {"label": "0-18", "min": 0, "max": 18},
    {"label": "19-65", "min": 19, "max": 65},
    {"label": "65+", "min": 66, "max": None},
]

FAIRNESS_GENDER_GROUPS: List[str] = ["male", "female", "other"]

FAIRNESS_LANGUAGE_GROUPS: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "es": "Spanish",
    "fr": "French",
    "zh": "Mandarin",
}
