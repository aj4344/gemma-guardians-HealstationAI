// DisclaimerModal.jsx - Comprehensive disclaimer and consent popup
import React, { useState } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FaExclamationTriangle, FaCheckCircle, FaUserMd, FaLock, 
  FaTrash, FaMicrophone, FaUpload, FaStethoscope
} from 'react-icons/fa';

const Backdrop = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 1rem;
`;

const ModalContainer = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 25px;
  padding: 2rem;
  max-width: 600px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  color: ${props => props.theme?.text || 'white'};
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  
  @media (max-width: 768px) {
    padding: 1.5rem;
    max-height: 90vh;
  }
  
  /* Custom scrollbar */
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 1.5rem;
`;

const IconContainer = styled.div`
  background: linear-gradient(135deg, #FF9800, #F44336);
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 2.5rem;
  color: white;
  box-shadow: 0 8px 25px rgba(244, 67, 54, 0.3);
`;

const Title = styled.h2`
  margin: 0 0 0.5rem 0;
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #FF9800, #F44336);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const Subtitle = styled.p`
  margin: 0;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.7);
`;

const ContentSection = styled.div`
  margin: 1.5rem 0;
`;

const SectionTitle = styled.h3`
  font-size: 1.2rem;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: ${props => props.$color || 'inherit'};
  
  svg {
    font-size: 1.3rem;
  }
`;

const InfoBox = styled.div`
  background: ${props => props.$background || 'rgba(255, 255, 255, 0.05)'};
  border: 1px solid ${props => props.$border || 'rgba(255, 255, 255, 0.1)'};
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
`;

const InfoList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
`;

const InfoItem = styled.li`
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin: 0.75rem 0;
  font-size: 0.95rem;
  line-height: 1.5;
  
  svg {
    color: ${props => props.$color || '#4CAF50'};
    margin-top: 0.2rem;
    flex-shrink: 0;
  }
`;

const WarningBox = styled(InfoBox)`
  background: rgba(255, 152, 0, 0.1);
  border-color: rgba(255, 152, 0, 0.3);
`;

const PrivacyBox = styled(InfoBox)`
  background: rgba(76, 175, 80, 0.1);
  border-color: rgba(76, 175, 80, 0.3);
`;

const HowToSection = styled.div`
  background: rgba(33, 150, 243, 0.1);
  border: 1px solid rgba(33, 150, 243, 0.3);
  border-radius: 12px;
  padding: 1.2rem;
  margin: 1.5rem 0;
`;

const StepList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
`;

const Step = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
`;

const StepNumber = styled.div`
  background: linear-gradient(135deg, #2196F3, #1976D2);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
`;

const StepContent = styled.div`
  flex: 1;
  
  strong {
    display: block;
    margin-bottom: 0.25rem;
    color: #2196F3;
  }
  
  span {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.8);
  }
`;

const ConsentSection = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1.2rem;
  margin: 1.5rem 0;
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
  font-size: 0.95rem;
  line-height: 1.5;
  
  input[type="checkbox"] {
    margin-top: 0.2rem;
    cursor: pointer;
    width: 18px;
    height: 18px;
    accent-color: #4CAF50;
  }
  
  &:hover {
    color: rgba(255, 255, 255, 1);
  }
`;

const ButtonContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 2rem;
`;

