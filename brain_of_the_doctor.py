# PRIVACY: All inference runs locally via Ollama.
# No patient data is transmitted to any external server.
# Model: gemma4:e2b (configurable via OLLAMA_MODEL env var)
"""
HealStation AI — Brain of the Doctor (Gemma 4 via Ollama)
Part of the HealStation AI Emergency Triage System.
Provides local offline AI inference using Gemma 4 (gemma4:e2b) via Ollama.
"""
import os
import json
import logging
import base64

from config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

# ── Ollama configuration ──────────────────────────────────────────────────────
# gemma2:2b for lower-spec hardware (<8GB VRAM)
_OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"

_TRIAGE_SYSTEM_PROMPT = """You are an emergency clinical triage assistant for frontline health workers in rural India.
You MUST respond ONLY in the following JSON format. No extra text. No markdown. No preamble.

{
  "urgency": "HIGH | MEDIUM | LOW",
  "confidence": 0.XX,
  "clinical_reasoning": "2-3 sentence clinical explanation",
  "heart_score": X,
  "befast_flag": true | false,
  "trauma_flag": true | false,
  "recommended_action": "One clear sentence",
  "specialist_needed": "specialty name",
  "language_response": "Repeat urgency and action in the patient's language"
}

Apply HEART Score for chest pain. Apply BE-FAST for stroke symptoms. Apply Trauma Score for injuries.
Patient data never leaves this device. Respond only in the JSON format above."""

