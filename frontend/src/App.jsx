import React, { useState, useEffect, useRef } from 'react';
import styled, { ThemeProvider, createGlobalStyle } from 'styled-components';
import { 
  FaStethoscope, FaMicrophone, FaStop, FaUpload, FaMoon, FaSun, 
  FaUser, FaGlobe, FaDownload, FaTrash, FaFilePdf, FaCopy, 
  FaPlay, FaUserMd, FaHeartbeat, FaPause, FaTachometerAlt, FaInfoCircle, FaHeart
} from 'react-icons/fa';
import axios from 'axios';
import LocationPermission from './components/LocationPermission';
import DoctorRecommendations from './components/DoctorRecommendations';
import AboutSection from './components/ui/AboutSection';
import AyushmanBharatCard from './components/ui/AyushmanBharatCard';
import DisclaimerModal from './components/ui/DisclaimerModal';
import { EmergencyButton } from './components/ui/EmergencyButton';
import { apiUrl, openExternal } from './config';

// Simplified Translations
const TRANSLATIONS = {
  en: {
    language_name: "English",
    header: "🩺 HealStation AI",
    subheader: "Offline Triage for Frontline Health Workers",
    patient_panel: "👤 Patient Input",
    patient_desc: "Describe your symptoms and upload medical files.",
    doctor_panel: "🩺 Doctor's Analysis", 
    doctor_desc: "Triage Assessment",
    step1_title: "🎤 Step 1: Record Symptoms",
    step1_desc: "Record your symptoms clearly.",
    step1_text_title: "📝 Or Type Your Symptoms",
    step1_text_desc: "Describe your symptoms in text form.",
    text_input_placeholder: "Describe your symptoms, medical history, and any concerns...",
    text_input_label: "Text Input:",
    text_required: "Please record audio or type your symptoms",
    step2_title: "📷 Step 2: Upload Files (Optional)",
    step2_desc: "Upload medical images or documents for better analysis.",
    files_optional: "Medical files are optional but recommended for better diagnosis",
    files_uploaded: "files uploaded for better analysis",
    step3_title: "🏥 Step 3: Get Diagnosis",
    recommendation_title: "💡 Recommendation:",
    recommendation_text: "For more accurate diagnosis, consider uploading medical reports, test results, or photos of affected areas. This is optional but highly recommended.",
    diagnosis_button: "⚡ Get Triage Assessment",
    find_doctors_button: "🏥 Find Nearby Doctors & Hospitals",
    find_doctors_desc: "Find medical professionals near you for this condition",
    audio_recorded: "Audio recorded successfully!",
    transcription_label: "Transcription:",
    record_required: "Audio recording required",
    files_required: "Medical files required",
    upload_medical_files: "Upload Medical Files",
    max_files_reached: "Maximum 8 files allowed",
    analyzing: "AI Doctor is analyzing...",
    generating_diagnosis: "Generating comprehensive diagnosis...",
    creating_audio: "Creating audio response...",
    finalizing: "Finalizing presentation...",
    analysis_title: "🏥 Doctor's Analysis",
    audio_title: "🎵 Audio Response",
    reset_button: "🔄 Start New Consultation",
    copy_text: "Copy",
    download_audio: "Audio",
    clear_recording: "Clear",
    download_transcription: "Download",
    transcribing_audio: "Transcribing...",
    remove_file: "Remove",
    disclaimer: "⚠️ This AI tool is for educational purposes only.",
    ayushman_button: "🏥 Ayushman Bharat",
    ayushman_title: "Ayushman Bharat - PM-JAY",
    ayushman_subtitle: "Pradhan Mantri Jan Arogya Yojana",
    ayushman_desc: "Free health insurance for economically vulnerable families",
    check_eligibility: "Check Eligibility",
    name_label: "Full Name:",
    age_label: "Age:",
    state_label: "State:",
    income_label: "Annual Family Income:",
    area_label: "Area Type:",
    rural: "Rural",
    urban: "Urban",
    income_below_2l: "Below ₹2 Lakh",
    income_2_5l: "₹2-5 Lakh",
    income_above_5l: "Above ₹5 Lakh",
    eligible_title: "✅ Congratulations! You may be eligible",
    eligible_message: "Based on the information provided, you appear to qualify for Ayushman Bharat scheme.",
    not_eligible_title: "ℹ️ Not Eligible Currently",
    not_eligible_message: "Based on income criteria, you may not qualify. Consider state-specific health schemes.",
    coverage_info: "Coverage: ₹5,00,000 per family/year",
    beneficiary_id: "Sample Beneficiary ID:",
    benefits_title: "Key Benefits:",
    benefit_1: "Cashless treatment at empaneled hospitals",
    benefit_2: "Coverage for hospitalization expenses",
    benefit_3: "Pre and post-hospitalization expenses",
    benefit_4: "No cap on family size",
    find_hospitals: "Find Empaneled Hospitals"
  },
  hi: {
    language_name: "हिंदी",
    header: "🩺 हीलस्टेशन एआई",
    subheader: "फ्रंटलाइन स्वास्थ्य कर्मचारियों के लिए ऑफलाइन ट्राइएज",
    patient_panel: "👤 रोगी का इनपुट",
    patient_desc: "अपने लक्षणों का वर्णन करें और मेडिकल फाइलें अपलोड करें।",
    doctor_panel: "🩺 डॉक्टर का विश्लेषण",
    doctor_desc: "ट्राइएज मूल्यांकन",
    step1_title: "🎤 चरण 1: लक्षण रिकॉर्ड करें",
    step1_desc: "अपने लक्षणों को स्पष्ट रूप से रिकॉर्ड करें।",
    step1_text_title: "📝 या अपने लक्षण टाइप करें",
    step1_text_desc: "अपने लक्षणों का टेक्स्ट में वर्णन करें।",
    text_input_placeholder: "अपने लक्षण, चिकित्सा इतिहास और किसी भी चिंता का वर्णन करें...",
    text_input_label: "टेक्स्ट इनपुट:",
    text_required: "कृपया ऑडियो रिकॉर्ड करें या अपने लक्षण टाइप करें",
    step2_title: "📷 चरण 2: फाइलें अपलोड करें (वैकल्पिक)",
    step2_desc: "बेहतर विश्लेषण के लिए मेडिकल इमेज या दस्तावेज़ अपलोड करें।",
    files_optional: "मेडिकल फाइलें वैकल्पिक हैं लेकिन बेहतर निदान के लिए सुझाई जाती हैं",
    files_uploaded: "बेहतर विश्लेषण के लिए फाइलें अपलोड की गईं",
    step3_title: "🏥 चरण 3: निदान प्राप्त करें",
    recommendation_title: "💡 सुझाव:",
    recommendation_text: "अधिक सटीक निदान के लिए, मेडिकल रिपोर्ट, टेस्ट रिजल्ट या प्रभावित क्षेत्रों की फोटो अपलोड करने पर विचार करें। यह वैकल्पिक है लेकिन अत्यधिक अनुशंसित है।",
    diagnosis_button: "⚡ ट्राइएज मूल्यांकन प्राप्त करें",
    audio_recorded: "ऑडिओ सफलतापूर्वक रिकॉर्ड किया गया!",
    transcription_label: "अनुवाद:",
    record_required: "ऑडियो रिकॉर्डिंग आवश्यक है",
    files_required: "मेडिकल फाइलें आवश्यक हैं",
    upload_medical_files: "मेडिकल फाइलें अपलोड करें",
    max_files_reached: "अधिकतम 8 फाइलों की अनुमति है",
    analyzing: "एआई डॉक्टर विश्लेषण कर रहा है...",
    generating_diagnosis: "व्यापक निदान तैयार कर रहा है...",
    creating_audio: "ऑडियो प्रतिक्रिया बना रहा है...",
    finalizing: "प्रस्तुति को अंतिम रूप दे रहा है...",
    analysis_title: "🏥 डॉक्टर का विश्लेषण",
    audio_title: "🎵 ऑडियो प्रतिक्रिया",
    reset_button: "🔄 नया परामर्श शुरू करें",
    copy_text: "कॉपी करें",
    download_audio: "ऑडिओ",
    clear_recording: "साफ़ करें",
    download_transcription: "डाउनलोड करें",
    transcribing_audio: "अनुवाद हो रहा है...",
    remove_file: "हटाएं",
    find_doctors_button: "🏥 नजदीकी डॉक्टर और अस्पताल खोजें",
    find_doctors_desc: "इस स्थिति के लिए अपने पास के चिकित्सक पेशेवर खोजें",
    disclaimer: "⚠️ यह एआई टूल केवल शैक्षिक उद्देश्यों के लिए है।",
    ayushman_button: "🏥 आयुष्मान भारत",
    ayushman_title: "आयुष्मान भारत - PM-JAY",
    ayushman_subtitle: "प्रधानमंत्री जन आरोग्य योजना",
    ayushman_desc: "आर्थिक रूप से कमजोर परिवारों के लिए मुफ्त स्वास्थ्य बीमा",
    check_eligibility: "पात्रता जांचें",
    name_label: "पूरा नाम:",
    age_label: "आयु:",
    state_label: "राज्य:",
    income_label: "वार्षिक पारिवारिक आय:",
    area_label: "क्षेत्र प्रकार:",
    rural: "ग्रामीण",
    urban: "शहरी",
    income_below_2l: "₹2 लाख से कम",
    income_2_5l: "₹2-5 लाख",
    income_above_5l: "₹5 लाख से अधिक",
    eligible_title: "✅ बधाई हो! आप पात्र हो सकते हैं",
    eligible_message: "प्रदान की गई जानकारी के आधार पर, आप आयुष्मान भारत योजना के लिए योग्य प्रतीत होते हैं।",
    not_eligible_title: "ℹ️ वर्तमान में पात्र नहीं",
    not_eligible_message: "आय मानदंड के आधार पर, आप योग्य नहीं हो सकते हैं। राज्य-विशिष्ट स्वास्थ्य योजनाओं पर विचार करें।",
    coverage_info: "कवरेज: ₹5,00,000 प्रति परिवार/वर्ष",
    beneficiary_id: "नमूना लाभार्थी आईडी:",
    benefits_title: "मुख्य लाभ:",
    benefit_1: "सूचीबद्ध अस्पतालों में कैशलेस उपचार",
    benefit_2: "अस्पताल में भर्ती खर्चों के लिए कवरेज",
    benefit_3: "अस्पताल में भर्ती से पहले और बाद के खर्च",
    benefit_4: "परिवार के आकार पर कोई सीमा नहीं",
    find_hospitals: "सूचीबद्ध अस्पताल खोजें"
  },
  mr: {
    language_name: "मराठी",
    header: "🩺 हीलस्टेशन एआय",
    subheader: "फ्रंटलाइन आरोग्य कर्मचाऱ्यांसाठी ऑफलाइन ट्रायेज",
    patient_panel: "👤 रुग्णाची माहिती",
    patient_desc: "तुमच्या लक्षणांचे वर्णन करा आणि वैद्यकीय फाइल अपलोड करा.",
    doctor_panel: "🩺 डॉक्टरांचे विश्लेषण",
    doctor_desc: "ट्रायेज मूल्यांकन",
    step1_title: "🎤 पाऊल 1: लक्षणे रेकॉर्ड करा",
    step1_desc: "तुमची लक्षणे स्पष्टपणे रेकॉर्ड करा.",
    step1_text_title: "📝 किंवा तुमची लक्षणे टाइप करा",
    step1_text_desc: "तुमच्या लक्षणांचे मजकूर स्वरूपात वर्णन करा.",
    text_input_placeholder: "तुमची लक्षणे, वैद्यकीय इतिहास आणि कोणत्याही चिंतेचे वर्णन करा...",
    text_input_label: "मजकूर इनपुट:",
    text_required: "कृपया ऑडिओ रेकॉर्ड करा किंवा तुमची लक्षणे टाइप करा",
    step2_title: "📷 पाऊल 2: फाइल अपलोड करा (वैकल्पिक)",
    step2_desc: "चांगल्या विश्लेषणासाठी वैद्यकीय प्रतिमा किंवा दस्तऐवज अपलोड करा.",
    files_optional: "वैद्यकीय फाइल वैकल्पिक आहेत परंतु चांगल्या निदानासाठी सुचवल्या जातात",
    files_uploaded: "चांगल्या विश्लेषणासाठी फाइल अपलोड केल्या",
    step3_title: "🏥 पाऊल 3: निदान मिळवा",
    recommendation_title: "💡 शिफारस:",
    recommendation_text: "अधिक अचूक निदानासाठी, वैद्यकीय अहवाल, चाचणी निकाल किंवा प्रभावित भागांचे फोटो अपलोड करण्याचा विचार करा. हे वैकल्पिक आहे परंतु अत्यधिक शिफारस केली जाते.",
    diagnosis_button: "⚡ ट्राइएज मूल्यांकन मिळवा",
    audio_recorded: "ऑडिओ यशस्वीरित्या रेकॉर्ड झाला!",
    transcription_label: "लिप्यंतरण:",
    record_required: "ऑडिओ रेकॉर्डिंग आवश्यक आहे",
    files_required: "वैद्यकीय फाइल आवश्यक आहेत",
    upload_medical_files: "वैद्यकीय फाइल अपलोड करा",
    max_files_reached: "जास्तीत जास्त 8 फाइलांना परवानगी आहे",
    analyzing: "एआय डॉक्टर विश्लेषण करत आहे...",
    generating_diagnosis: "सर्वसमावेशक निदान तयार करत आहे...",
    creating_audio: "ऑडिओ प्रतिसाद तयार करत आहे...",
    finalizing: "सादरीकरण अंतिम करत आहे...",
    analysis_title: "🏥 डॉक्टरांचे विश्लेषण",
    audio_title: "🎵 ऑडिओ प्रतिसाद",
    reset_button: "🔄 नवीन सल्लामसलत सुरू करा",
    copy_text: "कॉपी करा",
    download_audio: "ऑडिओ",
    clear_recording: "साफ करा",
    download_transcription: "डाउनलोड करा",
    transcribing_audio: "लिप्यंतरण होत आहे...",
    remove_file: "काढा",
    find_doctors_button: "🏥 जवळील डॉक्टर आणि रुग्णालय शोधा",
    find_doctors_desc: "या स्थितीसाठी आपल्या जवळील वैद्यकीय व्यावसायिक शोधा",
    disclaimer: "⚠️ हे एआय साधन केवळ शैक्षणिक उद्देशांसाठी आहे।",
    ayushman_button: "🏥 आयुष्मान भारत",
    ayushman_title: "आयुष्मान भारत - PM-JAY",
    ayushman_subtitle: "प्रधानमंत्री जन आरोग्य योजना",
    ayushman_desc: "आर्थिकदृष्ट्या असुरक्षित कुटुंबांसाठी मोफत आरोग्य विमा",
    check_eligibility: "पात्रता तपासा",
    name_label: "पूर्ण नाव:",
    age_label: "वय:",
    state_label: "राज्य:",
    income_label: "वार्षिक कौटुंबिक उत्पन्न:",
    area_label: "क्षेत्र प्रकार:",
    rural: "ग्रामीण",
    urban: "शहरी",
    income_below_2l: "₹2 लाखापेक्षा कमी",
    income_2_5l: "₹2-5 लाख",
    income_above_5l: "₹5 लाखापेक्षा जास्त",
    eligible_title: "✅ अभिनंदन! तुम्ही पात्र असू शकता",
    eligible_message: "प्रदान केलेल्या माहितीच्या आधारे, तुम्ही आयुष्मान भारत योजनेसाठी पात्र आहात.",
    not_eligible_title: "ℹ️ सध्या पात्र नाही",
    not_eligible_message: "उत्पन्न निकषांवर आधारित, तुम्ही पात्र नसाल. राज्य-विशिष्ट आरोग्य योजनांचा विचार करा.",
    coverage_info: "कव्हरेज: ₹5,00,000 प्रति कुटुंब/वर्ष",
    beneficiary_id: "नमुना लाभार्थी आयडी:",
    benefits_title: "मुख्य फायदे:",
    benefit_1: "सूचीबद्ध रुग्णालयांमध्ये कॅशलेस उपचार",
    benefit_2: "रुग्णालयात दाखल खर्चासाठी कव्हरेज",
    benefit_3: "रुग्णालयात दाखल होण्यापूर्वी आणि नंतरचे खर्च",
    benefit_4: "कुटुंबाच्या आकारावर कोणतीही मर्यादा नाही",
    find_hospitals: "सूचीबद्ध रुग्णालय शोधा"
  }
};

