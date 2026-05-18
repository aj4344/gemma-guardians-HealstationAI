// 🚨 Emergency Triage Component - Real-time Emergency Risk Scoring & Hospital Routing
import React, { useState, useEffect, useCallback } from 'react';
import styled, { keyframes } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaExclamationTriangle,
  FaPhoneAlt,
  FaHospital,
  FaHeartbeat,
  FaBrain,
  FaUserInjured,
  FaMapMarkerAlt,
  FaTimes,
  FaAmbulance,
  FaDirections,
  FaCheck,
  FaClock,
  FaExclamationCircle,
  FaInfoCircle,
  FaArrowRight
} from 'react-icons/fa';
import axios from 'axios';

// ============ ANIMATIONS ============
const pulse = keyframes`
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.9; }
`;

const emergencyPulse = keyframes`
  0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
  50% { box-shadow: 0 0 0 15px rgba(220, 38, 38, 0); }
`;

const slideIn = keyframes`
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
`;

// ============ STYLED COMPONENTS ============
const EmergencyOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.95);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 15000;
  padding: 1rem;
`;

const EmergencyContainer = styled(motion.div)`
  background: linear-gradient(180deg, rgba(30, 30, 35, 0.98) 0%, rgba(20, 20, 25, 0.98) 100%);
  backdrop-filter: blur(25px);
  border: 2px solid ${props => props.$triageColor || '#DC2626'};
  border-radius: 25px;
  padding: 2rem;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5),
              0 0 30px ${props => props.$triageColor || '#DC2626'}40;
  position: relative;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${props => props.$triageColor || '#DC2626'};
    border-radius: 4px;
  }
`;

const CloseButton = styled(motion.button)`
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    color: white;
  }
`;

const TriageHeader = styled.div`
  text-align: center;
  margin-bottom: 1.5rem;
`;

const TriageBadge = styled(motion.div)`
  background: ${props => props.$triageColor || '#DC2626'};
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  animation: ${props => props.$isCritical ? emergencyPulse : 'none'} 1.5s infinite;
  
  svg {
    font-size: 1.2rem;
  }
`;

const TriageTitle = styled.h2`
  color: white;
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
`;

const TriageSubtitle = styled.p`
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
`;

const ActionSection = styled.div`
  margin: 1.5rem 0;
`;

const PrimaryActionButton = styled(motion.a)`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  width: 100%;
  padding: 1.25rem 1.5rem;
  background: ${props => props.$triageColor || '#DC2626'};
  color: white;
  border: none;
  border-radius: 15px;
  font-size: 1.2rem;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.3s ease;
  animation: ${props => props.$pulse ? pulse : 'none'} 2s infinite;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px ${props => props.$triageColor || '#DC2626'}50;
  }

  svg {
    font-size: 1.5rem;
  }
`;

const SecondaryActions = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1rem;
`;

const SecondaryActionButton = styled(motion.button)`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 1rem 1.25rem;
  background: rgba(255, 255, 255, 0.08);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  font-size: 1rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.25);
  }

  svg {
    font-size: 1.2rem;
    color: ${props => props.$color || '#3B82F6'};
  }

  .action-text {
    flex: 1;
  }

  .action-arrow {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const ScoreSection = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  padding: 1.25rem;
  margin: 1.5rem 0;
`;

const ScoreTitle = styled.h3`
  color: white;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ScoreGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
`;

const ScoreCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
  border: 1px solid ${props => {
    if (props.$riskLevel === 'HIGH' || props.$riskLevel === 'CRITICAL') return '#DC2626';
    if (props.$riskLevel === 'MODERATE') return '#F59E0B';
    return 'rgba(255, 255, 255, 0.1)';
  }};

  .score-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    color: ${props => props.$iconColor || '#4CAF50'};
  }

  .score-name {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.25rem;
  }

  .score-value {
    color: white;
    font-size: 1.5rem;
    font-weight: 700;
  }

  .score-max {
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.9rem;
  }

  .risk-level {
    font-size: 0.7rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    margin-top: 0.5rem;
    background: ${props => {
      if (props.$riskLevel === 'HIGH' || props.$riskLevel === 'CRITICAL') return 'rgba(220, 38, 38, 0.2)';
      if (props.$riskLevel === 'MODERATE') return 'rgba(245, 158, 11, 0.2)';
      return 'rgba(34, 197, 94, 0.2)';
    }};
    color: ${props => {
      if (props.$riskLevel === 'HIGH' || props.$riskLevel === 'CRITICAL') return '#EF4444';
      if (props.$riskLevel === 'MODERATE') return '#FBBF24';
      return '#22C55E';
    }};
  }