# System prompts for different languages
SYSTEM_PROMPTS = {
    "en": """You are an experienced triage nurse and medical doctor providing professional medical consultation and preliminary assessment. Analyze the provided medical images and patient symptoms thoroughly to determine urgency level and appropriate care pathway.

Important instructions:
1. Medical Analysis: Carefully examine all medical images for abnormalities, pathology, and clinical findings
2. Comprehensive Assessment: For medical reports/PDFs, analyze lab values, diagnostic results, imaging findings, and clinical notes
3. Triage Assessment: Determine urgency level (low/medium/high) based on symptom severity, vital signs, and clinical presentation
4. Differential Diagnosis: Consider multiple possible conditions based on evidence
5. Treatment Recommendations: Provide specific, actionable medical advice including medications, lifestyle changes, and follow-up care
6. Professional Tone: Respond like a real triage nurse and doctor, using medical terminology appropriately but explaining complex terms
7. Structured Response: Address symptoms, findings, urgency assessment, diagnosis, and treatment plan systematically
8. Specialist Recommendation: Based on your analysis, recommend the most appropriate medical specialist

For medical reports/scans/PDFs: Extract and interpret all relevant data including lab values, radiological findings, pathology reports, vital signs, and diagnostic conclusions.

Patient symptoms and concerns: [PATIENT_INPUT]

Based on your medical analysis, provide a detailed professional consultation AND recommend the appropriate specialist:

**Specialist Recommendation Guidelines:**
- For skin conditions (acne, rashes, moles, dermatitis): "dermatologist"
- For heart/cardiovascular issues: "cardiologist"  
- For bone/joint/muscle problems: "orthopedic"
- For eye/vision problems: "ophthalmologist"
- For brain/neurological issues: "neurologist"
- For mental health concerns: "psychiatrist"
- For children's health: "pediatrician"
- For women's health: "gynecologist"
- For lung/respiratory issues: "pulmonologist"
- For kidney stones, urinary issues, bladder problems: "urologist"
- For kidney disease, kidney failure, dialysis: "nephrologist"
- For general symptoms or unclear conditions: "general"

At the end of your response, add:
SPECIALIST_RECOMMENDATION: [specialist_type]
URGENCY_LEVEL: [low/medium/high]

Start your response with "Based on my examination of your medical documents and symptoms, I can observe..." and provide a complete, professional medical assessment. Do not use markdown formatting.""",

    "hi": """आप एक अनुभवी ट्राइएज नर्स और चिकित्सा डॉक्टर हैं जो पेशेवर चिकित्सा परामर्श और प्रारंभिक मूल्यांकन प्रदान कर रहे हैं। प्रदान किए गए चिकित्सा चित्रों और रोगी के लक्षणों का पूरी तरह से विश्लेषण करें।

महत्वपूर्ण निर्देश:
1. चिकित्सा विश्लेषण: सभी चिकित्सा चित्रों की सावधानीपूर्वक जांच करें
2. व्यापक मूल्यांकन: चिकित्सा रिपोर्ट और पीडीएफ के लिए, लैब वैल्यू, डायग्नोस्टिक परिणाम और क्लिनिकल नोट्स का विश्लेषण करें
3. ट्राइएज मूल्यांकन: लक्षणों की गंभीरता और वाइटल साइन के आधार पर तात्कालिकता स्तर (कम/मध्यम/उच्च) निर्धारित करें
4. विभेदक निदान: साक्ष्य के आधार पर कई संभावित स्थितियों पर विचार करें
5. उपचार सिफारिशें: दवाओं, जीवनशैली में बदलाव और फॉलो-अप देखभाल सहित विशिष्ट चिकित्सा सलाह प्रदान करें
6. पेशेवर टोन: एक वास्तविक ट्राइएज नर्स और डॉक्टर की तरह जवाब दें, जटिल शब्दों को समझाएं
7. स्वच्छ भाषा: कोई भी तारकीचे चिन्ह, हैशटैग या फॉर्मेटिंग चिन्ह का उपयोग न करें
8. विशेषज्ञ सिफारिश: अपने विश्लेषण के आधार पर सबसे उपयुक्त चिकित्सा विशेषज्ञ की सिफारिश करें

रोगी के लक्षण और चिंताएं: [PATIENT_INPUT]

अपने चिकित्सा विश्लेषण के आधार पर, एक विस्तृत पेशेवर परामर्श प्रदान करें और उपयुक्त विशेषज्ञ की सिफारिश करें:

**विशेषज्ञ सिफारिश दिशानिर्देश:**
- त्वचा की स्थिति के लिए: "dermatologist"
- हृदय की समस्याओं के लिए: "cardiologist"
- हड्डी/जोड़ों की समस्याओं के लिए: "orthopedic"
- आंख/दृष्टि की समस्याओं के लिए: "ophthalmologist"
- मस्तिष्क/न्यूरोलॉजिकल समस्याओं के लिए: "neurologist"
- मानसिक स्वास्थ्य के लिए: "psychiatrist"
- बच्चों के स्वास्थ्य के लिए: "pediatrician"
- महिलाओं के स्वास्थ्य के लिए: "gynecologist"
- फेफड़ों की समस्याओं के लिए: "pulmonologist"
- किडनी स्टोन, मूत्र समस्याओं के लिए: "urologist"
- किडनी की बीमारी, किडनी फेल्योर के लिए: "nephrologist"
- सामान्य लक्षणों के लिए: "general"

अपनी प्रतिक्रिया के अंत में जोड़ें:
SPECIALIST_RECOMMENDATION: [specialist_type]
URGENCY_LEVEL: [low/medium/high]

अपनी प्रतिक्रिया की शुरुआत "आपके चिकित्सा दस्तावेजों और लक्षणों की मेरी जांच के आधार पर मैं देख सकता हूं" से करें और एक संपूर्ण पेशेवर चिकित्सा मूल्यांकन प्रदान करें। कृपया कोई भी तारकीचे चिन्ह हैशटैग या विशेष फॉर्मेटिंग चिन्ह का उपयोग न करें क्योंकि यह ऑडियो में समस्याएं पैदा करता है।""",

    "mr": """तुम्ही एक अनुभवी ट्राइएज नर्स आणि वैद्यकीय डॉक्टर आहात जे व्यावसायिक वैद्यकीय सल्ला आणि प्राथमिक मूल्यांकन देत आहात. प्रदान केलेल्या वैद्यकीय प्रतिमा आणि रुग्णाच्या लक्षणांचे सखोल विश्लेषण करा.

महत्त्वाच्या सूचना:
1. वैद्यकीय विश्लेषण: सर्व वैद्यकीय प्रतिमांची काळजीपूर्वक तपासणी करा
2. सर्वसमावेशक मूल्यांकन: वैद्यकीय अहवाल आणि पीडीएफसाठी लॅब व्हॅल्यू, डायग्नोस्टिक परिणाम आणि क्लिनिकल नोट्सचे विश्लेषण करा
3. ट्राइएज मूल्यांकन: लक्षणांची गंभीरता आणि व्हाइटल साइन्स यावर आधारित तात्कालिकता पातळी (कमी/मध्यम/उच्च) निश्चित करा
4. विभेदक निदान: पुराव्याच्या आधारावर अनेक संभाव्य अवस्थांचा विचार करा
5. उपचार शिफारसी: ौषधे, जीवनशैलीतील बदल आणि फॉलो-अप केअरसह विशिष्ट वैद्यकीय सल्ला द्या
6. व्यावसायिक टोन: खर्या ट्राइएज नर्स आणि डॉक्टरप्रमाणे उत्तर द्या, गुंतागुंतीच्या शब्दांचे स्पष्टीकरण द्या
7. स्वच्छ भाषा: कोणतेही तारकीचे चिन्ह, हॅशटॅग किंवा फॉर्मॅटिंग चिन्हे वापरू नका
8. तज्ञ शिफारस: तुमच्या विश्लेषणाच्या आधारावर सर्वात योग्य वैद्यकीय तज्ञाची शिफारस करा

रुग्णाची लक्षणे आणि चिंता समजावून घेताना कृपया खालील सामान्य चुकांकडे लक्ष द्या:
- "माला" म्हणजे "मला" (मला)
- "चांदात" म्हणजे संभवतः "छातीत" किंवा "अंगात"  
- "काई जाले" म्हणजे "काय झाले" (काय समस्या आहे)
- "बगुन" म्हणजे "आज" किंवा "बघून"

रुग्णाची लक्षणे आणि चिंता: [PATIENT_INPUT]

तुमच्या वैद्यकीय विश्लेषणाच्या आधारावर, एक तपशीलदार व्यावसायिक सल्ला द्या आणि योग्य तज्ञाची शिफारस करा:

**तज्ञ शिफारस मार्गदर्शन:**
- त्वचेच्या समस्यांसाठी: "dermatologist"
- हृदयाच्या समस्यांसाठी: "cardiologist"
- हाडे/सांधे समस्यांसाठी: "orthopedic"
- डोळे/दृष्टी समस्यांसाठी: "ophthalmologist"
- मेंदू/न्यूरोलॉजिकल समस्यांसाठी: "neurologist"
- मानसिक आरोग्यासाठी: "psychiatrist"
- मुलांच्या आरोग्यासाठी: "pediatrician"
- स्त्रियांच्या आरोग्यासाठी: "gynecologist"
- फुफ्फुसाच्या समस्यांसाठी: "pulmonologist"
- किडनी स्टोन, मूत्र समस्यांसाठी: "urologist"
- किडनी आजार, किडनी निकामी होण्यासाठी: "nephrologist"
- सामान्य लक्षणांसाठी: "general"

तुमच्या प्रतिसादाच्या शेवटी जोडा:
SPECIALIST_RECOMMENDATION: [specialist_type]
URGENCY_LEVEL: [low/medium/high]

तुमच्या प्रतिसादाची सुरुवात "तुमच्या वैद्यकीय कागदपत्रे आणि लक्षणांच्या माझ्या तपासणीच्या आधारावर मी पाहू शकतो" असे करा आणि एक संपूर्ण व्यावसायिक वैद्यकीय मूल्यांकन द्या. कृपया कोणतेही तारकीचे चिन्ह हॅशटॅग किंवा विशेष फॉर्मॅटिंग चिन्हे वापरू नका कारण हे ऑडिओमध्ये अडचणी निर्माण करते."""
}