// Simple Themes
const lightTheme = {
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  cardBg: 'rgba(255, 255, 255, 0.95)',
  text: '#2d3748',
  textSecondary: '#718096',
  primary: '#4299e1',
  primaryHover: '#3182ce',
  success: '#48bb78',
  error: '#f56565',
  danger: '#e53e3e',
  border: 'rgba(255, 255, 255, 0.2)',
  shadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
};

const darkTheme = {
  background: 'linear-gradient(135deg, #1a202c 0%, #2d3748 100%)',
  cardBg: 'rgba(45, 55, 72, 0.95)',
  text: '#f7fafc',
  textSecondary: '#a0aec0',
  primary: '#63b3ed',
  primaryHover: '#4299e1',
  success: '#68d391',
  error: '#fc8181',
  danger: '#fc8181',
  border: 'rgba(255, 255, 255, 0.1)',
  shadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
};

// Professional Loading Animation Component
const DiagnosisLoadingOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  color: white;
`;

const LoadingContainer = styled.div`
  text-align: center;
  padding: 3rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
`;

const LoadingSpinner = styled.div`
  width: 80px;
  height: 80px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top: 4px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 2rem;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const LoadingText = styled.h2`
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: white;
`;

const LoadingSubtext = styled.p`
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 1rem;
`;

const LoadingProgress = styled.div`
  width: 300px;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  margin: 1rem auto;
  overflow: hidden;
`;

const LoadingProgressBar = styled.div`
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #81C784);
  border-radius: 3px;
  animation: progress 2s ease-in-out infinite;
  
  @keyframes progress {
    0% { width: 0%; }
    50% { width: 75%; }
    100% { width: 100%; }
  }
`;

const LoadingSteps = styled.div`
  text-align: left;
  margin-top: 2rem;
`;

const LoadingStep = styled.div`
  display: flex;
  align-items: center;
  margin: 0.5rem 0;
  color: ${props => props.$active ? '#4CAF50' : 'rgba(255, 255, 255, 0.6)'};
  
  .icon {
    margin-right: 1rem;
    width: 20px;
  }
`;

// Professional Loading Component
const DiagnosisLoading = ({ stage, message }) => {
  const stages = [
    { id: 'analyzing', icon: '🧠', text: 'Analyzing symptoms and medical data...' },
    { id: 'generating', icon: '📝', text: 'Generating comprehensive diagnosis...' },
    { id: 'audio', icon: '🎵', text: 'Creating audio response...' },
    { id: 'finalizing', icon: '✅', text: 'Finalizing diagnosis...' }
  ];

  return (
    <DiagnosisLoadingOverlay>
      <LoadingContainer>
        <LoadingSpinner />
        <LoadingText>🩺 AI Doctor is Working</LoadingText>
        <LoadingSubtext>{message}</LoadingSubtext>
        <LoadingProgress>
          <LoadingProgressBar />
        </LoadingProgress>
        <LoadingSteps>
          {stages.map((s, index) => (
            <LoadingStep key={s.id} $active={stages.findIndex(st => st.id === stage) >= index}>
              <span className="icon">{s.icon}</span>
              <span>{s.text}</span>
            </LoadingStep>
          ))}
        </LoadingSteps>
      </LoadingContainer>
    </DiagnosisLoadingOverlay>
  );
};

