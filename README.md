# 🏥 HealStation AI — Emergency Triage Assistant

> **Offline-first, multilingual clinical triage for frontline health workers in rural India**
> Powered by Gemma 4 (gemma4:e2b) · Runs entirely on-device · No internet required (specialThanks to Ollama)

[![Gemma 4](https://img.shields.io/badge/Gemma_4-gemma4:e2b-blue)](https://ollama.com/library/gemma4)
[![Ollama](https://img.shields.io/badge/Ollama-local_inference-green)](https://ollama.com)
[![Offline](https://img.shields.io/badge/Offline--First-yes-brightgreen)](.)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB)](https://react.dev)
[![License](https://img.shields.io/badge/License-Apache_2.0-green)](LICENSE)

---

## The Problem

India has fewer than 1 doctor per 1,500 people in rural areas. ASHA workers and frontline health workers
must make triage decisions daily — cardiac emergencies, strokes, trauma — often without specialist support
and with no reliable internet. Misdiagnosed cardiac events and delayed strokes cost thousands of lives every
year in regions where connectivity gaps make cloud-based AI impossible.

## The Solution

HealStation AI runs Gemma 4 locally via Ollama. ASHA workers and frontline health workers enter symptoms
in their own language — English, Hindi, or Marathi — and receive a structured clinical triage decision in
seconds. No internet. No patient data ever leaves the device.

## Why Gemma 4

Gemma 4 runs entirely on-device via Ollama. A health worker in rural Maharashtra with no internet
connectivity can open this app and receive a clinical triage decision in seconds. Patient data never
leaves their device — a critical requirement in healthcare. Cloud-only models like GPT-4 are impossible
in this context. Gemma 4's open weights and Apache license also mean this tool can be freely deployed
across India's public health system.

## Clinical Protocols

| Protocol | Use Case | Criteria |
|---|---|---|
| HEART Score | Chest pain / cardiac | History, ECG, Age, Risk factors, Troponin |
| BE-FAST | Stroke symptoms | Balance, Eyes, Face, Arms, Speech, Time |
| Trauma Score | Physical injuries | GCS, Respiratory Rate, Systolic BP |

## Architecture

```mermaid
flowchart LR
    User["Health Worker"] --> React["React UI\n(localhost:3000 in dev)"]
    React --> FastAPI["FastAPI\n(api.py :8001)"]
    FastAPI --> Gemma["Ollama\n(Gemma 4 E2B)"]
    FastAPI --> Triage["Emergency\nTriage Engine"]
    FastAPI --> STT["faster-whisper\n(Offline STT)"]
    FastAPI --> TTS["pyttsx3\n(Offline TTS)"]
    Gemma --> Output["Structured JSON\nTriage Result"]
    Triage --> Output
```

## Hardware Requirements

| Spec | Minimum | Recommended |
|---|---|---|
| RAM | 8 GB | 16 GB |
| VRAM | 4 GB | 8 GB |
| Model | gemma2:2b | gemma4:e2b |
| OS | Windows / macOS / Linux | Any |

---

## Quick Start

### 1. Install Ollama and pull the model
```bash
# Install Ollama from https://ollama.com
ollama serve
ollama pull gemma4:e2b
# Low-spec alternative: ollama pull gemma2:2b  (then set OLLAMA_MODEL=gemma2:2b in .env)
```

### 2. Clone and set up backend
```bash
git clone https://github.com/aj4344/gemma-guardians-HealstationAI.git
cd gemma-guardians-HealstationAI

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
# Linux only, for offline voice output: sudo apt install espeak-ng

copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

The offline speech-to-text model is downloaded once while online:
`python download_stt_model.py`.

### 3. Start the backend
```bash
python api.py
# Backend: http://127.0.0.1:8001
# Verify: GET /api/ollama-status → {"ollama":"connected","offline_ready":true}
```

### 4. Start the frontend
```bash
cd frontend
npm install
npm run dev
# Frontend: http://localhost:3000 (proxies /api to the backend on :8001)
```

### 5. Production: one offline process
```bash
cd frontend && npm ci && npm run build && cd ..
python api.py
# UI and API are both served on http://127.0.0.1:8001 — Node.js is not needed at runtime
```
See [Deployment](#-deployment) for the security settings to review first.

---

## Features

- ✅ Fully offline inference (Ollama + Gemma 4)
- ✅ Multilingual: English, Hindi, Marathi
- ✅ HEART Score, BE-FAST, Trauma Score protocols
- ✅ Structured JSON triage output with confidence score
- ✅ Offline hospital routing (static database)
- ✅ Local speech-to-text (faster-whisper, no network required)
- ✅ Offline TTS (pyttsx3, no network required)
- ✅ Ayushman Bharat eligibility checker
- ✅ No patient data ever transmitted externally

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/ollama-status` | Ollama + model health check |
| GET | `/api/stt-health` | faster-whisper STT status |
| POST | `/api/get-doctor-response` | Main triage consultation |
| POST | `/api/transcribe-audio` | Offline speech-to-text |
| POST | `/api/emergency-triage` | Emergency triage (HEART/BE-FAST/Trauma) |
| POST | `/api/emergency-triage/quick` | Keyword-only quick triage (`{"symptoms": "..."}`) |
| POST | `/api/emergency-hospitals` | Nearest hospital routing |
| POST | `/api/search-doctors` | Listed specialists near a location (static directory) |
| POST | `/api/search-doctors-by-city` | Listed specialists in a named city |
| GET | `/api/audio/{filename}` | Spoken response for a consultation (WAV) |

## Project Structure

```
gemma-guardians-HealstationAI/
├── api.py                     ← FastAPI backend (triage pipeline, Gemma 4 via Ollama)
├── config.py                  ← All settings (read from env / .env)
├── voice_of_the_patient.py    ← faster-whisper STT
├── voice_of_the_doctor.py     ← pyttsx3 TTS
├── brain_of_the_doctor.py     ← Standalone Gemma consultation CLI (not used by the API)
├── advanced_doctor_service.py ← Static specialist directory
├── requirements.txt / requirements-dev.txt
├── .env.example
├── emergency_triage/          ← HEART / BE-FAST / Trauma engine, guardrails' constants
├── doctor_search/             ← Directory search package
├── tests/                     ← pytest suite (python -m pytest)
├── scripts/                   ← Manual smoke tests against a live Ollama / microphone
└── frontend/
    └── src/
        ├── App.jsx
        └── components/ui/
            ├── EmergencyTriage.jsx
            ├── AyushmanBharatCard.jsx
            └── AboutSection.jsx
```

## Validated By

Clinical protocols (HEART Score, BE-FAST, Trauma Score) and triage logic were reviewed and validated
by Three practicing physicians(Doctors) before submission.

## Ollama Special Track

This project is eligible for the **Ollama Special Mention** track — all Gemma 4 inference runs
entirely via Ollama for local, offline deployment. No cloud API is required for any part of the
core triage flow.

## Verification Checklist

```bash
ollama list                              # shows gemma4:e2b
python api.py                            # starts without errors
curl http://127.0.0.1:8001/api/ollama-status   # {"offline_ready":true}
curl -X POST http://127.0.0.1:8001/api/emergency-triage \
  -H "Content-Type: application/json" \
  -d '{"symptoms":"chest pain","language":"en"}'
# open http://localhost:3000             # frontend loads (dev)
pip install -r requirements-dev.txt && python -m pytest   # backend test suite

```

## License

Apache 2.0 — free to deploy across India's public health system.

---

## Architecture

```mermaid
flowchart LR
    subgraph Frontend["React Frontend (Vite, :3000)"]
        UI["App.jsx + UI Components"]
        Upload["Voice / Text / Image / PDF Input"]
    end

    subgraph Backend["FastAPI Backend (Python, :8001)"]
        API["api.py Endpoints + triage pipeline"]
        STT["voice_of_the_patient.py (faster-whisper)"]
        TTS["voice_of_the_doctor.py (pyttsx3)"]
        Search["doctor_search/* (static database)"]
        Triage["emergency_triage/*"]
    end

    subgraph Local["Local Inference"]
        Ollama["Ollama (Gemma 4 E2B)"]
        Whisper["faster-whisper (offline STT)"]
    end

    UI --> Upload
    Upload --> API
    API --> STT
    API --> TTS
    API --> Search
    API --> Triage
    API --> Ollama
    STT --> Whisper
```

---

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- npm (or pnpm/yarn)
- Ollama (required for Gemma 4 inference)


---

## Installation

### **Step 1: Clone Repository**

```bash
git clone https://github.com/aj4344/gemma-guardians-HealstationAI.git

# Navigate into the project directory
cd gemma-guardians-HealstationAI
```

---

### **Step 2: Backend Setup (Python)**

#### **Option A: Windows**
```cmd
# Create virtual environment
py -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Upgrade pip
py -m pip install --upgrade pip

# Install dependencies
py -m pip install -r requirements.txt
```

#### **Option B: macOS/Linux**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Linux only:** offline voice output (pyttsx3) needs the system speech engine:
`sudo apt install espeak-ng`. Windows and macOS use their built-in voices.

---

### **Step 3: Configure Environment Variables**

#### **Copy the example file:**
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```





#### **Required offline settings:**

```env
# Ollama base URL (default for local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e2b

# Low-spec alternative: OLLAMA_MODEL=gemma2:2b
```

#### **Optional STT/TTS tuning:**

```env
# Enable offline TTS (pyttsx3). Outputs .wav files.
LOCAL_TTS_ENABLED=true

# Enable offline STT (faster-whisper)
ENABLE_LOCAL_STT=true
LOCAL_STT_MODEL_SIZE=small  # use "tiny" for fastest demos
LOCAL_STT_MODEL_PATH=
LOCAL_STT_DEVICE=cpu
LOCAL_STT_COMPUTE_TYPE=int8
LOCAL_STT_CPU_THREADS=0
LOCAL_STT_NUM_WORKERS=1
```

---

### **Step 4: Frontend Setup (React + Vite)**

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (choose one)
npm install          # Using npm (recommended)
# or
pnpm install         # Using pnpm (faster)
# or
yarn install         # Using yarn

# Return to project root
cd ..
```

---

## ▶️ Running the Application

### **Method 1: Manual Start (Recommended for Development)**

You need **TWO terminal windows** running simultaneously:

#### **Terminal 1️⃣ - Start Backend (Python/FastAPI)**

```bash
# Make sure virtual environment is activated
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Start FastAPI server
py api.py           # Windows
# or
python3 api.py      # macOS/Linux

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8001
# INFO:     Application startup complete.
```

**Backend will be accessible at:** `http://127.0.0.1:8001`

**Test backend:**
```bash
# In a new terminal
curl http://127.0.0.1:8001/api
# Should return: {"status":"healthy","message":"HealStation AI: Doctor Assistant API is running"}
```

#### **Terminal 2️⃣ - Start Frontend (React/Vite)**

```bash
# Navigate to frontend
cd frontend

# Start Vite dev server
npm run dev         # Using npm

# You should see:
# VITE v7.0.0  ready in XXX ms
# ➜  Local:   http://localhost:3000/
# ➜  Network: use --host to expose
```

**Frontend will be accessible at:** `http://localhost:3000`

**Open in browser:**
```
http://localhost:3000
```

---

### **Method 2: Optional Local Automation (User-Created)**

On Windows, `start_offline.bat` starts Ollama and the backend together. To serve the UI from the
same process, build it once first (`cd frontend && npm run build`).

---

## ✅ Verification Checklist

After starting both servers, verify everything works:

- [ ] **Backend Running**: Visit `http://127.0.0.1:8001/api` → `{"status":"healthy", ...}`
- [ ] **Frontend Running**: Visit `http://localhost:3000` → See app interface
- [ ] **API Connection**: Check browser console → No CORS errors
- [ ] **Ollama Status**: Visit `/api/ollama-status` → `{"offline_ready":true}`
- [ ] **Offline STT**: Try voice recording → faster-whisper transcribes locally
- [ ] **Offline Triage**: Click "Emergency Triage" → Results appear without network

---

## 🎯 First-Time Usage

### **Test the Application:**

1. **Select Language:** Choose English, Hindi (हिंदी), or Marathi (मराठी)
2. **Accept Disclaimer:** Read and accept the medical disclaimer
3. **Record Symptoms:** Click microphone and describe symptoms (or type)
4. **Upload Files (Optional):** Add medical images/PDFs
5. **Get Diagnosis:** Click "Get Triage Assessment"
6. **View Results:** See AI analysis with urgency level
7. **Find Doctors:** Click "Find Nearby Doctors & Hospitals"
8. **Check Ayushman Bharat:** Test health insurance eligibility

### **Sample Test Data:**

**Test Case 1: High Urgency**
```
Symptoms: "Severe chest pain, shortness of breath, sweating, I'm 52 years old"
Expected: HIGH urgency banner, Cardiologist recommendation
```

**Test Case 2: Medium Urgency**
```
Symptoms: "Persistent fever for 3 days, cough, body aches"
Expected: MEDIUM urgency, General Physician recommendation
```

**Test Case 3: Low Urgency**
```
Symptoms: "Minor skin rash on arm, no pain, started yesterday"
Expected: LOW urgency, Dermatologist recommendation
```

---

## 🛑 Stopping the Application

### **Method 1: Terminal**
- Press `Ctrl+C` in each terminal window
- Type `deactivate` to exit Python virtual environment

### **Method 2: Task Manager (Windows)**
```cmd
# Kill backend
taskkill /F /IM python.exe

# Kill frontend
taskkill /F /IM node.exe
```

### **Method 3: Activity Monitor (Mac)**
- Open Activity Monitor
- Search for "python" and "node"
- Force quit both processes

---

## 🔧 Development Commands

### **Backend Commands**
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix

# Install new package (then add it to requirements.txt by hand)
pip install package-name

# Run with auto-reload
uvicorn api:app --reload --port 8001

# Run the test suite
pip install -r requirements-dev.txt
python -m pytest

# Check Python version
py --version
```

### **Frontend Commands**
```bash
cd frontend

# Development server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Install new package
npm install package-name
```

---

## 📦 Project Structure

```
gemma-guardians-HealstationAI/
│
├── api.py                       # FastAPI backend (port 8001) + triage pipeline
├── config.py                    # Every setting, read from env / .env
├── voice_of_the_patient.py      # Speech-to-text (faster-whisper, offline)
├── voice_of_the_doctor.py       # Text-to-speech (pyttsx3, offline)
├── brain_of_the_doctor.py       # Standalone Gemma consultation CLI (not used by the API)
├── advanced_doctor_service.py   # Static specialist directory (unverified listings)
├── doctor_search/               # Directory search package used by the API
├── emergency_triage/            # HEART / BE-FAST / Trauma scoring, hospital routing
│
├── tests/                       # pytest suite: python -m pytest
├── scripts/                     # Manual checks against live Ollama / audio files
├── check_offline_ready.py       # Verifies Whisper model + Ollama are available
├── download_stt_model.py        # One-time Whisper model download
├── benchmark_offline.py         # Local inference timing
├── start_offline.bat            # Windows: start Ollama + backend
│
├── requirements.txt             # Runtime dependencies
├── requirements-dev.txt         # + test dependencies
├── .env.example                 # All settings with defaults
├── .github/workflows/ci.yml     # Tests, lint, build, audit on every push/PR
│
└── frontend/                    # React + Vite application
    ├── src/
    │   ├── App.jsx              # Main React component
    │   ├── config.js            # API base URL (VITE_API_BASE_URL)
    │   ├── components/
    │   │   ├── DoctorRecommendations.jsx
    │   │   ├── LocationPermission.jsx
    │   │   └── ui/              # About, Ayushman Bharat, Disclaimer, Emergency triage
    │   └── styles/breakpoints.js
    ├── package.json
    └── vite.config.js
```

---

## � Offline Configuration

No cloud API keys are required. All inference runs locally via Ollama.

### Verify Ollama is running
```bash
ollama list                              # shows gemma4:e2b
curl http://localhost:11434/api/tags     # confirms Ollama server
```

---

## 📊 API Endpoints

### Backend API (Port 8001)

#### 1. Core Health Endpoints
```
GET /
GET /api
GET /api/health-check
```

#### 2. Voice Transcription Endpoint
```
POST /api/transcribe-audio
Content-Type: multipart/form-data

Form fields:
  - audio: file (required)
  - language: en|hi|mr (optional, default: en)

Response:
{
  "text": "transcribed text",
  "language": "en"
}
```

#### 3. AI Consultation Endpoint
```
POST /api/get-doctor-response
Content-Type: application/json

Body:
{
  "patient_text": "string (required)",
  "language": "en|hi|mr",
  "image_data": ["base64_image_1", "base64_image_2"],
  "pdf_data": [{"name": "report.pdf", "data": "base64_pdf"}],
  "image_count": 0,
  "pdf_count": 0
}

Response (abridged):
{
  "doctor_response": "string",
  "audio_url": "/api/audio/doctor_response_<random>.wav",  // null when TTS is off/unavailable
  "urgency": "low|medium|high",
  "reasons": ["..."], "actions": ["..."],
  "specialist": "cardiologist", "confidence": 0.0-1.0,
  "triage_source": "toxin_fast_lane|red_flag_guardrail|local_gemma|emergency_fallback|unassessed",
  "emergency_action_block": { ... } | null
}

Errors: 422 for invalid input; 503 with a localized, patient-safe "detail" when the
assessment could not be completed (never a fabricated "low" result).
```

Vitals can be sent as fields (`heart_rate`, `bp_systolic`, `bp_diastolic`, `spo2`,
`temperature` in °C) or typed in the text as `BP: 140/90, Heart Rate: 85, Temp: 101°F, Oxygen: 96%`.
Critical vitals always produce `urgency: "high"`.

Uploaded images and PDFs are accepted (max 8) but **not yet analysed** by the triage
pipeline; they are only counted in `consensus_explanation`.

#### 4. Audio Playback / Status Endpoints
```
GET /api/audio/{filename}        # streams the generated WAV (random, unguessable name)
GET /api/audio-status/{filename} # { ready, status, file_size }
GET /api/voices                  # supported TTS voices by language
```

#### 5. Doctor Discovery Endpoints
```
POST /api/search-doctors
Content-Type: application/json

Body:
{
  "latitude": 18.5204,
  "longitude": 73.8567,
  "specialty": "cardiologist",
  "radius": 25000,
  "sort_by": "distance|rating|reviews|availability|experience",
  "limit": 20,
  "language": "en"
}
```

```
POST /api/search-doctors-by-city
Content-Type: application/json

Body:
{
  "city": "Mumbai",
  "specialty": "dermatologist",
  "sort_by": "distance|rating|reviews|availability|experience",
  "limit": 20,
  "language": "en",
  "user_latitude": 18.5204,
  "user_longitude": 73.8567
}
```

#### 6. Emergency Triage Endpoints
```
POST /api/emergency-triage
Content-Type: application/json

Body:
{
  "symptoms": "string (required)",
  "age": 52,
  "gender": "male|female|other",
  "vital_signs": {
    "blood_pressure_systolic": 140,
    "blood_pressure_diastolic": 90,
    "heart_rate": 98,
    "temperature_celsius": 38.2,
    "oxygen_saturation": 95,
    "respiratory_rate": 20
  },
  "medical_history": ["diabetes", "hypertension"],
  "symptom_duration": "2 hours",
  "language": "en|hi|mr",
  "latitude": 18.5204,
  "longitude": 73.8567,
  "ai_analysis": "optional prior AI analysis"
}
```

```
POST /api/emergency-triage/quick     # body: {"symptoms": "..."}
GET  /api/emergency-triage/quick     # deprecated: puts symptoms in the URL / access logs
POST /api/emergency-hospitals
GET /api/emergency-info
```

---

## 🧩 Complete Code Reference (Function and Module Index)

This section is generated from the current source code and is the most accurate technical reference in this repository.

### Backend (Python) - Files, Classes, and Functions

#### `api.py` (FastAPI entrypoint)
- Pydantic request/response models:
  - `ConsultationRequest`, `ConsultationResponse`, `TranscriptionResponse`
  - `DoctorSearchRequest`, `DoctorSearchResponse`
  - `CitySearchRequest`, `CitySearchResponse`
  - `QuickTriageRequest`, `QuickTriageResponse`
- HTTP route handlers:
  - `read_root()` -> `GET /`
  - `api_health_check()` -> `GET /api`
  - `transcribe_audio_endpoint(...)` -> `POST /api/transcribe-audio`
  - `get_consultation(...)` -> `POST /api/get-doctor-response`
  - `get_audio(filename)` -> `GET /api/audio/{filename}`
  - `get_voices()` -> `GET /api/voices`
  - `search_doctors_endpoint(request)` -> `POST /api/search-doctors`
  - `search_doctors_by_city_endpoint(request)` -> `POST /api/search-doctors-by-city`
  - `check_audio_status(filename)` -> `GET /api/audio-status/{filename}`
  - `emergency_triage(request)` -> `POST /api/emergency-triage`
  - `quick_emergency_triage(request)` -> `POST /api/emergency-triage/quick` (GET deprecated)
  - `find_emergency_hospitals(request)` -> `POST /api/emergency-hospitals`
  - `get_emergency_info()` -> `GET /api/emergency-info`
  - `health_check()` -> `GET /api/health-check`
- Triage pipeline (in order): `_evaluate_toxin_fast_lane()` → `_evaluate_red_flag_guardrail()`
  → `_run_local_gemma_triage()` / `_build_emergency_fallback_triage()` → `select_offline_first_triage()`
  → `_critical_vital_findings()` safety floor.
- Utility functions:
  - `_generate_response_audio(text, language)`, `cleanup_old_audio_files()`

#### `brain_of_the_doctor.py` (standalone consultation CLI — the API calls Ollama from `api.py`)
- Prompt and model utilities:
  - `get_system_prompt(language_code="en")`
- AI generation functions:
  - `get_doctor_advice_multimodal(patient_input, image_data_list=None, pdf_data_list=None, language="en")`
  - `get_doctor_advice_text_only(patient_input, language="en")`
- Post-processing and compatibility:
  - `extract_specialist_recommendation(doctor_response)`
  - `get_doctor_response(patient_message, image_data=None, pdf_data=None, language="en")`
  - `encode_image(image_path)`

#### `voice_of_the_patient.py` (speech-to-text)
- `improve_transcription(text, language_code="en")`
  - Corrects common Marathi/Hindi misheard words and cleans noisy text.
- `transcribe_audio_offline(audio_path, language_code="en")`
  - Uses faster-whisper locally with language-specific prompt hints.

#### `voice_of_the_doctor.py` (text-to-speech)
- Text cleaning and TTS core:
  - `clean_text_for_audio(text, language="en")`
  - `_text_to_speech_core(text, output_filepath, lang='en')`
- Public TTS helpers:
  - `generate_doctor_voice(...)`
  - `speak_as_doctor(...)`
  - `get_doctor_voice_for_ui(...)`
  - `text_to_speech_for_api(text, output_path, language="en")`
  - `get_available_voices()`
- Offline-first: pyttsx3 is the primary engine; no network required.

#### `advanced_doctor_service.py` (primary doctor search implementation)
- Class: `AdvancedDoctorSearchService`
- Key methods:
  - `_calculate_distance(...)`, `_calculate_distance_km(...)`
  - `_determine_city(...)`
  - `_get_prominent_doctors(...)`
  - `_is_available_today(...)`
  - `search_doctors_enhanced(...)`
  - `_apply_advanced_sorting(doctors, sort_by)`
  - `search_doctors_by_city(...)`
  - `_geocode_city(city)`
- Module-level async wrappers:
  - `search_doctors_enhanced(...)`
  - `search_doctors_by_city(...)`
- Only facility-level fields are returned; the per-doctor ratings, fees, credentials and
  appointment slots in the static data are unverified and are never sent to users.

#### `emergency_triage/` package

- `constants.py`
  - Defines `TRIAGE_LEVELS`, keyword sets (`CRITICAL_KEYWORDS`, `EMERGENCY_KEYWORDS`, `URGENT_KEYWORDS`), HEART/BE-FAST/TRAUMA configs, vital thresholds, emergency numbers, specialist mapping, and hospital capability requirements.

- `models.py`
  - Pydantic models and enums:
    - `TriageLevel`, `VitalSigns`, `EmergencyTriageRequest`
    - `HeartScore`, `BeFastScore`, `TraumaScore`, `EmergencyScores`
    - `EmergencyHospital`, `EmergencyAction`, `HospitalSearchRequest`, `TriageResponse`

- `triage_service.py`
  - Class: `TriageService`
  - Scoring methods:
    - `calculate_all_scores(...)`
    - `calculate_heart_score(...)`
    - `calculate_befast_score(...)`
    - `calculate_trauma_score(...)`
    - `quick_keyword_check(symptoms)`
  - Internal helpers:
    - `_compile_patterns()`, `_assess_vital_signs(vitals)`, `_check_respiratory_concern(symptoms)`

- `emergency_classifier.py`
  - Class: `EmergencyClassifier`
  - Main APIs:
    - `classify(request)`
    - `quick_classify(symptoms)`
  - Internal decision helpers:
    - `_score_to_level(scores)`
    - `_determine_emergency_type(...)`
    - `_detect_conditions(...)`
    - `_determine_time_sensitivity(level)`
    - `_generate_primary_action(...)`
    - `_generate_secondary_actions(...)`
    - `_get_specialist_recommendation(emergency_type)`
    - `_generate_assessment(...)`
    - `_calculate_confidence(...)`

- `hospital_routing_service.py`
  - Class: `HospitalRoutingService`
  - Multi-source routing methods:
    - `find_emergency_hospitals(request)`
    - `_search_overpass(...)`
    - `_parse_overpass_response(...)`
    - `_build_address_from_tags(tags)`
    - `_get_static_hospitals(...)`
    - `_score_and_sort(...)`
    - `_haversine(...)`
    - `get_nearest_hospital(hospitals)`
    - `get_best_match(hospitals, emergency_type)`

#### Tests and utility scripts (backend)
- `tests/` - pytest suite (`python -m pytest`): guardrails, toxin fast-lane, triage selection,
  safety regressions, API endpoints, security/privacy, fairness metrics, hospital routing.
- `scripts/run_sample_queries.py` - runs five sample cases against a live Ollama.
- `scripts/stt_smoke_test.py` - transcribes your own audio files with faster-whisper.
- `check_offline_ready.py` - verifies Ollama and all offline components are healthy.
- `benchmark_offline.py` - benchmarks local inference speed.

---

### Frontend (React) - Files, Components, and Key Functions

#### Core app files
- `frontend/src/main.jsx`
  - React root bootstrap; renders `<App />` in `StrictMode`.
- `frontend/src/App.jsx` (main app orchestrator)
  - Internal components: `DiagnosisLoading`, `AudioPlayer`.
  - Major handlers/functions:
    - `checkApiConnection()`
    - `handleLanguageSelect(...)`, `handleDisclaimerAccept()`
    - `startRecording()`, `stopRecording()`, `toggleRecording()`
    - `transcribeAudio(audioBlob)`
    - `handleFileUpload(...)`, `removeFile(index)`
    - `pollAudioStatus(filename, maxAttempts)`
    - `handleSubmit()`
    - `resetConsultation()`
    - `handleLocationGranted(location)`, `handleLocationDenied()`
    - `handleFindDoctors()`
    - `copyToClipboard(text)`, `downloadAudio(...)`, `downloadTranscription()`

#### Component folder: `frontend/src/components/`
- `DoctorRecommendations.jsx`
  - Functions: `searchDoctors()`, `searchDoctorsByCity()`, `handleFilterChange(...)`, `renderStars(...)`, `getDirections(...)`, `callDoctor(...)`, `visitWebsite(...)`.
- `LocationPermission.jsx`
  - Functions: `requestLocation()`, `handleDeny()`, `handleSearchByCity()`.
- `ui/EmergencyButton.jsx` - `EmergencyButton`, `FloatingEmergencyButton`; opens `EmergencyTriage`.
- `ui/EmergencyTriage.jsx` - `requestLocation(...)`, `performTriage(...)`, `openDirections(hospital)`;
  calls `POST /api/emergency-triage`, falls back to `POST /api/emergency-triage/quick`.
- `ui/DisclaimerModal.jsx` - consent modal for medical/legal/privacy terms.
- `ui/AboutSection.jsx` - project overview modal.
- `ui/AyushmanBharatCard.jsx` - PM-JAY eligibility checker.

#### Configuration and styling
- `frontend/src/config.js` -> `API_BASE_URL`, `apiUrl(path)`, `openExternal(url)`.
- `frontend/src/styles/breakpoints.js` -> `breakpoints`, `media` helpers.

---

### Environment Variables (code-verified)

All settings live in `config.py`; `.env.example` lists them with defaults. Real environment
variables take precedence over `.env`.

Ollama / triage:
- `OLLAMA_BASE_URL` (default: `http://localhost:11434`), `OLLAMA_MODEL` (default: `gemma4:e2b`)
- `LOCAL_GEMMA_MODEL`, `LOCAL_GEMMA_URL` - optional overrides; default to the two above
- `LOCAL_GEMMA_TIMEOUT_SECONDS` (120), `LOCAL_GEMMA_NUM_CTX` (1024), `LOCAL_GEMMA_NUM_PREDICT` (1400)
- `LOCAL_TRIAGE_CONFIDENCE_THRESHOLD` (0.6) - below it the rules-based classifier is used
- `ENABLE_LOCAL_TRIAGE` (true), `FAIRNESS_PARITY_THRESHOLD` (0.05)

Server:
- `API_HOST` (`127.0.0.1`), `API_PORT` (`8001`), `MAX_REQUEST_MB` (60)
- `CORS_ALLOW_ORIGINS` (`http://localhost:3000,http://127.0.0.1:3000`)
- `FRONTEND_DIST_DIR` (`frontend/dist`) - served at `/` when it exists

Offline STT:
- `ENABLE_LOCAL_STT` (true), `LOCAL_STT_MODEL_SIZE` (`small`), `LOCAL_STT_MODEL_PATH`,
  `LOCAL_STT_DEVICE` (`cpu`), `LOCAL_STT_COMPUTE_TYPE` (`int8`), `LOCAL_STT_CPU_THREADS` (0 = auto),
  `LOCAL_STT_NUM_WORKERS` (1), `LOCAL_STT_LOCAL_FILES_ONLY` (true), `MAX_AUDIO_UPLOAD_MB` (25)

Offline TTS:
- `LOCAL_TTS_ENABLED` (true), `AUDIO_OUTPUT_DIR` (`audio_outputs/`),
  `AUDIO_RETENTION_SECONDS` (3600)

Frontend (build time):
- `VITE_API_BASE_URL` - only when the API is on a different origin (default: same origin)
- `VITE_DEV_API_TARGET` - backend used by the dev-server proxy (default `http://127.0.0.1:8001`)

---

### Runtime Data Flow (actual implementation)

1. User records audio or enters text in frontend.
2. Audio (if present) -> `POST /api/transcribe-audio`.
3. Consultation payload (text + optional image/pdf base64) -> `POST /api/get-doctor-response`.
4. Backend triage pipeline (`api.py`): toxin fast-lane → red-flag guardrail → Gemma 4 via Ollama
   (rules-based classifier as fallback) → critical-vitals safety floor.
5. Backend TTS pipeline (`voice_of_the_doctor.py`) generates a WAV in `audio_outputs/` (deleted after
   `AUDIO_RETENTION_SECONDS`).
6. Frontend polls `GET /api/audio-status/{filename}` and then plays `GET /api/audio/{filename}`.
7. If user chooses doctor discovery, frontend calls:
   - `POST /api/search-doctors` (location-based), or
   - `POST /api/search-doctors-by-city` (city query).
8. Emergency flow uses `EmergencyButton` / `EmergencyTriage` and calls:
   - `POST /api/emergency-triage` (full), fallback `POST /api/emergency-triage/quick`.
   - Optional hospital lookup via `POST /api/emergency-hospitals`.

---

## 🎯 Features in Detail

### 1. AI Medical Consultation

**How It Works:**
1. Patient records symptoms via voice or text
2. Optionally uploads medical images/PDFs
3. Gemma 4 via Ollama analyzes input locally
4. AI generates professional medical assessment
5. System identifies appropriate specialist
6. Response converted to audio (pyttsx3 offline TTS)
7. Audio delivered with text transcript

**Supported Specialties (20+):**
- Dermatologist (skin conditions)
- Cardiologist (heart issues)
- Orthopedic (bones/joints)
- Neurologist (brain/nervous system)
- Pediatrician (children's health)
- Gynecologist (women's health)
- Ophthalmologist (eye conditions)
- Pulmonologist (lungs/respiratory)
- Urologist (urinary system)
- Nephrologist (kidney disease)
- ENT (ear/nose/throat)
- Gastroenterologist (digestive system)
- Psychiatrist (mental health)
- Endocrinologist (hormones/diabetes)
- Rheumatologist (autoimmune)
- And more...

### 2. Location-Based Doctor Discovery 

**Data Sources:**
1. **Static specialist directory** (`advanced_doctor_service.py`): a small set of listings for
   major cities (Pune, Mumbai, Delhi, Bengaluru, Chennai). Listings have **not** been independently
   verified; every result says so and asks the user to call ahead.
2. **Static emergency hospital list** (`emergency_triage/hospital_routing_service.py`): major
   public hospitals in seven cities. Locations outside these cities return no results.

**Search Capabilities:**
- Search near the user's location or by city name without GPS
- Filter by specialty; sort by distance or listed availability
- Distance calculation to user location
- Hospital address and main phone number

**Medical Safety:**
- ✅ Ratings, review counts, fees, credentials and appointment slots are never shown
- ✅ Every listing is marked unverified with a "call ahead" note

### 3. Voice Interaction

**Speech-to-Text:**
- Engine: faster-whisper (local, no network required)
- Languages: English, Hindi, Marathi
- Offline transcription
- Smart corrections for Indian languages
- Handles medical terminology

**Text-to-Speech:**
- Primary: pyttsx3 (fully offline)
- Languages: English, Hindi, Marathi
- Natural medical voices
- Markdown cleaning for better audio

### 4. Medical Document Processing

**Supported Files:**
- **Images**: JPG, PNG, JPEG, WebP (X-rays, skin photos, medical scans)
- **PDFs**: Lab reports, medical records, prescriptions
- **Limit**: 8 files total per consultation
- **Processing**: Base64 encoding for secure transmission

**Analysis:** not implemented yet. Files are accepted and counted, but the triage pipeline
does not read their content; assessments are based on the typed/spoken symptoms and vitals.

---

## 🌍 Multilingual Support

### Supported Languages

| Language | Code | UI | Voice Input | Voice Output | Medical Terms |
|----------|------|----|-----------|--------------|--------------| 
| English | `en` | ✅ | ✅ | ✅ | ✅ |
| Hindi (हिंदी) | `hi` | ✅ | ✅ | ✅ | ✅ |
| Marathi (मराठी) | `mr` | ✅ | ✅ | ✅ | ✅ |

### Translation Coverage
- All UI elements
- System prompts
- Medical responses
- Error messages
- Loading states
- Button labels

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Pydantic v2)
- **Server**: Uvicorn (ASGI)
- **AI/LLM**: Ollama (Gemma 4 E2B) over HTTP (`requests`)
- **STT**: faster-whisper (local)
- **TTS**: pyttsx3 (offline)
- **Environment**: python-dotenv

### Frontend
- **Framework**: React 19.1.0
- **Build Tool**: Vite 7.0.0
- **Styling**: Styled Components 6.1.19
- **Animations**: Framer Motion 12.19.2
- **HTTP Client**: Axios
- **Voice Recording**: browser MediaRecorder API
- **Icons**: React Icons 5.5.0

### Local Services
- **AI**: Ollama (Gemma 4 E2B, fully offline)
- **STT**: faster-whisper (on-device)
- **TTS**: pyttsx3 (offline)
- **Directions**: opens Google Maps only when the user taps "Directions"

---

## 🧪 Testing

### Manual Testing

**Test Consultation:**
```bash
# Terminal 1
py api.py

# Terminal 2 (from frontend/)
npm run dev

# Open browser: http://localhost:3000
# Test: Record voice → Get triage assessment
```

**Test Doctor Search:**
```bash
# After getting diagnosis, click "Find Nearby Doctors"
# Allow location access or search by city
# Test sorting: Distance, Rating, Reviews
```

### Automated Tests

```bash
pip install -r requirements-dev.txt
python -m pytest            # backend: no Ollama, microphone or network needed
cd frontend && npm run lint && npm run build
```

CI (`.github/workflows/ci.yml`) runs the same on every push and pull request.

### API Testing

**Using curl:**
```bash
# Health check
curl http://127.0.0.1:8001/

# Doctor search (replace coordinates)
curl -X POST http://127.0.0.1:8001/api/search-doctors \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 18.5204,
    "longitude": 73.8567,
    "specialty": "cardiologist",
    "sort_by": "distance",
    "limit": 5
  }'
```

**Using Python:**
```python
import asyncio
from advanced_doctor_service import search_doctors_enhanced

async def test():
    doctors = await search_doctors_enhanced(
        specialty='cardiologist',
        latitude=18.5204,
        longitude=73.8567,
        sort_by='distance',
        limit=5
    )
    print(f"Found {len(doctors)} listings")
    for doc in doctors:
        print(f"{doc['name']} - {doc['hospital']} - {doc['distance_km']}km")

asyncio.run(test())
```

---

## 📝 Usage Examples

### Example 1: Voice Consultation
```
1. Select language: English
2. Click microphone → Record: "I have chest pain and shortness of breath"
3. Upload X-ray image (optional)
4. Click "Get Doctor's Diagnosis"
5. Receive: AI analysis + audio response + specialist recommendation
6. Click "Find Nearby Doctors" → Location-based cardiologists
```

### Example 2: Text + PDF Consultation
```
1. Select language: Hindi
2. Type symptoms in text box
3. Upload lab report PDF
4. Get comprehensive analysis in Hindi
5. Audio plays in Hindi voice
6. Search for specialists in your city
```

### Example 3: City-Based Doctor Search
```
1. Complete consultation
2. Get specialist recommendation
3. Search by city: "Mumbai"
4. Sort by: "Top Rated"
5. View doctors with verified ratings and contact info
```

---

## 🔒 Security & Privacy

### Data Handling
- ✅ All inference, STT and TTS run on the device; no patient data is sent to external services
- ✅ Generated recordings use random names and are deleted after `AUDIO_RETENTION_SECONDS`
  (default 1 hour), including leftovers at startup
- ✅ Logs never contain symptoms, transcripts, model output or locations (only sizes/outcomes)
- ✅ Production bundles strip debug logging; the UI makes no third-party requests
- ✅ No patient data stored permanently

### API Security
- CORS limited to `CORS_ALLOW_ORIGINS` (no credentials); the bundled UI is same-origin
- Input validation and size limits: text, attachments, audio uploads (`MAX_AUDIO_UPLOAD_MB`),
  request bodies (`MAX_REQUEST_MB`)
- Error responses never include internal exception details
- **No authentication:** the API binds to `127.0.0.1` by default. Do not expose it on a
  network without a reverse proxy that adds TLS and authentication.

### Medical Disclaimer
⚠️ **IMPORTANT**: This AI tool is for educational and informational purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical concerns.

---

## 🐛 Troubleshooting

### Common Issues

**1. Backend won't start**
```bash
# Check Python version
py --version  # Should be 3.10+

# Check if port 8001 is in use
netstat -ano | findstr :8001

# Kill process if needed
taskkill /PID <PID> /F

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**2. Frontend won't start**
```bash
# Clear cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Try different port
npm run dev -- --port 3000
```

**3. Audio recording not working**
```bash
# Check browser permissions
# Chrome: Settings → Privacy → Site Settings → Microphone
# Allow microphone access for localhost

# Recording happens in the browser; transcription needs the Whisper model:
python download_stt_model.py
```

**4. Ollama not responding**
```bash
# Check Ollama is running
ollama serve

# Verify model is pulled
ollama list | findstr gemma4:e2b   # Windows
ollama list | grep gemma4:e2b      # macOS/Linux
```

**5. Sorting not working correctly**

- Updated `advanced_doctor_service.py`
- Added safe numeric extraction helpers
- Now handles mixed data types properly

---

## 📦 Maintenance & Cleanup

### Current Repository State

No automated cleanup scripts are currently committed in this repository.

Recommended maintenance practices:
- Remove stale files only after running tests and manual API checks
- Keep `audio_outputs/` trimmed if it grows too large
- Run `python -m pytest` after backend changes

---

## 🚀 Deployment

### Production (single device, offline)

```bash
pip install -r requirements.txt
python download_stt_model.py              # once, while online
cd frontend && npm ci && npm run build && cd ..
python api.py                             # UI + API on http://127.0.0.1:8001
```

Checklist:
- Keep `API_HOST=127.0.0.1` unless a reverse proxy adds TLS and authentication in front.
- If the UI is hosted on another origin, build it with `VITE_API_BASE_URL=https://api.example`
  and add that UI origin to `CORS_ALLOW_ORIGINS`.
- Run one Uvicorn worker: the fairness metrics are in-memory and TTS is serialized per process.
- Review the static specialist directory before relying on it (see Data Sources above).
- Pin dependency versions for your deployment (`pip freeze` in a clean venv) and keep CI green.

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run linters
black brain_of_the_doctor.py
flake8 api.py

# Frontend linting
npm run lint
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👥 Authors

- **AJ** - *Initial work* - [@aj4344](https://github.com/aj4344)

---

## 🙏 Acknowledgments

- **Google** - For Gemma 4 open weights
- **Ollama** - For local model serving
- **OpenStreetMap** - For medical facility data
- **faster-whisper** - For on-device speech-to-text
- **FastAPI** - For the excellent Python framework
- **React** - For the powerful UI library

---

## 📊 Project Stats

- **Supported Languages**: 3 (EN, HI, MR)
- **Clinical protocols**: HEART, BE-FAST, Trauma + red-flag and toxin guardrails
- **Emergency hospital list**: major public hospitals in 7 cities (static, offline)


---

## 🔮 Future Roadmap

The production-readiness plan (requirements, phases, acceptance criteria) is in [docs/PRD.md](docs/PRD.md).

- [ ] Analyse uploaded reports/images in the triage pipeline (currently accepted but not read)
- [ ] Replace the static specialist directory with a verified source (e.g. ABDM Health Facility Registry)
- [ ] Add more Indian languages (Tamil, Telugu, Bengali)
- [ ] Implement appointment booking system
- [ ] Add telemedicine video consultation
- [ ] Integrate with ABDM (Ayushman Bharat Digital Mission)
- [ ] Add prescription generation
- [ ] Implement medical history tracking
- [ ] Add symptoms checker with visual body map
- [ ] Electronic health records (EHR) support

---

## 📞 Contact

- 📧 **Email**: jabhijeet789@gmail.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/aj4344/gemma-guardians-HealstationAI/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/aj4344/gemma-guardians-HealstationAI/discussions)

---

## ⭐ Show Your Support

If you find this project helpful, please consider:
- ⭐ Starring the repository
- 🔀 Forking for your own use
- 🐛 Reporting bugs
- 💡 Suggesting features
- 📣 Sharing with others

---

<div align="center">

**Made with ❤️ and 🤖 AI**

*HealStation AI: Doctor Assistant - Revolutionizing Medical Consultation*

</div>