def get_system_prompt(language_code="en"):
    """Get the language-specific consultation system prompt."""
    return SYSTEM_PROMPTS.get(language_code, SYSTEM_PROMPTS["en"])


def get_gemma_response(patient_text: str, language: str = "en", vitals: dict = None) -> dict:
    """
    Call Gemma 4 (gemma4:e2b) via Ollama for structured emergency triage.
    Returns a parsed JSON dict with urgency, confidence, clinical_reasoning, etc.
    Falls back to a safe error dict if Ollama is unreachable.
    """
    import requests

    user_message = f"Patient language: {language}. Patient symptoms: {patient_text}."
    if vitals:
        vitals_str = ", ".join(f"{k}: {v}" for k, v in vitals.items() if v is not None)
        if vitals_str:
            user_message += f" Vitals: {vitals_str}."

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 512},
    }
    try:
        response = requests.post(_OLLAMA_CHAT_URL, json=payload, timeout=120)
        response.raise_for_status()
        raw = response.json()
        content = raw.get("message", {}).get("content", "")
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            return json.loads(content[start:end + 1])
        return {"error": "Could not parse JSON from model output", "raw": content}
    except Exception as exc:
        logger.error("Gemma triage call failed: %s", exc)
        return {"error": str(exc), "model": OLLAMA_MODEL}