// Global Styles
const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: ${props => props.theme.background};
    color: ${props => props.theme.text};
    line-height: 1.6;
    overflow-x: hidden;
  }
`;

// Enhanced Audio Player Component - Simplified and Robust
const AudioPlayer = ({ audioUrl, autoPlay = false }) => {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [audioError, setAudioError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const speedOptions = [0.5, 0.75, 1, 1.25, 1.5, 2];

  // Close speed menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showSpeedMenu && !event.target.closest('[data-speed-control]')) {
        setShowSpeedMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showSpeedMenu]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !audioUrl) return;

    setIsLoading(true);
    setAudioError(null);

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        setDuration(audio.duration);
        setIsLoading(false);
        console.log(`🎵 Audio ready - Duration: ${audio.duration.toFixed(1)}s`);
      }
    };
    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };
    const handleError = (e) => {
      console.error('🎵 Audio loading error:', e);
      const errorMsg = audio.error ? 
        `Audio error: ${audio.error.code} - ${audio.error.message}` : 
        'Failed to load audio file';
      setAudioError(errorMsg);
      setIsLoading(false);
      setIsPlaying(false);
    };
    const handleCanPlay = () => {
      setIsLoading(false);
      setAudioError(null);
      console.log('🎵 Audio can play');
    };

    // Add event listeners
    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);
    audio.addEventListener('canplay', handleCanPlay);

    // Enhanced loading with retry mechanism
    const loadAudio = async (retryCount = 0) => {
      try {
        console.log(`🎵 Loading audio attempt ${retryCount + 1}: ${audioUrl}`);
        
        // Add cache-busting parameter to ensure fresh request
        const urlWithCacheBust = `${audioUrl}${audioUrl.includes('?') ? '&' : '?'}t=${Date.now()}`;
        audio.src = urlWithCacheBust;
        
        // Wait for the audio to load
        await new Promise((resolve, reject) => {
          const loadTimeout = setTimeout(() => {
            reject(new Error('Audio load timeout'));
          }, 15000); // 15 second timeout
          
          const onLoad = () => {
            clearTimeout(loadTimeout);
            audio.removeEventListener('canplaythrough', onLoad);
            audio.removeEventListener('error', onError);
            resolve();
          };
          
          const onError = (e) => {
            clearTimeout(loadTimeout);
            audio.removeEventListener('canplaythrough', onLoad);
            audio.removeEventListener('error', onError);
            reject(e);
          };
          
          audio.addEventListener('canplaythrough', onLoad);
          audio.addEventListener('error', onError);
          audio.load();
        });
        
        console.log('🎵 Audio loaded successfully');
        
        // Auto-play with improved timing
        if (autoPlay) {
          await attemptAutoPlay();
        }
        
      } catch (error) {
        console.error(`🎵 Audio load attempt ${retryCount + 1} failed:`, error);
        
        if (retryCount < 2) { // Retry up to 3 times
          console.log(`🎵 Retrying audio load in 2 seconds...`);
          setTimeout(() => loadAudio(retryCount + 1), 2000);
        } else {
          setAudioError(`Failed to load audio after 3 attempts: ${error.message}`);
          setIsLoading(false);
        }
      }
    };

    const attemptAutoPlay = async () => {
      try {
        await audio.play();
        setIsPlaying(true);
        console.log('🎵 Autoplay successful!');
      } catch (error) {
        console.log('🎵 Autoplay failed (browser policy):', error.message);
        // Autoplay failure is normal due to browser policies
      }
    };

    // Start loading with initial delay to allow server processing
    setTimeout(() => loadAudio(), 1500);

    // Cleanup
    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('canplay', handleCanPlay);
    };
  }, [audioUrl, autoPlay]);

  const togglePlayPause = async () => {
    const audio = audioRef.current;
    if (!audio || audioError) return;

    try {
      if (isPlaying) {
        audio.pause();
        setIsPlaying(false);
        console.log('🎵 Audio paused');
      } else {
        // Reset if ended
        if (audio.ended) {
          audio.currentTime = 0;
        }
        
        await audio.play();
        setIsPlaying(true);
        console.log('🎵 Audio playing');
      }
    } catch (error) {
      console.error('🎵 Play/pause failed:', error);
      setIsPlaying(false);
      
      if (error.name === 'NotAllowedError') {
        alert('Audio playback blocked by browser. Please click play again.');
      } else {
        alert(`Audio playback failed: ${error.message}`);
      }
    }
  };

  const handleSeek = (e) => {
    const audio = audioRef.current;
    if (!audio || !duration || audioError) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    audio.currentTime = percent * duration;
  };

  const changeSpeed = (speed) => {
    const audio = audioRef.current;
    if (!audio || audioError) return;
    
    try {
      audio.playbackRate = speed;
      setPlaybackSpeed(speed);
      setShowSpeedMenu(false);
      console.log(`🎵 Playback speed changed to: ${speed}x`);
    } catch (error) {
      console.error('🎵 Speed change failed:', error);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <AudioContainer>
      <audio 
        ref={audioRef} 
        preload="metadata" 
        style={{ display: 'none' }}
        crossOrigin="anonymous"
      />
      
      {/* Error Display */}
      {audioError && (
        <ErrorDisplay>
          ❌ Audio Error: {audioError}
          <button 
            onClick={() => {
              setAudioError(null);
              setIsLoading(true);
              // Retry loading the audio
              if (audioRef.current && audioUrl) {
                audioRef.current.src = audioUrl + '?retry=' + Date.now();
                audioRef.current.load();
              }
            }}
            style={{
              marginLeft: '10px',
              background: '#f56565',
              color: 'white',
              border: 'none',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            🔄 Retry
          </button>
          <button 
            onClick={() => {
              if (audioUrl) {
                openExternal(audioUrl);
              }
            }}
            style={{
              marginLeft: '5px',
              background: '#4299e1',
              color: 'white',
              border: 'none',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            🔗 Test URL
          </button>
        </ErrorDisplay>
      )}
      
      {/* Loading Indicator */}
      {isLoading && !audioError && (
        <div style={{ padding: '10px', textAlign: 'center', color: '#666' }}>
          🔄 Loading audio...
        </div>
      )}
      
      {/* Audio Controls */}
      <Controls>
        <PlayButton 
          onClick={togglePlayPause} 
          disabled={!audioUrl || isLoading || audioError}
          title={
            audioError ? `Error: ${audioError}` :
            isLoading ? 'Loading...' :
            isPlaying ? 'Pause' : 'Play'
          }
        >
          {isLoading ? '⏳' : isPlaying ? <FaPause /> : <FaPlay />}
        </PlayButton>

        <ProgressBar onClick={handleSeek} disabled={!duration || audioError}>
          <Progress style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }} />
        </ProgressBar>

        <TimeDisplay>
          {formatTime(currentTime)} / {formatTime(duration)}
        </TimeDisplay>

        <SpeedControl data-speed-control>
          <SpeedButton onClick={() => setShowSpeedMenu(!showSpeedMenu)} disabled={audioError}>
            <FaTachometerAlt />
            <span>{playbackSpeed}x</span>
          </SpeedButton>
          
          {showSpeedMenu && (
            <SpeedMenu>
              {speedOptions.map(speed => (
                <SpeedOption 
                  key={speed}
                  onClick={() => changeSpeed(speed)}
                  $active={speed === playbackSpeed}
                >
                  {speed}x
                </SpeedOption>
              ))}
            </SpeedMenu>
          )}
        </SpeedControl>
      </Controls>
    </AudioContainer>
  );
};

function App() {
  // Main State
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [language, setLanguage] = useState('');
  const [showLanguageSelector, setShowLanguageSelector] = useState(true);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [apiStatus, setApiStatus] = useState('checking');
  const [computeMode, setComputeMode] = useState('auto'); // 'auto' | 'offline' | 'online'
  const [sttHealth, setSttHealth] = useState(null);
  
  // New Loading States for Professional Animation
  const [isGeneratingDiagnosis, setIsGeneratingDiagnosis] = useState(false);
  const [loadingStage, setLoadingStage] = useState('analyzing');
  const [loadingMessage, setLoadingMessage] = useState('');
  
  // Audio States
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  // Text Input States
  const [textInput, setTextInput] = useState('');
  const [vitalSigns, setVitalSigns] = useState('');
  
  // File States
  const [medicalFiles, setMedicalFiles] = useState([]);
  const [filePreviews, setFilePreviews] = useState([]);

  // Location States
  const [showLocationPrompt, setShowLocationPrompt] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [locationPermissionGranted, setLocationPermissionGranted] = useState(false);
  
  // Doctor Recommendation States
  const [specialistRecommendation, setSpecialistRecommendation] = useState(null);
  const [urgencyLevel, setUrgencyLevel] = useState(null);
  const [fairnessMetrics, setFairnessMetrics] = useState(null);
  const [showDoctorRecommendations, setShowDoctorRecommendations] = useState(false);
  const [showFindDoctorsButton, setShowFindDoctorsButton] = useState(false);
  
  // Modal States
  const [showAboutSection, setShowAboutSection] = useState(false);
  const [showAyushmanCard, setShowAyushmanCard] = useState(false);

  const t = TRANSLATIONS[language] || TRANSLATIONS['en'];
  const theme = isDarkMode ? darkTheme : lightTheme;

  const [isOnline, setIsOnline] = useState(navigator.onLine);
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Compute Mode Auto Toggle
  useEffect(() => {
    if (computeMode === 'auto' && !isOnline) {
      setComputeMode('offline');
    }
  }, [isOnline, computeMode]);

  // API Connection Check: poll until the backend answers; one loop per
  // language selection, cancelled when the language changes or on unmount.
  useEffect(() => {
    if (!language) return undefined;
    let cancelled = false;
    let retryTimer = null;

    const checkSttHealth = async () => {
      try {
        const response = await axios.get(apiUrl('/api/stt-health'), { timeout: 30000 });
        if (!cancelled) setSttHealth(response.data);
      } catch (error) {
        console.error('STT health check failed:', error);
        if (!cancelled) setSttHealth({ ready: false, error: error.message });
      }
    };

    const checkApiConnection = async () => {
      try {
        const response = await axios.get(apiUrl('/api'), { timeout: 10000 });
        if (!cancelled && response.status === 200) {
          setApiStatus('connected');
          checkSttHealth();
        }
      } catch (error) {
        if (cancelled) return;
        console.error('API connection failed:', error);
        setApiStatus('error');
        retryTimer = setTimeout(checkApiConnection, 5000);
      }
    };

    checkApiConnection();
    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
    };
  }, [language]);

  // Language Selection
  const handleLanguageSelect = (selectedLang) => {
    setLanguage(selectedLang);
    setShowLanguageSelector(false);
    setShowDisclaimer(true); // Show disclaimer after language selection
  };
  
  // Disclaimer Acceptance
  const handleDisclaimerAccept = () => {
    setShowDisclaimer(false);
  };

  // Audio Recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.push(event.data);
      };
      
      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        setRecordedAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
        await transcribeAudio(audioBlob);
      };
      
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error('Recording failed:', error);
      const permissionMessages = {
        en: 'Could not access microphone. Please grant permission.',
        hi: 'माइक्रोफोन एक्सेस नहीं हो सका। कृपया अनुमति दें।',
        mr: 'मायक्रोफोन वापरता आला नाही. कृपया परवानगी द्या.',
      };
      alert(permissionMessages[language] || permissionMessages.en);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Audio Transcription
  const transcribeAudio = async (audioBlob) => {
    setIsTranscribing(true);
    try {
      const formData = new FormData();
      const webmFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
      formData.append('audio', webmFile);
      formData.append('language', language);

      const response = await axios.post(apiUrl('/api/transcribe-audio'), formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setTranscription(response.data.text);
    } catch (error) {
      console.error('Transcription failed:', error);
      const detail = error.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : 'Failed to transcribe audio. Please try again.');
      setRecordedAudio(null);
    } finally {
      setIsTranscribing(false);
    }
  };

  // File Upload
  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    const maxFiles = 8;
    
    if (medicalFiles.length + files.length > maxFiles) {
      alert(t.max_files_reached);
      return;
    }
    
    const validFiles = files.filter(file => {
      return file.type.startsWith('image/') || file.type === 'application/pdf';
    });
    
    if (validFiles.length !== files.length) {
      alert('Please select only image files (JPG, PNG) or PDF files.');
      return;
    }
    
    setMedicalFiles(prev => [...prev, ...validFiles]);
    
    // Generate previews
    validFiles.forEach((file) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = () => {
          setFilePreviews(prev => [...prev, {
            type: 'image',
            name: file.name,
            url: reader.result,
            size: (file.size / 1024 / 1024).toFixed(2) + ' MB'
          }]);
        };
        reader.readAsDataURL(file);
      } else {
        setFilePreviews(prev => [...prev, {
          type: 'pdf',
          name: file.name,
          size: (file.size / 1024 / 1024).toFixed(2) + ' MB'
        }]);
      }
    });
  };

  const removeFile = (index) => {
    setMedicalFiles(prev => prev.filter((_, i) => i !== index));
    setFilePreviews(prev => prev.filter((_, i) => i !== index));
  };

  // Submit Consultation
  // Poll for audio file readiness (optimized for speed)
  const pollAudioStatus = async (filename, maxAttempts = 20) => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await axios.get(apiUrl(`/api/audio-status/${filename}`));
        
        if (response.data.ready) {
          console.log(`🎵 Audio ready after ${attempt + 1} attempts, size: ${response.data.file_size} bytes`);
          return true;
        }
        
        console.log(`🎵 Audio not ready, attempt ${attempt + 1}/${maxAttempts}, status: ${response.data.status}`);
        
        // Faster polling - shorter wait times
        const waitTime = attempt < 5 ? 500 : 800; // Start with 500ms, then 800ms
        await new Promise(resolve => setTimeout(resolve, waitTime));
      } catch (error) {
        console.log(`🎵 Audio status check failed, attempt ${attempt + 1}:`, error.message);
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    
    console.log('🎵 Audio polling timeout - proceeding anyway');
    return false;
  };

  const handleSubmit = async () => {
    // Check if we have either audio transcription or text input
    let patientText = transcription || textInput;
    if (!patientText) {
      return;
    }
    
    // Append vital signs if provided
    if (vitalSigns.trim()) {
      patientText += `\n\n[Vital Signs]: ${vitalSigns}`;
    }
    
    setIsGeneratingDiagnosis(true);
    setLoadingStage('analyzing');
    setLoadingMessage('Processing your symptoms and medical data...');
    
    try {
      // Stage 1: Analyzing
      setLoadingStage('analyzing');
      setLoadingMessage('AI Doctor is analyzing your symptoms and medical files...');
      
      // Process files
      const imageDataList = [];
      const pdfDataList = [];
      
      for (const file of medicalFiles) {
        const reader = new FileReader();
        const fileData = await new Promise((resolve) => {
          reader.onload = () => resolve(reader.result.split(',')[1]);
          reader.readAsDataURL(file);
        });
        
        if (file.type.startsWith('image/')) {
          imageDataList.push(fileData);
        } else if (file.type === 'application/pdf') {
          pdfDataList.push({ name: file.name, data: fileData });
        }
      }

      // Stage 2: Generating diagnosis
      setLoadingStage('generating');
      setLoadingMessage('Generating comprehensive medical diagnosis...');

      // Brief pause to show the stage change
      await new Promise(resolve => setTimeout(resolve, 200));

      // DEMO INTERCEPT: disabled — all queries now route to live Gemma4 backend
      // const demoHit = matchDemoQuery(patientText, language);
      // if (demoHit) { ... }

      // Send to API
      const response = await axios.post(apiUrl('/api/get-doctor-response'), {
        patient_text: patientText,
        typed_text: textInput || null,
        transcription_text: transcription || null,
        language: language,
        image_data: imageDataList,
        pdf_data: pdfDataList,
        image_count: imageDataList.length,
        pdf_count: pdfDataList.length,
        execution_mode: computeMode === 'auto' ? null : computeMode,
      }, {
        headers: { 'Content-Type': 'application/json' },
        timeout: 120000 // Increased timeout for longer generation
      });

      if (response.data?.doctor_response) {
        // Extract specialist recommendation and urgency level
        const specialistRec = response.data.specialist_recommendation || 'general';
        const urgency = response.data.urgency_level || 'low';
        const fairnessData = response.data.fairness_metrics || null;
        
        console.log('🔍 Raw API response specialist_recommendation:', response.data.specialist_recommendation);
        console.log('🔍 Processed specialistRec:', specialistRec);
        
        setSpecialistRecommendation(specialistRec);
        setUrgencyLevel(urgency);
        setFairnessMetrics(fairnessData);
        
        console.log('🩺 Specialist recommendation:', specialistRec);
        console.log('⚡ Urgency level:', urgency);
        
        // Stage 3: Waiting for audio
        setLoadingStage('audio');
        setLoadingMessage('Generating high-quality audio response...');
        
        let finalAudioUrl = null;
        
        if (response.data.audio_url) {
          // Extract filename from URL for polling
          const audioPath = response.data.audio_url.startsWith('/') 
            ? response.data.audio_url 
            : `/${response.data.audio_url}`;
          const filename = audioPath.split('/').pop();
          
          console.log('🎵 Starting audio polling for:', filename);
          
          // Wait for audio to be fully generated
          const audioReady = await pollAudioStatus(filename);
          
          if (audioReady) {
            finalAudioUrl = apiUrl(audioPath);
            console.log('🎵 Audio URL constructed:', finalAudioUrl);
          } else {
            console.log('⚠️ Audio polling timeout, but proceeding with URL');
            finalAudioUrl = apiUrl(audioPath);
          }
        } else {
          console.log('⚠️ No audio_url received from API');
        }

        // Stage 4: Finalizing
        setLoadingStage('finalizing');
        setLoadingMessage('Finalizing diagnosis presentation...');
        
        // Quick finalization
        await new Promise(resolve => setTimeout(resolve, 300));

        const doctorMessage = {
          type: 'doctor',
          content: response.data.doctor_response,
          timestamp: new Date().toLocaleTimeString(),
          audioUrl: finalAudioUrl,
          autoPlay: true,
          specialistRecommendation: specialistRec,
          urgencyLevel: urgency,
          fairnessMetrics: fairnessData
        };
        
        setConversation(prev => [...prev, doctorMessage]);
        
        // Show find doctors button if specialist recommended (including general practitioners)
        if (specialistRec && specialistRec.trim() !== '') {
          console.log('🔘 Setting showFindDoctorsButton to true for specialist:', specialistRec);
          setShowFindDoctorsButton(true);
        } else {
          console.log('🔘 Not showing find doctors button - no specialist recommendation');
        }
      }
      
    } catch (error) {
      console.error('Consultation error:', error);
      
      const errorMessage = {
        type: 'error',
        // The server sends a localized, patient-safe explanation in `detail`.
        content: typeof error.response?.data?.detail === 'string' ? error.response.data.detail : `Error: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setIsGeneratingDiagnosis(false);
      setLoadingStage('analyzing');
      setLoadingMessage('');
    }
  };

  // Reset Everything (but preserve location)
  const resetConsultation = () => {
    setConversation([]);
    setRecordedAudio(null);
    setTranscription('');
    setTextInput('');
    setMedicalFiles([]);
    setFilePreviews([]);
    setSpecialistRecommendation(null);
    setUrgencyLevel(null);
    setFairnessMetrics(null);
    setShowDoctorRecommendations(false);
    setShowFindDoctorsButton(false);
    // Reset location states so user has to grant permission again
    setUserLocation(null);
    setLocationPermissionGranted(false);
    setShowLocationPrompt(false);
  };

  const formatParityMetric = (value) => {
    if (typeof value !== 'number' || Number.isNaN(value)) {
      return 'N/A';
    }
    return `${(value * 100).toFixed(1)}%`;
  };

  // Location Permission Handlers
  const handleLocationGranted = (location) => {
    console.log('📍 Location granted:', location);
    setUserLocation(location);
    setLocationPermissionGranted(true);
    setShowLocationPrompt(false);
    
    // Check if this was called from find doctors button
    if (showFindDoctorsButton) {
      // Show doctor recommendations after location is granted
      setTimeout(() => {
        setShowFindDoctorsButton(false);
        setShowDoctorRecommendations(true);
      }, 500);
    } else {
      // Original flow: proceed with diagnosis
      setTimeout(() => {
        handleSubmit();
      }, 500);
    }
  };

  const handleLocationDenied = () => {
    console.log('📍 Location permission denied');
    setLocationPermissionGranted(false);
    setShowLocationPrompt(false);
    
    // Check if this was called from find doctors button
    if (showFindDoctorsButton) {
      // Can't show doctors without location, keep the button
      alert('Location permission is required to find nearby doctors and hospitals.');
    } else {
      // Original flow: proceed with diagnosis without location
      setTimeout(() => {
        handleSubmit();
      }, 500);
    }
  };

  // Manual Doctor Search Handler
  const handleFindDoctors = () => {
    // Check if location permission is needed
    if (!locationPermissionGranted && !userLocation) {
      setShowLocationPrompt(true);
      return;
    }
    
    // If location is available, show doctor recommendations
    setShowFindDoctorsButton(false);
    setShowDoctorRecommendations(true);
  };

  // Utility Functions
  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('Copied to clipboard!');
    } catch (err) {
      console.error('Copy failed:', err);
    }
  };

  const downloadAudio = async (audioUrl, timestamp) => {
    try {
      const response = await fetch(audioUrl);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `doctor-response-${timestamp.replace(/:/g, '-')}.wav`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const downloadTranscription = () => {
    if (!transcription) return;
    const blob = new Blob([transcription], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcription-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Language Selection Screen
  if (showLanguageSelector) {
    return (
      <ThemeProvider theme={theme}>
        <GlobalStyle />
        <LanguageScreen>
          <LanguageCard>
            <Logo>
              <FaStethoscope size={48} />
              <h1>HealStation AI</h1>
            </Logo>
            
            <LanguageTitle>🌐 Select Language / भाषा चुनें / भाषा निवडा</LanguageTitle>
            
            <LanguageButtons>
              <LanguageButton onClick={() => handleLanguageSelect('en')}>
                🇬🇧 English
              </LanguageButton>
              <LanguageButton onClick={() => handleLanguageSelect('hi')}>
                🇮🇳 हिंदी (Hindi)
              </LanguageButton>
              <LanguageButton onClick={() => handleLanguageSelect('mr')}>
                🇮🇳 मराठी (Marathi)
              </LanguageButton>
            </LanguageButtons>

            {/* 🚨 Emergency Button - Quick access on language selection page */}
            <EmergencyButton 
              language={language} 
              showBanner={true} 
              showQuickActions={true}
            />
            
            <Disclaimer>
              ⚠️ This AI tool is for educational purposes only. Always consult a qualified healthcare professional.
            </Disclaimer>
          </LanguageCard>
        </LanguageScreen>
      </ThemeProvider>
    );
  }

  // Main App
  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <AppContainer>
        {/* Header */}
        <Header>
          <Logo>
            <FaStethoscope size={32} />
            <div>
              <h1>{t.header}</h1>
              <p>{t.subheader}</p>
            </div>
          </Logo>
          
          <HeaderControls>
            <LanguageSelect>
              <FaGlobe />
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="en">English</option>
                <option value="hi">हिंदी</option>
                <option value="mr">मराठी</option>
              </select>
            </LanguageSelect>
            
            <StatusBadge
              $connected={apiStatus === 'connected'}
              title={apiStatus === 'connected' ? 'Local AI server connected' : 'Cannot reach the local AI server'}
            >
              {apiStatus === 'connected'
                ? (isOnline ? '🟢 Local AI ready' : '🟢 Local AI ready (no internet)')
                : apiStatus === 'checking' ? '⏳ Connecting...' : '🔴 AI server unreachable'}
            </StatusBadge>

            <StatusBadge
              $connected={Boolean(sttHealth?.ready)}
              title={sttHealth?.error ? `STT Error: ${sttHealth.error}` : sttHealth?.ready ? `Offline STT ready (${sttHealth.model}, ${sttHealth.device})` : 'Checking STT...'}
            >
              {sttHealth === null
                ? '🎙️ STT...'
                : sttHealth.ready
                ? `🎙️ STT: Offline`
                : `🎙️ STT Error`}
            </StatusBadge>

            {/* Compute Mode Toggle */}
            <select
              id="compute-mode-select"
              value={computeMode}
              onChange={(e) => setComputeMode(e.target.value)}
              title="Choose compute tier for AI diagnosis"
              style={{
                background: computeMode === 'offline'
                  ? 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)'
                  : computeMode === 'online'
                  ? 'linear-gradient(135deg, #0f3460 0%, #533483 100%)'
                  : 'linear-gradient(135deg, #2d5016 0%, #1a3a0a 100%)',
                color: '#e0e0e0',
                border: '1px solid rgba(255,255,255,0.25)',
                borderRadius: '8px',
                padding: '6px 10px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                outline: 'none',
                letterSpacing: '0.3px',
              }}
            >
              {/* <option value="auto">⚡ Auto (Gemma → Cloud)</option> */}
              <option value="offline">🔒 Offline (Gemma 4 )</option>
              {/* <option value="online">☁️ Online (Cloud Tier)</option> */}
            </select>
            
            <AboutButton onClick={() => setShowAboutSection(true)}>
              <FaInfoCircle /> About
            </AboutButton>
            
            <AyushmanButton onClick={() => setShowAyushmanCard(true)}>
              <FaHeart /> {t.ayushman_button}
            </AyushmanButton>
            
            <ThemeButton onClick={() => setIsDarkMode(!isDarkMode)}>
              {isDarkMode ? <FaSun /> : <FaMoon />}
            </ThemeButton>
          </HeaderControls>
        </Header>

        {/* Main Content */}
        <MainContent>
          {/* Patient Panel */}
          <Panel>
            <PanelHeader>
              <FaUser size={24} />
              <div>
                <h2>{t.patient_panel}</h2>
                <p>{t.patient_desc}</p>
              </div>
            </PanelHeader>

            <PanelContent>
              {/* Step 1: Audio Recording */}
              <Section>
                <SectionTitle>{t.step1_title}</SectionTitle>
                <SectionDesc>{t.step1_desc}</SectionDesc>
                
                <RecordingArea>
                  <RecordButton 
                    onClick={toggleRecording}
                    $recording={isRecording}
                    disabled={isGeneratingDiagnosis || isTranscribing}
                  >
                    {isRecording ? <FaStop size={24} /> : <FaMicrophone size={24} />}
                  </RecordButton>
                  
                  <Status>
                    {isTranscribing ? (
                      <span style={{color: theme.primary}}>🔄 {t.transcribing_audio}</span>
                    ) : recordedAudio ? (
                      <span style={{color: theme.success}}>✅ {t.audio_recorded}</span>
                    ) : textInput ? (
                      <span style={{color: theme.success}}>✅ Text input provided</span>
                    ) : (
                      <span style={{color: theme.error}}>🎤 {t.text_required}</span>
                    )}
                  </Status>
                  
                  {recordedAudio && (
                    <ButtonGroup>
                      <SmallButton onClick={resetConsultation}>
                        <FaTrash /> {t.clear_recording}
                      </SmallButton>
                      {transcription && (
                        <SmallButton onClick={downloadTranscription}>
                          <FaDownload /> {t.download_transcription}
                        </SmallButton>
                      )}
                    </ButtonGroup>
                  )}
                  
                  {transcription && (
                    <TranscriptionBox>
                      <strong>{t.transcription_label}</strong>
                      <p>{transcription}</p>
                    </TranscriptionBox>
                  )}
                </RecordingArea>
              </Section>

              {/* Step 1b: Text Input Alternative */}
              <Section>
                <SectionTitle>{t.step1_text_title}</SectionTitle>
                <SectionDesc>{t.step1_text_desc}</SectionDesc>
                
                <TextInputArea>
                  <TextInputBox
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder={t.text_input_placeholder}
                    disabled={isGeneratingDiagnosis}
                    rows={4}
                  />
                  
                  <Status>
                    {textInput ? (
                      <span style={{color: theme.success}}>✅ {t.text_input_label} {textInput.length} characters</span>
                    ) : (
                      <span style={{color: theme.textSecondary}}>📝 {t.text_required}</span>
                    )}
                  </Status>
                  
                  {textInput && (
                    <ButtonGroup>
                      <SmallButton onClick={() => setTextInput('')}>
                        <FaTrash /> Clear Text
                      </SmallButton>
                      <SmallButton onClick={() => copyToClipboard(textInput)}>
                        <FaCopy /> Copy Text
                      </SmallButton>
                    </ButtonGroup>
                  )}
                </TextInputArea>
                
                {/* Vital Signs Input - Optional */}
                <VitalSignsInput>
                  <label>💊 Vital Signs (Optional):</label>
                  <input
                    type="text"
                    value={vitalSigns}
                    onChange={(e) => setVitalSigns(e.target.value)}
                    placeholder="e.g., BP: 140/90, Heart Rate: 85 bpm, Temp: 101°F, Oxygen: 96%"
                    disabled={isGeneratingDiagnosis}
                  />
                  <small>
                    ℹ️ If available, include blood pressure, heart rate, temperature, oxygen saturation, etc.
                  </small>
                </VitalSignsInput>
              </Section>

              {/* Step 2: File Upload */}
              <Section>
                <SectionTitle>{t.step2_title}</SectionTitle>
                <SectionDesc>{t.step2_desc}</SectionDesc>
                
                <UploadArea>
                  <UploadZone>
                    <input
                      type="file"
                      accept="image/*,application/pdf"
                      multiple
                      onChange={handleFileUpload}
                      id="file-upload"
                      disabled={medicalFiles.length >= 8}
                    />
                    <label htmlFor="file-upload">
                      <FaUpload size={32} />
                      <span>{t.upload_medical_files}</span>
                      <small>{medicalFiles.length}/8 files</small>
                    </label>
                  </UploadZone>
                  
                  <Status>
                    {medicalFiles.length === 0 ? (
                      <span style={{color: theme.textSecondary}}>📷 {t.files_optional}</span>
                    ) : (
                      <span style={{color: theme.success}}>✅ {medicalFiles.length} {t.files_uploaded}</span>
                    )}
                  </Status>
                </UploadArea>
                
                {filePreviews.length > 0 && (
                  <FileGrid>
                    {filePreviews.map((preview, index) => (
                      <FileCard key={index}>
                        <FilePreview>
                          {preview.type === 'image' ? (
                            <img src={preview.url} alt={`File ${index + 1}`} />
                          ) : (
                            <FaFilePdf size={32} color="#dc3545" />
                          )}
                        </FilePreview>
                        <FileInfo>
                          <FileName>{preview.name}</FileName>
                          <FileSize>{preview.size}</FileSize>
                        </FileInfo>
                        <RemoveButton onClick={() => removeFile(index)}>
                          ×
                        </RemoveButton>
                      </FileCard>
                    ))}
                  </FileGrid>
                )}
              </Section>

              {/* Step 3: Diagnosis */}
              <Section>
                <SectionTitle>{t.step3_title}</SectionTitle>
                
                {/* Recommendation for better analysis */}
                {(transcription || textInput) && medicalFiles.length === 0 && (
                  <RecommendationBox>
                    <strong>{t.recommendation_title}</strong>
                    <p>{t.recommendation_text}</p>
                  </RecommendationBox>
                )}
                
                <DiagnosisButton
                  onClick={handleSubmit}
                  disabled={isGeneratingDiagnosis || isTranscribing || (!transcription && !textInput)}
                  $ready={(transcription || textInput) && !isGeneratingDiagnosis}
                >
                  {isGeneratingDiagnosis ? (
                    <>
                      <Spinner />
                      Processing...
                    </>
                  ) : (
                    <>
                      <FaHeartbeat />
                      {t.diagnosis_button}
                    </>
                  )}
                </DiagnosisButton>
              </Section>
            </PanelContent>
          </Panel>

          {/* Doctor Panel */}
          <Panel>
            <PanelHeader>
              <FaUserMd size={24} />
              <div>
                <h2>{t.doctor_panel}</h2>
                <p>{t.doctor_desc}</p>
              </div>
            </PanelHeader>

            <PanelContent>
              {conversation.length === 0 ? (
                <WelcomeScreen>
                  <FaStethoscope size={64} />
                  <h1>{t.header}</h1>
                  <div style={{
                    background: 'rgba(99,179,237,0.08)',
                    border: '1px solid rgba(99,179,237,0.25)',
                    borderRadius: '12px',
                    padding: '0.85rem 1.25rem',
                    margin: '0.75rem 0 1rem',
                    textAlign: 'left',
                    lineHeight: '2',
                    fontSize: '0.88rem',
                    letterSpacing: '0.01em',
                  }}>
                    🔒 No data leaves this device<br/>
                    🌐 EN | हिंदी | मराठी<br/>
                    📡 Fully Offline — Gemma 4
                  </div>
                  <CheckList>
                    <CheckItem style={{color: recordedAudio ? theme.success : theme.error}}>
                      {recordedAudio ? '✅' : '⏳'} {t.record_required}
                    </CheckItem>
                    <CheckItem style={{color: medicalFiles.length > 0 ? theme.success : theme.error}}>
                      {medicalFiles.length > 0 ? '✅' : '⏳'} {t.files_required}
                    </CheckItem>
                  </CheckList>
                </WelcomeScreen>
              ) : (
                <ConversationArea>
                  {conversation.map((message, index) => (
                    <MessageCard key={index}>
                      {message.type === 'doctor' && (
                        <DoctorMessage>
                          <MessageHeader>
                            <FaUserMd />
                            <h4>{t.analysis_title}</h4>
                            <Timestamp>{message.timestamp}</Timestamp>
                          </MessageHeader>
                          
                          {/* Urgency Banner */}
                          {urgencyLevel && (
                            <UrgencyBanner $urgency={urgencyLevel}>
                              {urgencyLevel === 'high' && (
                                <>
                                  🚨 <strong>HIGH URGENCY:</strong> Seek immediate medical attention. Visit emergency room or call emergency services if symptoms worsen.
                                </>
                              )}
                              {urgencyLevel === 'medium' && (
                                <>
                                  ⚠️ <strong>MEDIUM URGENCY:</strong> Consult with a specialist within 24-48 hours. Monitor symptoms closely.
                                </>
                              )}
                              {urgencyLevel === 'low' && (
                                <>
                                  ✅ <strong>LOW URGENCY:</strong> Routine consultation recommended. Schedule appointment at your convenience.
                                </>
                              )}
                            </UrgencyBanner>
                          )}

                          {(message.fairnessMetrics || fairnessMetrics) && (
                            <FairnessWidget>
                              <FairnessHeaderRow>
                                <strong>Fairness Metrics</strong>
                                <FairnessBadge
                                  $status={(message.fairnessMetrics || fairnessMetrics).fairness_status || 'Review ⚠️'}
                                >
                                  {(message.fairnessMetrics || fairnessMetrics).fairness_status || 'Review ⚠️'}
                                </FairnessBadge>
                              </FairnessHeaderRow>
                              <FairnessMeta>
                                Parity Score: {formatParityMetric((message.fairnessMetrics || fairnessMetrics).parity_score)}
                                {' | '}
                                Threshold: {formatParityMetric((message.fairnessMetrics || fairnessMetrics).parity_threshold)}
                              </FairnessMeta>
                              <FairnessRow>
                                <span>Age Accuracy</span>
                                <span>
                                  {Object.entries(((message.fairnessMetrics || fairnessMetrics).group_accuracy || {}).age || {})
                                    .map(([group, value]) => `${group}: ${formatParityMetric(value)}`)
                                    .join(' | ') || 'N/A'}
                                </span>
                              </FairnessRow>
                              <FairnessRow>
                                <span>Gender Accuracy</span>
                                <span>
                                  {Object.entries(((message.fairnessMetrics || fairnessMetrics).group_accuracy || {}).gender || {})
                                    .map(([group, value]) => `${group}: ${formatParityMetric(value)}`)
                                    .join(' | ') || 'N/A'}
                                </span>
                              </FairnessRow>
                              <FairnessRow>
                                <span>Language Accuracy</span>
                                <span>
                                  {Object.entries(((message.fairnessMetrics || fairnessMetrics).group_accuracy || {}).language || {})
                                    .map(([group, value]) => `${group}: ${formatParityMetric(value)}`)
                                    .join(' | ') || 'N/A'}
                                </span>
                              </FairnessRow>
                              <FairnessRow>
                                <span>Age Confidence</span>
                                <span>
                                  {Object.entries(((message.fairnessMetrics || fairnessMetrics).confidence_parity || {}).age || {})
                                    .map(([group, value]) => `${group}: ${formatParityMetric(value)}`)
                                    .join(' | ') || 'N/A'}
                                </span>
                              </FairnessRow>
                              <FairnessRow>
                                <span>Gender Confidence</span>
                                <span>
                                  {Object.entries(((message.fairnessMetrics || fairnessMetrics).confidence_parity || {}).gender || {})
                                    .map(([group, value]) => `${group}: ${formatParityMetric(value)}`)
                                    .join(' | ') || 'N/A'}
                                </span>
                              </FairnessRow>
                              <FairnessRow>
                                <span>Language Confidence</span>
                                <span>
                                  {Object.entries(((message.fairnessMetrics || fairnessMetrics).confidence_parity || {}).language || {})
                                    .map(([group, value]) => `${group}: ${formatParityMetric(value)}`)
                                    .join(' | ') || 'N/A'}
                                </span>
                              </FairnessRow>
                            </FairnessWidget>
                          )}
                           
                          <MessageContent>{message.content}</MessageContent>
                          
                          {message.audioUrl && (
                            <AudioSection>
                              <AudioLabel>🎵 {t.audio_title}</AudioLabel>
                              <AudioPlayer 
                                audioUrl={message.audioUrl} 
                                autoPlay={message.autoPlay}
                              />
                            </AudioSection>
                          )}
                          
                          <ActionButtons>
                            <ActionButton onClick={() => copyToClipboard(message.content)}>
                              <FaCopy /> {t.copy_text}
                            </ActionButton>
                            {message.audioUrl && (
                              <ActionButton onClick={() => downloadAudio(message.audioUrl, message.timestamp)}>
                                <FaDownload /> {t.download_audio}
                              </ActionButton>
                            )}
                          </ActionButtons>
                        </DoctorMessage>
                      )}
                      
                      {message.type === 'loading' && (
                        <LoadingMessage>
                          <Spinner />
                          {message.content}
                        </LoadingMessage>
                      )}
                      
                      {message.type === 'error' && (
                        <ErrorMessage>
                          ❌ {message.content}
                        </ErrorMessage>
                      )}
                    </MessageCard>
                  ))}
                </ConversationArea>
              )}
              
              {conversation.length > 0 && (
                <ResetButton onClick={resetConsultation}>
                  🔄 {t.reset_button}
                </ResetButton>
              )}
            </PanelContent>
          </Panel>
        </MainContent>

        {/* Footer */}
        <Footer>
          <p>© {new Date().getFullYear()} HealStation AI. {t.disclaimer}</p>
        </Footer>
        
        {/* Find Doctors Button */}
        {showFindDoctorsButton && (
          <FindDoctorsButtonContainer>
            <FindDoctorsButton onClick={handleFindDoctors}>
              {t.find_doctors_button}
            </FindDoctorsButton>
            <FindDoctorsDescription>
              {t.find_doctors_desc}
            </FindDoctorsDescription>
          </FindDoctorsButtonContainer>
        )}
        
        {/* Doctor Recommendations */}
        {showDoctorRecommendations && specialistRecommendation && userLocation && (
          <DoctorRecommendations
            userLocation={userLocation}
            recommendedSpecialty={specialistRecommendation}
            language={language}
          />
        )}
        
        {/* Professional Loading Overlay */}
        {isGeneratingDiagnosis && (
          <DiagnosisLoading 
            stage={loadingStage} 
            message={loadingMessage}
          />
        )}
        
        {/* Location Permission Modal */}
        {showLocationPrompt && (
          <LocationPermission
            onLocationGranted={handleLocationGranted}
            onLocationDenied={handleLocationDenied}
            language={language}
          />
        )}
        
        {/* About Section Modal */}
        {showAboutSection && (
          <AboutSection onClose={() => setShowAboutSection(false)} />
        )}
        
        {/* Ayushman Bharat Health Card Modal */}
        {showAyushmanCard && (
          <AyushmanBharatCard 
            onClose={() => setShowAyushmanCard(false)}
            language={language}
            translations={t}
          />
        )}
        
        {/* Disclaimer Modal - Shows after language selection */}
        {showDisclaimer && (
          <DisclaimerModal
            onAccept={handleDisclaimerAccept}
            language={language}
          />
        )}
      </AppContainer>
    </ThemeProvider>
  );
}

// Simplified Styled Components
const AppContainer = styled.div`
  min-height: 100vh;
  background: ${props => props.theme.background};
  display: flex;
  flex-direction: column;
`;

const Header = styled.header`
  background: ${props => props.theme.cardBg};
  border-bottom: 1px solid ${props => props.theme.border};
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: ${props => props.theme.shadow};
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  color: ${props => props.theme.primary};
  
  h1 { margin: 0; font-size: 1.2rem; }
  p { margin: 0; font-size: 0.9rem; color: ${props => props.theme.textSecondary}; }
`;

const HeaderControls = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const AboutButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.2rem;
  background: rgba(66, 153, 225, 0.15);
  border: 1px solid rgba(66, 153, 225, 0.3);
  border-radius: 12px;
  color: ${props => props.theme.text};
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(66, 153, 225, 0.25);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(66, 153, 225, 0.2);
  }