`;

const HospitalSection = styled.div`
  margin: 1.5rem 0;
`;

const HospitalTitle = styled.h3`
  color: white;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const HospitalCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: #4CAF50;
  }
`;

const HospitalName = styled.div`
  color: white;
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 0.5rem;
`;

const HospitalDetails = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;

  .detail {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .badge {
    background: rgba(76, 175, 80, 0.2);
    color: #4CAF50;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
  }
`;

const DetectedConditions = styled.div`
  background: rgba(234, 88, 12, 0.1);
  border: 1px solid rgba(234, 88, 12, 0.3);
  border-radius: 12px;
  padding: 1rem;
  margin: 1rem 0;
`;

const ConditionTitle = styled.h4`
  color: #F97316;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ConditionList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.9rem;
    padding: 0.35rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;

    &::before {
      content: '•';
      color: #F97316;
      font-size: 1.2rem;
    }
  }
`;

const Disclaimer = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 1rem;
  margin-top: 1.5rem;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
  line-height: 1.5;
  text-align: center;
`;

const LocationWarning = styled.div`
  background: linear-gradient(135deg, rgba(234, 88, 12, 0.2), rgba(220, 38, 38, 0.2));
  border: 1px solid rgba(234, 88, 12, 0.5);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  
  .location-icon {
    font-size: 2rem;
  }
  
  .location-text {
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.9rem;
    text-align: center;
    line-height: 1.4;
  }
  
  .location-subtext {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.8rem;
    text-align: center;
  }
`;

const EnableLocationButton = styled.button`
  background: linear-gradient(135deg, #EA580C, #DC2626);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const LocationStatusBadge = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  
  ${props => props.$status === 'granted' && `
    background: rgba(34, 197, 94, 0.2);
    color: #22C55E;
    border: 1px solid rgba(34, 197, 94, 0.3);
  `}
  
  ${props => props.$status === 'denied' && `
    background: rgba(239, 68, 68, 0.2);
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  `}
  
  ${props => props.$status === 'pending' && `
    background: rgba(234, 179, 8, 0.2);
    color: #EAB308;
    border: 1px solid rgba(234, 179, 8, 0.3);
  `}
`;

const LoadingContainer = styled.div`
  text-align: center;
  padding: 3rem;
  color: white;

  .spinner {
    width: 60px;
    height: 60px;
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-top-color: #DC2626;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1.5rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  h3 {
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
  }

  p {
    color: rgba(255, 255, 255, 0.6);
  }
`;

// ============ QUICK SYMPTOM INPUT ============
const SymptomInputSection = styled.div`
  margin-bottom: 1.5rem;
`;

const SymptomInput = styled.textarea`
  width: 100%;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  resize: vertical;
  min-height: 100px;
  font-family: inherit;

  &::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }

  &:focus {
    outline: none;
    border-color: #4CAF50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
  }