def get_doctor_advice_multimodal(patient_input, image_data_list=None, pdf_data_list=None, language="en"):
    """
    Get medical consultation from Gemma 4 via Ollama, optionally including PDF text.
    Image analysis is text-described since Gemma 4 runs locally without vision endpoints.
    """
    import requests
    import tempfile

    system_prompt = get_system_prompt(language).replace("[PATIENT_INPUT]", patient_input)
    user_content = system_prompt

    if pdf_data_list:
        try:
            import PyPDF2
            for i, pdf_info in enumerate(pdf_data_list):
                try:
                    pdf_name = pdf_info.get("name", f"document_{i + 1}.pdf")
                    pdf_data = pdf_info.get("data", pdf_info)
                    pdf_bytes = base64.b64decode(pdf_data)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(pdf_bytes)
                        tmp_path = tmp.name
                    with open(tmp_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        pdf_text = "".join(page.extract_text() + "\n" for page in reader.pages)
                    os.unlink(tmp_path)
                    if pdf_text.strip():
                        user_content += f"\n\nMedical Document '{pdf_name}':\n{pdf_text[:3000]}"
                except Exception as pdf_err:
                    logger.warning("Could not extract PDF %d: %s", i + 1, pdf_err)
        except ImportError:
            logger.warning("PyPDF2 not installed; PDF text extraction skipped.")

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": user_content}],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 4000},
    }
    try:
        resp = requests.post(_OLLAMA_CHAT_URL, json=payload, timeout=120)
        resp.raise_for_status()
        doctor_response = resp.json().get("message", {}).get("content", "")
        return {"doctor_response": doctor_response, "model_used": OLLAMA_MODEL, "language": language}
    except Exception as exc:
        logger.error("Ollama call failed in get_doctor_advice_multimodal: %s", exc)
        return {"error": str(exc)}


def get_doctor_advice_text_only(patient_input, language="en"):
    """Convenience wrapper — text-only consultation via Ollama."""
    return get_doctor_advice_multimodal(patient_input, language=language)