`;

const AyushmanButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.2rem;
  background: linear-gradient(135deg, rgba(255, 153, 51, 0.15), rgba(19, 136, 8, 0.15));
  border: 1px solid rgba(255, 153, 51, 0.3);
  border-radius: 12px;
  color: ${props => props.theme.text};
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: linear-gradient(135deg, rgba(255, 153, 51, 0.25), rgba(19, 136, 8, 0.25));
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 153, 51, 0.3);
  }
`;

const LanguageSelect = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  
  select {
    background: ${props => props.theme.cardBg};
    border: 1px solid ${props => props.theme.border};
    color: ${props => props.theme.text};
    padding: 0.5rem 1rem;
    border-radius: 8px;
    outline: none;
  }
`;

const StatusBadge = styled.div`
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  background: ${props => props.$connected ? 'rgba(72, 187, 120, 0.1)' : 'rgba(245, 101, 101, 0.1)'};
  color: ${props => props.$connected ? '#48bb78' : '#f56565'};
  border: 1px solid ${props => props.$connected ? 'rgba(72, 187, 120, 0.3)' : 'rgba(245, 101, 101, 0.3)'};
`;

const ThemeButton = styled.button`
  width: 40px;
  height: 40px;
  background: ${props => props.theme.primary};
  border: none;
  color: white;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.1);
  }
