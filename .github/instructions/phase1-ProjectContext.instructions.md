---
applyTo: '**'
---



I have a comprehensive understanding of the MedMind AI Doctor project. Let me provide you with a detailed analysis of the project structure and functionality:

📋 Project Analysis: MedMind AI Doctor
🏗️ Architecture Overview
This is a sophisticated AI-powered medical consultation application with a modern tech stack:

Backend (Python):

FastAPI - High-performance async web framework
Groq API - For LLM (Llama-4-Scout) and Whisper transcription
Edge-TTS/gTTS - Text-to-speech generation
PyPDF2 - PDF processing for medical reports
Frontend (React):

React 19 with hooks and functional components
Styled Components - Component-based styling
Vite - Fast build tool
Axios - HTTP client for API communication
🎯 Core Features
1. Multilingual Support
English, Hindi, Marathi with proper translations
Language-specific TTS voices
Smart transcription corrections for local languages
2. Multimodal Input
Voice Recording - Real-time audio capture and transcription
Image Upload - Medical images (X-rays, skin conditions, etc.)
PDF Processing - Medical reports and lab results
Text Input - Manual symptom description
3. AI-Powered Analysis
Groq's Llama-4-Scout-17B for multimodal medical analysis
Whisper-Large-V3 for speech-to-text transcription
Comprehensive prompts for professional medical consultation
Differential diagnosis with treatment recommendations
4. Professional UI/UX
Modern medical interface with hospital-themed design
Dark/Light mode toggle
Real-time loading animations with stages
Responsive design for all devices
Audio playback with controls
🔧 Key Components
Backend Files:
api.py - Main FastAPI server with RESTful endpoints
brain_of_the_doctor.py - AI logic and multimodal processing
voice_of_the_doctor.py - TTS generation with Edge-TTS
voice_of_the_patient.py - STT with Groq Whisper
Frontend Files:
App.jsx - Main React component (2071 lines!)
ConsultationPanel.jsx - Chat-like consultation interface
Styled Components - Professional medical UI
📊 Workflow Process
Language Selection → User chooses preferred language
Audio Recording → Real-time symptom recording
Transcription → Groq Whisper converts speech to text
File Upload → Medical images/PDFs processed
AI Analysis → Multimodal LLM analyzes all inputs
Response Generation → Professional medical consultation
TTS Output → Doctor's voice response in selected language
Results Display → Text + Audio with professional UI
🚀 Technical Highlights
Advanced Features:
Async processing for non-blocking operations
Smart error handling with fallback mechanisms
File type validation and size limits
Real-time status updates during processing
Audio polling for smooth TTS delivery
Cleanup routines for temporary files
Performance Optimizations:
Lazy loading for heavy components
Efficient state management with React hooks
Optimized API calls with proper timeouts
Memory management for uploaded files
🛠️ Development Setup
The project uses:

Batch files for easy startup (run_backend.bat, run_frontend.bat)
Environment variables for API keys
Modern Python packaging with requirements.txt
Vite development server for hot reloading
🎨 UI/UX Design
Medical theme with stethoscope icons and hospital colors
Professional typography and spacing
Intuitive step-by-step workflow
Real-time feedback and status indicators
Accessibility features with proper ARIA labels
🔐 Security & Privacy
API key management through environment variables
CORS configuration for secure cross-origin requests
Input validation and sanitization
Temporary file cleanup for privacy