const AcceptButton = styled(motion.button)`
  background: linear-gradient(135deg, #4CAF50, #45a049);
  border: none;
  border-radius: 12px;
  padding: 1rem 2rem;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.3);
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #45a049, #4CAF50);
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(76, 175, 80, 0.4);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const DisclaimerModal = ({ onAccept, language = 'en' }) => {
  const [hasConsented, setHasConsented] = useState(false);

  const translations = {
    en: {
      title: "Important Disclaimer & Privacy Notice",
      subtitle: "Please read carefully before using HealStation AI",
      medicalDisclaimer: "Medical Disclaimer",
      privacyNotice: "Privacy & Data Protection",
      howToUse: "How to Use HealStation AI",
      consent: "User Consent",
      acceptButton: "I Understand & Accept",
      warnings: [
        "This is an AI-powered tool for educational and informational purposes ONLY",
        "NOT a substitute for professional medical advice, diagnosis, or treatment",
        "ALWAYS seek the advice of qualified healthcare professionals",
        "Never disregard professional medical advice or delay seeking it based on AI suggestions",
        "In case of emergency, call emergency services immediately"
      ],
      privacy: [
        "We DO NOT store your medical data, images, or personal information",
        "All consultations are processed in real-time and NOT saved to any database",
        "Your location is used only to find nearby doctors and is NOT stored",
        "Audio recordings are processed for transcription and immediately deleted",
        "Your data remains private and secure during your session"
      ],
      steps: [
        { title: "Record or Type Symptoms", desc: "Describe your symptoms using voice or text" },
        { title: "Upload Medical Files (Optional)", desc: "Add images, reports, or test results" },
        { title: "Get AI Triage Assessment", desc: "Receive preliminary medical analysis" },
        { title: "Find Nearby Doctors", desc: "Get recommendations for specialists in your area" }
      ],
      consentText: "I understand this is an educational tool, not medical advice. I agree that my data is not stored and I will seek professional medical consultation for actual health concerns."
    },
    hi: {
      title: "महत्वपूर्ण अस्वीकरण और गोपनीयता सूचना",
      subtitle: "HealStation AI का उपयोग करने से पहले कृपया ध्यान से पढ़ें",
      medicalDisclaimer: "चिकित्सा अस्वीकरण",
      privacyNotice: "गोपनीयता और डेटा सुरक्षा",
      howToUse: "HealStation AI का उपयोग कैसे करें",
      consent: "उपयोगकर्ता सहमति",
      acceptButton: "मैं समझता हूं और स्वीकार करता हूं",
      warnings: [
        "यह केवल शैक्षिक और सूचनात्मक उद्देश्यों के लिए एक AI-संचालित उपकरण है",
        "पेशेवर चिकित्सा सलाह, निदान या उपचार का विकल्प नहीं है",
        "हमेशा योग्य स्वास्थ्य पेशेवरों की सलाह लें",
        "AI सुझावों के आधार पर पेशेवर चिकित्सा सलाह को कभी अनदेखा न करें",
        "आपातकाल की स्थिति में तुरंत आपातकालीन सेवाओं को कॉल करें"
      ],
      privacy: [
        "हम आपके चिकित्सा डेटा, छवियों या व्यक्तिगत जानकारी को संग्रहीत नहीं करते हैं",
        "सभी परामर्श वास्तविक समय में संसाधित किए जाते हैं और किसी भी डेटाबेस में सहेजे नहीं जाते हैं",
        "आपके स्थान का उपयोग केवल पास के डॉक्टरों को खोजने के लिए किया जाता है और संग्रहीत नहीं किया जाता",
        "ऑडियो रिकॉर्डिंग ट्रांसक्रिप्शन के लिए संसाधित की जाती हैं और तुरंत हटा दी जाती हैं",
        "आपका डेटा आपके सत्र के दौरान निजी और सुरक्षित रहता है"
      ],
      steps: [
        { title: "लक्षण रिकॉर्ड या टाइप करें", desc: "आवाज या टेक्स्ट का उपयोग करके अपने लक्षणों का वर्णन करें" },
        { title: "चिकित्सा फाइलें अपलोड करें (वैकल्पिक)", desc: "छवियां, रिपोर्ट या परीक्षण परिणाम जोड़ें" },
        { title: "AI ट्राइएज मूल्यांकन प्राप्त करें", desc: "प्रारंभिक चिकित्सा विश्लेषण प्राप्त करें" },
        { title: "पास के डॉक्टर खोजें", desc: "अपने क्षेत्र में विशेषज्ञों की सिफारिशें प्राप्त करें" }
      ],
      consentText: "मैं समझता हूं कि यह एक शैक्षिक उपकरण है, चिकित्सा सलाह नहीं। मैं सहमत हूं कि मेरा डेटा संग्रहीत नहीं है और मैं वास्तविक स्वास्थ्य चिंताओं के लिए पेशेवर चिकित्सा परामर्श लूंगा।"
    },
    mr: {
      title: "महत्त्वाचे अस्वीकरण आणि गोपनीयता सूचना",
      subtitle: "HealStation AI वापरण्यापूर्वी कृपया काळजीपूर्वक वाचा",
      medicalDisclaimer: "वैद्यकीय अस्वीकरण",
      privacyNotice: "गोपनीयता आणि डेटा संरक्षण",
      howToUse: "HealStation AI कसे वापरावे",
      consent: "वापरकर्ता संमती",
      acceptButton: "मला समजले आणि मी स्वीकारतो",
      warnings: [
        "हे केवळ शैक्षणिक आणि माहितीपूर्ण उद्देशांसाठी AI-चालित साधन आहे",
        "व्यावसायिक वैद्यकीय सल्ला, निदान किंवा उपचाराचा पर्याय नहीं",
        "नेहमी पात्र आरोग्य व्यावसायिकांचा सल्ला घ्या",
        "AI सूचनांच्या आधारे व्यावसायिक वैद्यकीय सल्ल्याकडे कधीही दुर्लक्ष करू नका",
        "आणीबाणीच्या परिस्थितीत तात्काळ आपत्कालीन सेवांना कॉल करा"
      ],
      privacy: [
        "आम्ही तुमचा वैद्यकीय डेटा, प्रतिमा किंवा वैयक्तिक माहिती संग्रहित करत नाही",
        "सर्व सल्लामसलत रिअल-टाइममध्ये प्रक्रिया केली जाते आणि कोणत्याही डेटाबेसमध्ये जतन केली जात नाही",
        "तुमचे स्थान फक्त जवळच्या डॉक्टरांना शोधण्यासाठी वापरले जाते आणि संग्रहीत केले जात नाही",
        "ऑडिओ रेकॉर्डिंग ट्रान्सक्रिप्शनसाठी प्रक्रिया केली जाते आणि लगेच हटवली जाते",
        "तुमचा डेटा तुमच्या सत्रादरम्यान खाजगी आणि सुरक्षित राहतो"
      ],
      steps: [
        { title: "लक्षणे रेकॉर्ड किंवा टाइप करा", desc: "आवाज किंवा मजकूर वापरून तुमच्या लक्षणांचे वर्णन करा" },
        { title: "वैद्यकीय फाइल अपलोड करा (वैकल्पिक)", desc: "प्रतिमा, अहवाल किंवा चाचणी परिणाम जोडा" },
        { title: "AI ट्राइएज मूल्यांकन मिळवा", desc: "प्राथमिक वैद्यकीय विश्लेषण मिळवा" },
        { title: "जवळील डॉक्टर शोधा", desc: "तुमच्या क्षेत्रातील तज्ञांसाठी शिफारसी मिळवा" }
      ],
      consentText: "मला समजते की हे एक शैक्षणिक साधन आहे, वैद्यकीय सल्ला नाही. मी सहमत आहे की माझा डेटा संग्रहीत नाही आणि मी वास्तविक आरोग्य चिंतेसाठी व्यावसायिक वैद्यकीय सल्ला घेईन."
    }
  };

  const t = translations[language] || translations.en;

  return (
    <AnimatePresence>
      <Backdrop
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <ModalContainer
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          transition={{ duration: 0.3 }}
        >
          <Header>
            <IconContainer>
              <FaExclamationTriangle />
            </IconContainer>
            <Title>{t.title}</Title>
            <Subtitle>{t.subtitle}</Subtitle>
          </Header>

          {/* Medical Disclaimer */}
          <ContentSection>
            <SectionTitle $color="#FF9800">
              <FaUserMd />
              {t.medicalDisclaimer}
            </SectionTitle>
            <WarningBox>
              <InfoList>
                {t.warnings.map((warning, index) => (
                  <InfoItem key={index} $color="#FF9800">
                    <FaExclamationTriangle />
                    <span>{warning}</span>
                  </InfoItem>
                ))}
              </InfoList>
            </WarningBox>
          </ContentSection>

          {/* Privacy Notice */}
          <ContentSection>
            <SectionTitle $color="#4CAF50">
              <FaLock />
              {t.privacyNotice}
            </SectionTitle>
            <PrivacyBox>
              <InfoList>
                {t.privacy.map((item, index) => (
                  <InfoItem key={index} $color="#4CAF50">
                    <FaCheckCircle />
                    <span>{item}</span>
                  </InfoItem>
                ))}
              </InfoList>
            </PrivacyBox>
          </ContentSection>

          {/* How to Use */}
          <HowToSection>
            <SectionTitle $color="#2196F3">
              <FaStethoscope />
              {t.howToUse}
            </SectionTitle>
            <StepList>
              {t.steps.map((step, index) => (
                <Step key={index}>
                  <StepNumber>{index + 1}</StepNumber>
                  <StepContent>
                    <strong>{step.title}</strong>
                    <span>{step.desc}</span>
                  </StepContent>
                </Step>
              ))}
            </StepList>
          </HowToSection>

          {/* Consent Checkbox */}
          <ConsentSection>
            <SectionTitle $color="white">
              <FaCheckCircle />
              {t.consent}
            </SectionTitle>
            <CheckboxLabel>
              <input
                type="checkbox"
                checked={hasConsented}
                onChange={(e) => setHasConsented(e.target.checked)}
              />
              <span>{t.consentText}</span>
            </CheckboxLabel>
          </ConsentSection>

          {/* Accept Button */}
          <ButtonContainer>
            <AcceptButton
              onClick={onAccept}
              disabled={!hasConsented}
              whileHover={hasConsented ? { scale: 1.02 } : {}}
              whileTap={hasConsented ? { scale: 0.98 } : {}}
            >
              <FaCheckCircle />
              {t.acceptButton}
            </AcceptButton>
          </ButtonContainer>
        </ModalContainer>
      </Backdrop>
    </AnimatePresence>
  );
};

export default DisclaimerModal;