`;

const MainContent = styled.main`
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  padding: 2rem;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
    gap: 1rem;
    padding: 1rem;
  }
`;

const Panel = styled.div`
  background: ${props => props.theme.cardBg};
  border-radius: 16px;
  box-shadow: ${props => props.theme.shadow};
  border: 1px solid ${props => props.theme.border};
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const PanelHeader = styled.div`
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid ${props => props.theme.border};
  display: flex;
  align-items: center;
  gap: 1rem;
  color: ${props => props.theme.primary};
  
  h2 { margin: 0; font-size: 1.1rem; }
  p { margin: 0; font-size: 0.9rem; color: ${props => props.theme.textSecondary}; }
`;

const PanelContent = styled.div`
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const Section = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid ${props => props.theme.border};
`;

const SectionTitle = styled.h3`
  margin: 0 0 0.5rem 0;
  color: ${props => props.theme.primary};
  font-size: 1rem;
`;

const SectionDesc = styled.p`
  margin: 0 0 1rem 0;
  color: ${props => props.theme.textSecondary};
  font-size: 0.9rem;
`;

const RecordingArea = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
`;

const TextInputArea = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const VitalSignsInput = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
  
  label {
    font-size: 0.9rem;
    font-weight: 600;
    color: ${props => props.theme.text};
  }
  
  input {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid ${props => props.theme.border};
    border-radius: 8px;
    background: ${props => props.theme.cardBg};
    color: ${props => props.theme.text};
    font-size: 0.9rem;
    font-family: inherit;
    transition: all 0.3s ease;
    
    &:focus {
      outline: none;
      border-color: ${props => props.theme.primary};
      box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
    }
    
    &::placeholder {
      color: ${props => props.theme.textSecondary};
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
  
  small {
    font-size: 0.75rem;
    color: ${props => props.theme.textSecondary};
    font-style: italic;
  }
`;