`;

const QuickCheckButton = styled(motion.button)`
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #DC2626, #B91C1C);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;

  &:hover {
    background: linear-gradient(135deg, #B91C1C, #DC2626);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const QuickSymptomButtons = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const QuickSymptomButton = styled(motion.button)`
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  color: white;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(220, 38, 38, 0.2);
    border-color: #DC2626;
  }

  &.selected {
    background: rgba(220, 38, 38, 0.3);
    border-color: #DC2626;
  }
`;

// ============ TRANSLATIONS ============
const translations = {
  en: {
    title: "Emergency Assessment",
    subtitle: "Real-time emergency risk evaluation",
    symptomsPlaceholder: "Describe your symptoms in detail...\nExample: I have severe chest pain that started 30 minutes ago, difficulty breathing, and sweating",
    checkSymptoms: "Check Emergency Level",
    analyzing: "Analyzing symptoms...",
    call108: "CALL 108 NOW",
    call112: "Emergency Helpline: 112",
    findER: "Find Nearest Emergency Room",
    detectedConditions: "Detected Conditions",
    riskScores: "Risk Assessment Scores",
    nearestHospitals: "Nearest Hospitals",
    disclaimer: "⚠️ This AI assessment is for guidance only and does NOT replace professional medical judgment. In any emergency, CALL 108 IMMEDIATELY.",
    quickSymptoms: ["Chest Pain", "Difficulty Breathing", "Severe Headache", "Unconscious", "Heavy Bleeding", "Stroke Symptoms", "Heart Attack", "Accident/Trauma"],
    cardiac: "Cardiac",
    stroke: "Stroke",
    trauma: "Trauma",
    low: "LOW",
    moderate: "MODERATE",
    high: "HIGH",
    critical: "CRITICAL",
    triageLevels: {
      1: "CRITICAL - Call 108 Immediately",
      2: "EMERGENCY - Go to ER Now",
      3: "URGENT - See Doctor Today",
      4: "STANDARD - Schedule Appointment",
      5: "SELF-CARE - Monitor at Home"
    },
    getDirections: "Get Directions",
    hasER: "Has ER",
    open24x7: "24/7",
    kmAway: "km away",
    minsDrive: "mins drive",
    // Location messages
    locationEnabled: "📍 Location enabled - showing hospitals near you",
    locationRequired: "📍 Location permission required to find nearby hospitals",
    locationDeniedMessage: "Please enable location access in your browser settings, then click the button below",
    enableLocation: "Enable Location",
    gettingLocation: "Getting location..."
  },
  hi: {
    title: "आपातकालीन मूल्यांकन",
    subtitle: "वास्तविक समय आपातकालीन जोखिम मूल्यांकन",
    symptomsPlaceholder: "अपने लक्षणों का विस्तार से वर्णन करें...\nउदाहरण: मुझे 30 मिनट पहले से तेज सीने में दर्द है, सांस लेने में तकलीफ और पसीना आ रहा है",
    checkSymptoms: "आपातकालीन स्तर जांचें",
    analyzing: "लक्षणों का विश्लेषण...",
    call108: "अभी 108 पर कॉल करें",
    call112: "आपातकालीन हेल्पलाइन: 112",
    findER: "निकटतम आपातकालीन कक्ष खोजें",
    detectedConditions: "पता लगाई गई स्थितियाँ",
    riskScores: "जोखिम मूल्यांकन स्कोर",
    nearestHospitals: "निकटतम अस्पताल",
    disclaimer: "⚠️ यह AI मूल्यांकन केवल मार्गदर्शन के लिए है और पेशेवर चिकित्सा निर्णय की जगह नहीं ले सकता। किसी भी आपात स्थिति में, तुरंत 108 पर कॉल करें।",
    quickSymptoms: ["सीने में दर्द", "सांस लेने में तकलीफ", "तेज सिरदर्द", "बेहोशी", "भारी रक्तस्राव", "स्ट्रोक के लक्षण", "दिल का दौरा", "दुर्घटना/आघात"],
    cardiac: "हृदय",
    stroke: "स्ट्रोक",
    trauma: "आघात",
    low: "कम",
    moderate: "मध्यम",
    high: "उच्च",
    critical: "गंभीर",
    triageLevels: {
      1: "गंभीर - तुरंत 108 कॉल करें",
      2: "आपातकालीन - अभी ER जाएं",
      3: "जरूरी - आज डॉक्टर से मिलें",
      4: "सामान्य - अपॉइंटमेंट लें",
      5: "स्व-देखभाल - घर पर निगरानी करें"
    },
    getDirections: "दिशाएं प्राप्त करें",
    hasER: "ER है",
    open24x7: "24/7",
    kmAway: "किमी दूर",
    minsDrive: "मिनट ड्राइव",
    // Location messages
    locationEnabled: "📍 स्थान सक्षम - आपके पास के अस्पताल दिखा रहे हैं",
    locationRequired: "📍 पास के अस्पताल खोजने के लिए स्थान अनुमति आवश्यक",
    locationDeniedMessage: "कृपया अपने ब्राउज़र सेटिंग्स में स्थान पहुंच सक्षम करें, फिर नीचे बटन पर क्लिक करें",
    enableLocation: "स्थान सक्षम करें",
    gettingLocation: "स्थान प्राप्त कर रहे हैं..."
  },
  mr: {
    title: "आणीबाणी मूल्यांकन",
    subtitle: "रिअल-टाइम आणीबाणी जोखीम मूल्यांकन",
    symptomsPlaceholder: "तुमची लक्षणे तपशीलवार वर्णन करा...\nउदाहरण: मला 30 मिनिटांपूर्वी तीव्र छातीत दुखणे सुरू झाले, श्वास घेण्यास त्रास आणि घाम येत आहे",
    checkSymptoms: "आणीबाणी पातळी तपासा",
    analyzing: "लक्षणांचे विश्लेषण...",
    call108: "आत्ताच 108 वर कॉल करा",
    call112: "आणीबाणी हेल्पलाइन: 112",
    findER: "जवळचे आणीबाणी कक्ष शोधा",
    detectedConditions: "आढळलेल्या परिस्थिती",
    riskScores: "जोखीम मूल्यांकन स्कोअर",
    nearestHospitals: "जवळचे रुग्णालये",
    disclaimer: "⚠️ हे AI मूल्यांकन फक्त मार्गदर्शनासाठी आहे आणि व्यावसायिक वैद्यकीय निर्णयाची जागा घेत नाही। कोणत्याही आणीबाणीत, ताबडतोब 108 वर कॉल करा।",
    quickSymptoms: ["छातीत दुखणे", "श्वास घेण्यास त्रास", "तीव्र डोकेदुखी", "बेशुद्ध", "जोरदार रक्तस्त्राव", "स्ट्रोकची लक्षणे", "हृदयविकाराचा झटका", "अपघात/आघात"],
    cardiac: "हृदय",
    stroke: "स्ट्रोक",
    trauma: "आघात",
    low: "कमी",
    moderate: "मध्यम",
    high: "उच्च",
    critical: "गंभीर",
    triageLevels: {
      1: "गंभीर - ताबडतोब 108 कॉल करा",
      2: "आणीबाणी - आत्ता ER ला जा",
      3: "तातडीचे - आज डॉक्टरांना भेटा",
      4: "सामान्य - भेटीची वेळ घ्या",
      5: "स्व-काळजी - घरी निरीक्षण करा"
    },
    getDirections: "दिशानिर्देश मिळवा",
    hasER: "ER आहे",
    open24x7: "24/7",
    kmAway: "किमी दूर",
    minsDrive: "मिनिटे ड्राइव्ह",
    // Location messages
    locationEnabled: "📍 स्थान सक्षम - तुमच्या जवळची रुग्णालये दाखवत आहे",
    locationRequired: "📍 जवळची रुग्णालये शोधण्यासाठी स्थान परवानगी आवश्यक",
    locationDeniedMessage: "कृपया तुमच्या ब्राउझर सेटिंग्जमध्ये स्थान प्रवेश सक्षम करा, नंतर खाली बटण दाबा",
    enableLocation: "स्थान सक्षम करा",
    gettingLocation: "स्थान मिळवत आहे..."
  }
};

// ============ TRIAGE LEVEL CONFIG ============
const TRIAGE_CONFIG = {
  1: { color: '#DC2626', icon: '🚨', name: 'CRITICAL' },
  2: { color: '#EA580C', icon: '⚠️', name: 'EMERGENCY' },
  3: { color: '#FACC15', icon: '⚡', name: 'URGENT' },
  4: { color: '#22C55E', icon: '📋', name: 'STANDARD' },
  5: { color: '#3B82F6', icon: 'ℹ️', name: 'SELF-CARE' }
};

// ============ MAIN COMPONENT ============
export const EmergencyTriage = ({ 
  isOpen, 
  onClose, 
  language = 'en',
  initialSymptoms = '',
  userLocation = null,
  apiBaseUrl = 'http://127.0.0.1:8001'
}) => {
  const [symptoms, setSymptoms] = useState(initialSymptoms);
  const [selectedQuickSymptoms, setSelectedQuickSymptoms] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [triageResult, setTriageResult] = useState(null);
  const [error, setError] = useState(null);
  const [location, setLocation] = useState(userLocation);
  const [locationStatus, setLocationStatus] = useState('pending'); // 'pending', 'granted', 'denied', 'unavailable'
  const [isRequestingLocation, setIsRequestingLocation] = useState(false);

  const t = translations[language] || translations.en;

  // Request user location with retry logic for timeout
  const requestLocation = useCallback((retryCount = 0, useHighAccuracy = false) => {
    if (!navigator.geolocation) {
      setLocationStatus('unavailable');
      console.log('Geolocation not supported by browser');
      return;
    }

    setIsRequestingLocation(true);
    setLocationStatus('pending');
    console.log(`📍 Requesting location (attempt ${retryCount + 1}, highAccuracy: ${useHighAccuracy})...`);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        console.log('✅ Location obtained:', position.coords.latitude, position.coords.longitude);
        const newLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };
        setLocation(newLocation);
        setLocationStatus('granted');
        setIsRequestingLocation(false);
      },
      (err) => {
        console.log('❌ Geolocation error:', err.code, err.message);
        
        // Error codes: 1 = PERMISSION_DENIED, 2 = POSITION_UNAVAILABLE, 3 = TIMEOUT
        if (err.code === 3 && retryCount < 2) {
          // Timeout - retry with different settings
          console.log(`⏳ Timeout, retrying with ${useHighAccuracy ? 'low' : 'high'} accuracy...`);
          requestLocation(retryCount + 1, !useHighAccuracy);
          return;
        }
        
        if (err.code === 2 && retryCount < 1) {
          // Position unavailable - retry once with different accuracy
          console.log('📍 Position unavailable, retrying...');
          requestLocation(retryCount + 1, !useHighAccuracy);
          return;
        }
        
        if (err.code === 1) {
          // Permission denied by user
          setLocationStatus('denied');
          console.log('🚫 Location permission denied by user');
        } else {
          // Timeout or unavailable after retries
          setLocationStatus('denied');
          console.log('⚠️ Could not get location after retries');
        }
        
        setIsRequestingLocation(false);
      },
      { 
        timeout: useHighAccuracy ? 15000 : 30000, // Longer timeout for low accuracy
        enableHighAccuracy: useHighAccuracy, 
        maximumAge: 300000 // Accept cached location up to 5 minutes old
      }
    );
  }, []);

  // Get user location on mount
  useEffect(() => {
    if (!location && locationStatus === 'pending') {
      requestLocation(0, false); // Start with low accuracy (faster on desktop)
    }
  }, [location, locationStatus, requestLocation]);

  // Re-fetch hospitals when location becomes available after triage was done without location
  useEffect(() => {
    const fetchHospitalsWithNewLocation = async () => {
      // Only proceed if we have triageResult, location, and no hospitals yet
      if (triageResult && location && locationStatus === 'granted' && 
          (!triageResult.hospitals || triageResult.hospitals.length === 0)) {
        console.log('📍 Location now available, fetching hospitals...');
        
        try {
          const allSymptoms = [symptoms, ...selectedQuickSymptoms].filter(Boolean).join(', ');
          
          const response = await axios.post(`${apiBaseUrl}/api/emergency-triage`, {
            symptoms: allSymptoms || 'general emergency',
            latitude: location.latitude,
            longitude: location.longitude,
            language: language,
            patient_info: {}
          }, {
            timeout: 30000
          });
          
          // Update triageResult with new hospitals data
          if (response.data.hospitals && response.data.hospitals.length > 0) {
            console.log(`✅ Found ${response.data.hospitals.length} hospitals near user`);
            setTriageResult(prev => ({
              ...prev,
              hospitals: response.data.hospitals,
              nearest_capable_hospital: response.data.nearest_capable_hospital
            }));
          }
        } catch (err) {
          console.error('Error fetching hospitals:', err);
        }
      }
    };
    
    fetchHospitalsWithNewLocation();
  }, [location, locationStatus, triageResult, symptoms, selectedQuickSymptoms, apiBaseUrl, language]);

  // Toggle quick symptom selection
  const toggleQuickSymptom = (symptom) => {
    setSelectedQuickSymptoms(prev => {
      if (prev.includes(symptom)) {
        return prev.filter(s => s !== symptom);
      }
      return [...prev, symptom];
    });
  };

  // Perform emergency triage
  const performTriage = useCallback(async () => {
    const allSymptoms = [symptoms, ...selectedQuickSymptoms].filter(Boolean).join(', ');
    
    if (!allSymptoms.trim()) {
      setError('Please describe your symptoms');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${apiBaseUrl}/api/emergency-triage`, {
        symptoms: allSymptoms,
        latitude: location?.latitude,
        longitude: location?.longitude,
        language: language,
        patient_info: {}
      }, {
        timeout: 30000
      });

      setTriageResult(response.data);
    } catch (err) {
      console.error('Triage error:', err);
      
      // Try quick endpoint as fallback
      try {
        const quickResponse = await axios.get(`${apiBaseUrl}/api/emergency-triage/quick`, {
          params: { symptoms: allSymptoms },
          timeout: 10000
        });
        
        setTriageResult({
          ...quickResponse.data,
          hospitals: [],
          scores: null
        });
      } catch (fallbackErr) {
        setError('Unable to perform emergency assessment. Please call 108 directly.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [symptoms, selectedQuickSymptoms, location, apiBaseUrl]);

  // Open Google Maps directions with user's actual location as origin
  const openDirections = (hospital) => {
    let url;
    
    if (location && location.latitude && location.longitude) {
      // Include user's actual location as origin for accurate directions
      url = `https://www.google.com/maps/dir/?api=1&origin=${location.latitude},${location.longitude}&destination=${hospital.latitude},${hospital.longitude}&travelmode=driving`;
      console.log(`🗺️ Opening directions from user location (${location.latitude}, ${location.longitude}) to ${hospital.name}`);
    } else {
      // Fallback: Let Google Maps determine origin (may be inaccurate)
      url = `https://www.google.com/maps/dir/?api=1&destination=${hospital.latitude},${hospital.longitude}&travelmode=driving`;
      console.log(`🗺️ Opening directions to ${hospital.name} (origin: user's device location)`);
    }
    
    window.open(url, '_blank');
  };

  if (!isOpen) return null;

  const triageLevel = triageResult?.triage_level || 5;
  const triageConfig = TRIAGE_CONFIG[triageLevel];

  return (
    <AnimatePresence>
      <EmergencyOverlay
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <EmergencyContainer
          $triageColor={triageResult ? triageConfig.color : '#DC2626'}
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
        >
          <CloseButton onClick={onClose} whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
            <FaTimes />
          </CloseButton>

          <TriageHeader>
            <TriageBadge 
              $triageColor={triageResult ? triageConfig.color : '#DC2626'}
              $isCritical={triageLevel <= 2}
            >
              <FaAmbulance />
              {triageResult ? t.triageLevels[triageLevel] : t.title}
            </TriageBadge>
            <TriageTitle>{t.title}</TriageTitle>
            <TriageSubtitle>{t.subtitle}</TriageSubtitle>
          </TriageHeader>

          {!triageResult && !isLoading && (
            <>
              <SymptomInputSection>
                <SymptomInput
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  placeholder={t.symptomsPlaceholder}
                />
                
                <QuickSymptomButtons>
                  {t.quickSymptoms.map((symptom, index) => (
                    <QuickSymptomButton
                      key={index}
                      className={selectedQuickSymptoms.includes(symptom) ? 'selected' : ''}
                      onClick={() => toggleQuickSymptom(symptom)}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {symptom}
                    </QuickSymptomButton>
                  ))}
                </QuickSymptomButtons>

                <QuickCheckButton
                  onClick={performTriage}
                  disabled={!symptoms.trim() && selectedQuickSymptoms.length === 0}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <FaExclamationTriangle />
                  {t.checkSymptoms}
                </QuickCheckButton>

                {error && (
                  <div style={{ color: '#EF4444', marginTop: '1rem', textAlign: 'center' }}>
                    {error}
                  </div>
                )}
              </SymptomInputSection>

              {/* Always show 108 call button */}
              <PrimaryActionButton
                href="tel:108"
                $triageColor="#DC2626"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <FaPhoneAlt />
                {t.call108}
              </PrimaryActionButton>
            </>
          )}

          {isLoading && (
            <LoadingContainer>
              <div className="spinner" />
              <h3>{t.analyzing}</h3>
              <p>Evaluating symptoms and finding nearest hospitals...</p>
            </LoadingContainer>
          )}

          {triageResult && !isLoading && (
            <>
              {/* Primary Action */}
              <ActionSection>
                {triageResult.call_108 ? (
                  <PrimaryActionButton
                    href="tel:108"
                    $triageColor={triageConfig.color}
                    $pulse={triageLevel <= 2}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <FaPhoneAlt />
                    {t.call108}
                  </PrimaryActionButton>
                ) : (
                  <PrimaryActionButton
                    as="button"
                    $triageColor={triageConfig.color}
                    onClick={() => {
                      if (triageResult.hospitals?.[0]) {
                        openDirections(triageResult.hospitals[0]);
                      }
                    }}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <FaHospital />
                    {triageResult.primary_action?.action_text || t.findER}
                  </PrimaryActionButton>
                )}

                <SecondaryActions>
                  {triageResult.call_108 && (
                    <SecondaryActionButton
                      $color="#22C55E"
                      onClick={() => triageResult.hospitals?.[0] && openDirections(triageResult.hospitals[0])}
                    >
                      <FaHospital />
                      <span className="action-text">{t.findER}</span>
                      <FaArrowRight className="action-arrow" />
                    </SecondaryActionButton>
                  )}
                  <SecondaryActionButton as="a" href="tel:112" $color="#3B82F6">
                    <FaPhoneAlt />
                    <span className="action-text">{t.call112}</span>
                    <FaArrowRight className="action-arrow" />
                  </SecondaryActionButton>
                </SecondaryActions>
              </ActionSection>

              {/* Detected Conditions */}
              {triageResult.detected_conditions?.length > 0 && (
                <DetectedConditions>
                  <ConditionTitle>
                    <FaExclamationCircle />
                    {t.detectedConditions}
                  </ConditionTitle>
                  <ConditionList>
                    {triageResult.detected_conditions.slice(0, 5).map((condition, index) => (
                      <li key={index}>{condition}</li>
                    ))}
                  </ConditionList>
                </DetectedConditions>
              )}

              {/* Risk Scores */}
              {triageResult.scores && (
                <ScoreSection>
                  <ScoreTitle>
                    <FaHeartbeat />
                    {t.riskScores}
                  </ScoreTitle>
                  <ScoreGrid>
                    <ScoreCard 
                      $riskLevel={triageResult.scores.heart_score?.risk_level}
                      $iconColor="#EF4444"
                    >
                      <div className="score-icon"><FaHeartbeat /></div>
                      <div className="score-name">{t.cardiac}</div>
                      <div className="score-value">
                        {triageResult.scores.heart_score?.score || 0}
                        <span className="score-max">/10</span>
                      </div>
                      <div className="risk-level">
                        {triageResult.scores.heart_score?.risk_level || t.low}
                      </div>
                    </ScoreCard>
                    
                    <ScoreCard 
                      $riskLevel={triageResult.scores.befast_score?.risk_level}
                      $iconColor="#8B5CF6"
                    >
                      <div className="score-icon"><FaBrain /></div>
                      <div className="score-name">{t.stroke}</div>
                      <div className="score-value">
                        {triageResult.scores.befast_score?.score || 0}
                        <span className="score-max">/6</span>
                      </div>
                      <div className="risk-level">
                        {triageResult.scores.befast_score?.risk_level || t.low}
                      </div>
                    </ScoreCard>
                    
                    <ScoreCard 
                      $riskLevel={triageResult.scores.trauma_score?.risk_level}
                      $iconColor="#F59E0B"
                    >
                      <div className="score-icon"><FaUserInjured /></div>
                      <div className="score-name">{t.trauma}</div>
                      <div className="score-value">
                        {triageResult.scores.trauma_score?.score || 0}
                        <span className="score-max">/10</span>
                      </div>
                      <div className="risk-level">
                        {triageResult.scores.trauma_score?.risk_level || t.low}
                      </div>
                    </ScoreCard>
                  </ScoreGrid>
                </ScoreSection>
              )}

              {/* Nearby Hospitals */}
              {triageResult.hospitals?.length > 0 && locationStatus === 'granted' && (
                <HospitalSection>
                  <HospitalTitle>
                    <FaHospital />
                    {t.nearestHospitals}
                  </HospitalTitle>
                  <LocationStatusBadge $status="granted">
                    <FaMapMarkerAlt /> {t.locationEnabled || 'Location enabled - showing nearby hospitals'}
                  </LocationStatusBadge>
                  {triageResult.hospitals.slice(0, 3).map((hospital, index) => (
                    <HospitalCard
                      key={hospital.id || index}
                      onClick={() => openDirections(hospital)}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <HospitalName>{hospital.name}</HospitalName>
                      <HospitalDetails>
                        <div className="detail">
                          <FaMapMarkerAlt />
                          {hospital.distance_text || `${hospital.distance_km?.toFixed(1)} ${t.kmAway}`}
                        </div>
                        <div className="detail">
                          <FaClock />
                          {hospital.estimated_travel_time || `${Math.round((hospital.distance_km || 0) * 2)} ${t.minsDrive}`}
                        </div>
                        {hospital.has_emergency_room && (
                          <span className="badge">{t.hasER}</span>
                        )}
                        {hospital.is_24x7 && (
                          <span className="badge">{t.open24x7}</span>
                        )}
                      </HospitalDetails>
                    </HospitalCard>
                  ))}
                </HospitalSection>
              )}

              {/* Location Required Warning */}
              {(locationStatus === 'denied' || locationStatus === 'unavailable') && (
                <LocationWarning>
                  <div className="location-icon">📍</div>
                  <div className="location-text">
                    {t.locationRequired || 'Location permission required to find nearby hospitals'}
                  </div>
                  <div className="location-subtext">
                    {t.locationDeniedMessage || 'Please enable location access in your browser to see hospitals near you'}
                  </div>
                  <EnableLocationButton 
                    onClick={() => requestLocation(0, false)}
                    disabled={isRequestingLocation}
                  >
                    <FaMapMarkerAlt />
                    {isRequestingLocation ? (t.gettingLocation || 'Getting location...') : (t.enableLocation || 'Enable Location')}
                  </EnableLocationButton>
                </LocationWarning>
              )}

              {/* Try Again Button */}
              <SecondaryActionButton
                onClick={() => {
                  setTriageResult(null);
                  setSymptoms('');
                  setSelectedQuickSymptoms([]);
                }}
                style={{ marginTop: '1rem' }}
              >
                <FaArrowRight style={{ transform: 'rotate(180deg)' }} />
                <span className="action-text">Assess Different Symptoms</span>
              </SecondaryActionButton>

              {/* Disclaimer */}
              <Disclaimer>
                {t.disclaimer}
              </Disclaimer>
            </>
          )}
        </EmergencyContainer>
      </EmergencyOverlay>
    </AnimatePresence>
  );
};

export default EmergencyTriage;