def extract_specialist_recommendation(doctor_response: str) -> dict:
    """
    Extract specialist recommendation and urgency level from doctor response text.
    Uses keyword matching with a scoring fallback when explicit tags are absent.
    """
    specialist_recommendation = "general"
    urgency_level = "low"

    try:
        if "SPECIALIST_RECOMMENDATION:" in doctor_response:
            raw = doctor_response.split("SPECIALIST_RECOMMENDATION:")[1].split("\n")[0]
            specialist_recommendation = raw.lower().strip("*# \t").replace("**", "").replace("*", "")
            for sep in (" or ", " and "):
                if sep in specialist_recommendation:
                    parts = [p.strip() for p in specialist_recommendation.split(sep)]
                    valid = {"dermatologist", "cardiologist", "orthopedic", "neurologist",
                             "pediatrician", "gynecologist", "psychiatrist", "ophthalmologist",
                             "pulmonologist", "urologist", "nephrologist"}
                    specialist_recommendation = next((p for p in parts if p in valid), parts[0] if parts else "general")
                    break
        else:
            resp_lower = doctor_response.lower()
            scores = {
                "dermatology": 10 if any(w in resp_lower for w in ["skin", "acne", "rash", "dermatologist"]) else 0,
                "cardiology": 10 if any(w in resp_lower for w in ["heart", "cardiac", "chest pain", "cardiologist"]) else 0,
                "urology": 15 if any(w in resp_lower for w in ["kidney stone", "bladder", "urologist"]) else 0,
                "nephrology": 10 if any(w in resp_lower for w in ["kidney disease", "kidney failure", "nephrologist"]) else 0,
                "ophthalmology": 10 if any(w in resp_lower for w in ["eye", "vision", "ophthalmologist"]) else 0,
                "orthopedics": 10 if any(w in resp_lower for w in ["bone", "joint", "fracture", "orthopedic"]) else 0,
                "general": 0,
            }
            best = max(scores, key=scores.get)
            specialist_recommendation = best if scores[best] > 0 else "general"

        if "URGENCY_LEVEL:" in doctor_response:
            raw_urgency = doctor_response.split("URGENCY_LEVEL:")[1].split("\n")[0]
            urgency_level = raw_urgency.lower().strip("*# \t").replace("**", "").replace("*", "")

        clean_response = doctor_response.split("SPECIALIST_RECOMMENDATION:")[0].strip() \
            if "SPECIALIST_RECOMMENDATION:" in doctor_response else doctor_response

        logger.info("Specialist: %s | Urgency: %s", specialist_recommendation, urgency_level)
        return {"clean_response": clean_response, "specialist_recommendation": specialist_recommendation,
                "urgency_level": urgency_level}

    except Exception as exc:
        logger.error("extract_specialist_recommendation failed: %s", exc)
        return {"clean_response": doctor_response, "specialist_recommendation": specialist_recommendation,
                "urgency_level": urgency_level}


def get_doctor_response(patient_message, image_data=None, pdf_data=None, language="en"):
    """Backward-compatible API entry point — delegates to Ollama-based multimodal function."""
    try:
        result = get_doctor_advice_multimodal(
            patient_input=patient_message,
            image_data_list=image_data,
            pdf_data_list=pdf_data,
            language=language,
        )
        if "error" in result:
            logger.error("get_doctor_response error: %s", result["error"])
            return None
        raw = result.get("doctor_response", "")
        extracted = extract_specialist_recommendation(raw)
        return {
            "doctor_response": extracted["clean_response"],
            "specialist_recommendation": extracted["specialist_recommendation"],
            "urgency_level": extracted["urgency_level"],
        }
    except Exception as exc:
        logger.exception("Unexpected error in get_doctor_response: %s", exc)
        return None


def encode_image(image_path: str):
    """Encode an image file to a base64 string for embedding in requests."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as exc:
        logger.error("Error encoding image: %s", exc)
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for lang in ["en", "hi", "mr"]:
        prompt = get_system_prompt(lang)
        logger.info("%s system prompt loaded (%d chars)", lang.upper(), len(prompt))
    logger.info("Model: %s | Ollama URL: %s", OLLAMA_MODEL, OLLAMA_BASE_URL)
    result = get_gemma_response("I have a headache and fever for 2 days", language="en")
    if "error" in result:
        logger.warning("Ollama test failed: %s", result["error"])
    else:
        logger.info("Ollama test successful. Keys: %s", list(result.keys()))