const UrgencyBanner = styled.div`
  padding: 1rem;
  border-radius: 12px;
  margin: 1rem 0;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.95rem;
  animation: slideIn 0.3s ease-out;
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  ${props => {
    if (props.$urgency === 'high') {
      return `
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.15) 100%);
        border: 2px solid rgba(239, 68, 68, 0.5);
        color: #ef4444;
      `;
    } else if (props.$urgency === 'medium') {
      return `
        background: linear-gradient(135deg, rgba(249, 115, 22, 0.15) 0%, rgba(234, 88, 12, 0.15) 100%);
        border: 2px solid rgba(249, 115, 22, 0.5);
        color: #f97316;
      `;
    } else {
      return `
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(22, 163, 74, 0.15) 100%);
        border: 2px solid rgba(34, 197, 94, 0.5);
        color: #22c55e;
      `;
    }
  }}
`;

const FairnessWidget = styled.div`
  margin: 1rem 0;
  padding: 0.9rem;
  border-radius: 10px;
  border: 1px solid ${props => props.theme.border};
  background: ${props => props.theme.cardBg};
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const FairnessHeaderRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: ${props => props.theme.text};
`;

const FairnessBadge = styled.span`
  font-size: 0.85rem;
  font-weight: 700;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  color: ${props => props.$status === 'Fair ✅' ? '#166534' : '#92400e'};
  background: ${props => props.$status === 'Fair ✅' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(245, 158, 11, 0.18)'};
  border: 1px solid ${props => props.$status === 'Fair ✅' ? 'rgba(34, 197, 94, 0.35)' : 'rgba(245, 158, 11, 0.35)'};
`;

const FairnessMeta = styled.div`
  font-size: 0.82rem;
  color: ${props => props.theme.textSecondary};
`;

const FairnessRow = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 0.6rem;
  font-size: 0.82rem;
  color: ${props => props.theme.text};

  span:last-child {
    text-align: right;
    color: ${props => props.theme.textSecondary};
  }
`;

const TextInputBox = styled.textarea`
  width: 100%;
  min-height: 120px;
  padding: 1rem;
  border: 2px solid ${props => props.theme.border};
  border-radius: 12px;
  background: ${props => props.theme.cardBg};
  color: ${props => props.theme.text};
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.primary};
    box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
  }
  
  &::placeholder {
    color: ${props => props.theme.textSecondary};
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const RecordButton = styled.button`
  width: 70px;
  height: 70px;
  border-radius: 50%;
  border: none;
  background: ${props => props.$recording ? '#ff4757' : props.theme.primary};
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    transform: scale(1.1);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const Status = styled.div`
  font-size: 0.9rem;
  text-align: center;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const SmallButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: ${props => props.theme.primary};
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover:not(:disabled) {
    background: ${props => props.theme.primaryHover};
  }
`;

const TranscriptionBox = styled.div`
  background: ${props => props.theme.cardBg};
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid ${props => props.theme.border};
  width: 100%;
  text-align: left;
  
  strong {
    color: ${props => props.theme.primary};
    display: block;
    margin-bottom: 0.5rem;
  }
  
  p {
    margin: 0;
    line-height: 1.5;
  }
`;

const RecommendationBox = styled.div`
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 152, 0, 0.1) 100%);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  text-align: left;
  
  strong {
    color: #ff9800;
    display: block;
    margin-bottom: 0.5rem;
  }
  
  p {
    margin: 0;
    color: ${props => props.theme.text};
    line-height: 1.5;
    font-size: 0.9rem;
  }
`;

const UploadArea = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const UploadZone = styled.div`
  input { display: none; }
  
  label {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 2rem;
    border: 2px dashed ${props => props.theme.border};
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: ${props => props.theme.primary};
      background: rgba(255, 255, 255, 0.05);
    }
    
    span {
      font-weight: 600;
      color: ${props => props.theme.text};
    }
    
    small {
      color: ${props => props.theme.textSecondary};
    }
  }
`;

const ErrorText = styled.div`
  text-align: center;
  padding: 0.75rem;
  background: rgba(245, 101, 101, 0.1);
  border: 1px solid rgba(245, 101, 101, 0.3);
  border-radius: 8px;
  font-size: 0.9rem;
  color: ${props => props.theme.error};
`;

const FileGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
`;

const FileCard = styled.div`
  position: relative;
  background: ${props => props.theme.cardBg};
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  overflow: hidden;
`;

const FilePreview = styled.div`
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`;

const FileInfo = styled.div`
  padding: 0.75rem;
`;

const FileName = styled.div`
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const FileSize = styled.div`
  font-size: 0.7rem;
  color: ${props => props.theme.textSecondary};
`;

const RemoveButton = styled.button`
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: rgba(245, 101, 101, 0.9);
  color: white;
  cursor: pointer;
  font-size: 14px;
  
  &:hover {
    background: #f56565;
  }
`;

const DiagnosisButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
  padding: 1rem 2rem;
  background: ${props => props.$ready ? props.theme.success : props.theme.textSecondary};
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: ${props => props.$ready ? 'pointer' : 'not-allowed'};
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
  }
`;

const Spinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid ${props => props.theme.border};
  border-top-color: ${props => props.theme.success};
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const WelcomeScreen = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 3rem;
  text-align: center;
  color: ${props => props.theme.primary};
  
  h1 {
    margin: 1rem 0;
    font-size: 1.5rem;
  }
`;

const CheckList = styled.div`
  margin-top: 2rem;
`;

const CheckItem = styled.div`
  margin: 0.75rem 0;
  padding: 0.5rem;
  font-size: 0.9rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
`;

const ConversationArea = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const MessageCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 1.5rem;
`;

const DoctorMessage = styled.div``;

const MessageHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  color: ${props => props.theme.success};
  
  h4 {
    margin: 0;
    flex: 1;
  }
`;

const MessageContent = styled.div`
  line-height: 1.6;
  margin-bottom: 1rem;
  white-space: pre-wrap;
`;

const AudioSection = styled.div`
  margin: 1rem 0;
`;

const AudioLabel = styled.div`
  font-size: 0.9rem;
  font-weight: 600;
  color: ${props => props.theme.primary};
  margin-bottom: 0.5rem;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
`;

const ActionButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: ${props => props.theme.primary};
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: ${props => props.theme.primaryHover};
  }
`;

const LoadingMessage = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  color: ${props => props.theme.primary};
  font-style: italic;
`;

const ErrorMessage = styled.div`
  color: ${props => props.theme.error};
  background: rgba(245, 101, 101, 0.1);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(245, 101, 101, 0.3);
`;

const Timestamp = styled.div`
  font-size: 0.7rem;
  color: ${props => props.theme.textSecondary};
`;

const ResetButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: ${props => props.theme.danger};
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  margin: 1rem auto;
  
  &:hover {
    background: #dc2626;
  }
`;

const Footer = styled.footer`
  background: ${props => props.theme.cardBg};
  border-top: 1px solid ${props => props.theme.border};
  padding: 1.5rem;
  text-align: center;
  
  p {
    margin: 0;
    color: ${props => props.theme.textSecondary};
    font-size: 0.8rem;
  }
`;

// Language Selection Components
const LanguageScreen = styled.div`
  min-height: 100vh;
  background: ${props => props.theme.background};
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
`;

const LanguageCard = styled.div`
  background: ${props => props.theme.cardBg};
  border-radius: 20px;
  box-shadow: ${props => props.theme.shadow};
  padding: 3rem;
  max-width: 500px;
  width: 100%;
  text-align: center;
`;

const LanguageTitle = styled.h1`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => props.theme.text};
  margin: 2rem 0 1rem;
`;

const LanguageButtons = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 2rem 0;
`;

const LanguageButton = styled.button`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: ${props => props.theme.text};
  font-size: 1rem;
  
  &:hover {
    border-color: ${props => props.theme.primary};
    background: ${props => props.theme.primary}20;
  }
`;

const Disclaimer = styled.p`
  color: ${props => props.theme.textSecondary};
  font-size: 0.8rem;
  margin-top: 2rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  line-height: 1.5;
`;

// Audio Player Components
const AudioContainer = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  padding: 1rem;
`;

const DebugPanel = styled.div`
  background: rgba(0, 100, 200, 0.1);
  border: 1px solid rgba(0, 100, 200, 0.3);
  border-radius: 6px;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.7rem;
`;

const DebugTitle = styled.div`
  font-weight: bold;
  color: #4299e1;
  margin-bottom: 0.25rem;
`;

const DebugMessage = styled.div`
  color: ${props => props.theme.textSecondary};
  margin: 0.1rem 0;
  font-family: monospace;
`;

const ErrorPanel = styled.div`
  background: rgba(245, 101, 101, 0.1);
  border: 1px solid rgba(245, 101, 101, 0.3);
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
`;

const ErrorTitle = styled.div`
  font-weight: bold;
  color: #f56565;
  margin-bottom: 0.25rem;
`;

const AudioErrorMessage = styled.div`
  color: ${props => props.theme.error};
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
`;

const RetryButton = styled.button`
  background: ${props => props.theme.error};
  color: white;
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  cursor: pointer;
  
  &:hover {
    background: ${props => props.theme.danger};
  }
`;

const LoadingIndicator = styled.div`
  text-align: center;
  color: ${props => props.theme.primary};
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
  font-style: italic;
`;

const Controls = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const PlayButton = styled.button`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: ${props => 
    props.$error ? props.theme.error :
    props.disabled ? props.theme.textSecondary : 
    props.theme.primary
  };
  color: white;
  border: none;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  opacity: ${props => props.disabled ? 0.6 : 1};
  
  &:hover:not(:disabled) {
    background: ${props => 
      props.$error ? props.theme.danger :
      props.theme.primaryHover
    };
    transform: scale(1.05);
  }
  
  &:active:not(:disabled) {
    transform: scale(0.95);
  }
`;

const ProgressBar = styled.div`
  flex: 1;
  cursor: ${props => props.disabled ? 'default' : 'pointer'};
  height: 6px;
  background: ${props => props.theme.border};
  border-radius: 3px;
  overflow: hidden;
  opacity: ${props => props.disabled ? 0.5 : 1};
  transition: all 0.3s ease;
  border: ${props => props.$error ? `1px solid ${props.theme.error}` : 'none'};
  
  &:hover:not([disabled]) {
    height: 8px;
  }
`;

const Progress = styled.div`
  height: 100%;
  background: ${props => props.theme.primary};
  transition: width 0.1s ease;
`;

const TimeDisplay = styled.div`
  font-size: 0.7rem;
  color: ${props => props.$error ? props.theme.error : props.theme.textSecondary};
  min-width: 70px;
  text-align: center;
`;

const SpeedControl = styled.div`
  position: relative;
`;

const SpeedButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  background: ${props => props.$error ? props.theme.error : props.theme.border};
  border: none;
  border-radius: 20px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  font-size: 0.7rem;
  color: ${props => props.$error ? 'white' : props.theme.text};
  opacity: ${props => props.disabled ? 0.5 : 1};
  
  &:hover:not(:disabled) {
    background: ${props => props.$error ? props.theme.danger : props.theme.primary};
    color: white;
  }
`;

const DebugControls = styled.div`
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
  font-size: 0.7rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  small {
    color: ${props => props.theme.textSecondary};
    word-break: break-all;
    max-width: 70%;
  }
`;

const TestButton = styled.button`
  background: ${props => props.theme.primary};
  color: white;
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.6rem;
  cursor: pointer;
  
  &:hover {
    background: ${props => props.theme.primaryHover};
  }
`;

// Missing Audio Player Styled Components
const ErrorDisplay = styled.div`
  padding: 0.75rem;
  background: rgba(245, 101, 101, 0.1);
  border: 1px solid rgba(245, 101, 101, 0.3);
  border-radius: 6px;
  margin-bottom: 0.5rem;
  color: ${props => props.theme.error};
  font-size: 0.8rem;
`;

const SpeedMenu = styled.div`
  position: absolute;
  bottom: 100%;
  right: 0;
  background: ${props => props.theme.cardBg};
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  box-shadow: ${props => props.theme.shadow};
  padding: 0.5rem 0;
  margin-bottom: 0.5rem;
  z-index: 100;
`;

const SpeedOption = styled.button`
  display: block;
  width: 100%;
  padding: 0.5rem 1rem;
  background: ${props => props.$active ? props.theme.primary : 'transparent'};
  color: ${props => props.$active ? 'white' : props.theme.text};
  border: none;
  cursor: pointer;
  font-size: 0.75rem;
  text-align: left;
  
  &:hover {
    background: ${props => props.$active ? props.theme.primaryHover : props.theme.border};
  }
`;

// Find Doctors Button Components
const FindDoctorsButtonContainer = styled.div`
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  max-width: 320px;
  
  @media (max-width: 768px) {
    position: fixed;
    bottom: 1rem;
    left: 50%;
    transform: translateX(-50%);
    max-width: 90vw;
  }
`;

const FindDoctorsButton = styled.button`
  background: linear-gradient(135deg, #4299e1 0%, #48bb78 100%);
  color: white;
  border: none;
  padding: 1.2rem 2.5rem;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 8px 25px rgba(66, 153, 225, 0.3);
  transition: all 0.3s ease;
  white-space: nowrap;
  position: relative;
  overflow: hidden;
  animation: pulse 2s infinite;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s;
  }
  
  &:hover::before {
    left: 100%;
  }
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 30px rgba(66, 153, 225, 0.4);
    background: linear-gradient(135deg, #3182ce 0%, #38a169 100%);
  }
  
  &:active {
    transform: translateY(-1px);
  }
  
  @keyframes pulse {
    0%, 100% {
      box-shadow: 0 8px 25px rgba(66, 153, 225, 0.3);
    }
    50% {
      box-shadow: 0 10px 30px rgba(66, 153, 225, 0.5);
    }
  }
  
  @media (max-width: 768px) {
    padding: 1rem 2rem;
    font-size: 1rem;
  }
`;

const FindDoctorsDescription = styled.p`
  color: ${props => props.theme.textSecondary};
  font-size: 0.9rem;
  text-align: center;
  margin: 0;
  padding: 0.75rem 1.5rem;
  background: ${props => props.theme.cardBg};
  border-radius: 25px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid ${props => props.theme.border};
  backdrop-filter: blur(10px);
  font-weight: 500;
  
  @media (max-width: 768px) {
    font-size: 0.8rem;
    padding: 0.5rem 1rem;
  }
`;

export default App;
