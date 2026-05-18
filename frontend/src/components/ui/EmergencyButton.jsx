// 🚨 Emergency Button Component - Quick access to emergency services
import React, { useState } from 'react';
import styled, { keyframes } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { FaExclamationTriangle, FaAmbulance, FaPhoneAlt, FaTimes } from 'react-icons/fa';
import EmergencyTriage from './EmergencyTriage';

// ============ ANIMATIONS ============
const pulse = keyframes`
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7);
  }
  50% { 
    transform: scale(1.02);
    box-shadow: 0 0 0 10px rgba(220, 38, 38, 0);
  }
`;

const emergencyGlow = keyframes`
  0%, 100% { 
    box-shadow: 0 4px 20px rgba(220, 38, 38, 0.4);
  }
  50% { 
    box-shadow: 0 4px 30px rgba(220, 38, 38, 0.6);
  }
`;

// ============ STYLED COMPONENTS ============
const EmergencyButtonContainer = styled(motion.div)`
  position: relative;
  width: 100%;
  margin: 1.5rem 0;
`;

const MainEmergencyButton = styled(motion.button)`
  width: 100%;
  padding: 1.25rem 1.5rem;
  background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
  border: 2px solid #EF4444;
  border-radius: 16px;
  color: white;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  transition: all 0.3s ease;
  animation: ${emergencyGlow} 2s ease-in-out infinite;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.2),
      transparent
    );
    transition: left 0.5s;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(220, 38, 38, 0.5);
    
    &::before {
      left: 100%;
    }
  }

  &:active {
    transform: translateY(0);
  }

  svg {
    font-size: 1.4rem;
  }

  .emergency-text {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
  }

  .primary-text {
    font-size: 1.1rem;
    font-weight: 700;
  }

  .secondary-text {
    font-size: 0.75rem;
    opacity: 0.9;
    font-weight: 400;
  }
`;

const QuickActionsRow = styled.div`
  display: flex;
  gap: 0.75rem;
  margin-top: 0.75rem;
`;

const QuickActionButton = styled(motion.a)`
  flex: 1;
  padding: 0.75rem 1rem;
  background: rgba(220, 38, 38, 0.15);
  border: 1px solid rgba(220, 38, 38, 0.3);
  border-radius: 12px;
  color: #EF4444;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  text-decoration: none;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(220, 38, 38, 0.25);
    border-color: rgba(220, 38, 38, 0.5);
    transform: translateY(-1px);
  }

  svg {
    font-size: 1rem;
  }
`;

const EmergencyBanner = styled(motion.div)`
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.2) 0%, rgba(185, 28, 28, 0.2) 100%);
  border: 1px solid rgba(220, 38, 38, 0.3);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
`;

const BannerIcon = styled.div`
  width: 40px;
  height: 40px;
  background: #DC2626;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.2rem;
  flex-shrink: 0;
`;

const BannerContent = styled.div`
  flex: 1;
`;

const BannerTitle = styled.div`
  color: #EF4444;
  font-weight: 700;
  font-size: 0.95rem;
  margin-bottom: 0.2rem;
`;

const BannerText = styled.div`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
`;

// ============ TRANSLATIONS ============
const translations = {
  en: {
    emergencyButton: "🚨 EMERGENCY? Get Instant Help",
    emergencySubtext: "AI-powered emergency assessment & hospital routing",
    call108: "Call 108",
    assessSymptoms: "Assess Symptoms",
    bannerTitle: "Medical Emergency?",
    bannerText: "Get instant AI triage and find the nearest hospital"
  },
  hi: {
    emergencyButton: "🚨 आपातकाल? तुरंत मदद पाएं",
    emergencySubtext: "AI-संचालित आपातकालीन मूल्यांकन और अस्पताल रूटिंग",
    call108: "108 कॉल करें",
    assessSymptoms: "लक्षण जांचें",
    bannerTitle: "चिकित्सा आपातकाल?",
    bannerText: "तुरंत AI ट्राइएज प्राप्त करें और निकटतम अस्पताल खोजें"
  },
  mr: {
    emergencyButton: "🚨 आणीबाणी? त्वरित मदत मिळवा",
    emergencySubtext: "AI-संचालित आणीबाणी मूल्यांकन आणि रुग्णालय रूटिंग",
    call108: "108 वर कॉल करा",
    assessSymptoms: "लक्षणे तपासा",
    bannerTitle: "वैद्यकीय आणीबाणी?",
    bannerText: "त्वरित AI ट्रायेज मिळवा आणि जवळचे रुग्णालय शोधा"
  }
};

// ============ MAIN COMPONENT ============
export const EmergencyButton = ({ 
  language = 'en',
  showBanner = true,
  showQuickActions = true,
  compact = false,
  apiBaseUrl = 'http://127.0.0.1:8001'
}) => {
  const [isTriageOpen, setIsTriageOpen] = useState(false);
  const t = translations[language] || translations.en;

  return (
    <>
      <EmergencyButtonContainer
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        {showBanner && !compact && (
          <EmergencyBanner>
            <BannerIcon>
              <FaAmbulance />
            </BannerIcon>
            <BannerContent>
              <BannerTitle>{t.bannerTitle}</BannerTitle>
              <BannerText>{t.bannerText}</BannerText>
            </BannerContent>
          </EmergencyBanner>
        )}

        <MainEmergencyButton
          onClick={() => setIsTriageOpen(true)}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          <FaExclamationTriangle />
          <div className="emergency-text">
            <span className="primary-text">{t.emergencyButton}</span>
            {!compact && (
              <span className="secondary-text">{t.emergencySubtext}</span>
            )}
          </div>
        </MainEmergencyButton>

        {showQuickActions && !compact && (
          <QuickActionsRow>
            <QuickActionButton
              href="tel:108"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <FaPhoneAlt />
              {t.call108}
            </QuickActionButton>
            <QuickActionButton
              as="button"
              onClick={() => setIsTriageOpen(true)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <FaAmbulance />
              {t.assessSymptoms}
            </QuickActionButton>
          </QuickActionsRow>
        )}
      </EmergencyButtonContainer>

      {/* Emergency Triage Modal */}
      <EmergencyTriage
        isOpen={isTriageOpen}
        onClose={() => setIsTriageOpen(false)}
        language={language}
        apiBaseUrl={apiBaseUrl}
      />
    </>
  );
};

// ============ FLOATING EMERGENCY BUTTON ============
const FloatingButtonContainer = styled(motion.div)`
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 9999;
`;

const FloatingButton = styled(motion.button)`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
  border: 2px solid #EF4444;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(220, 38, 38, 0.5);
  animation: ${pulse} 2s infinite;

  &:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 30px rgba(220, 38, 38, 0.6);
  }
`;

const FloatingLabel = styled(motion.div)`
  position: absolute;
  right: 70px;
  top: 50%;
  transform: translateY(-50%);
  background: #DC2626;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 4px 15px rgba(220, 38, 38, 0.3);

  &::after {
    content: '';
    position: absolute;
    right: -8px;
    top: 50%;
    transform: translateY(-50%);
    border: 4px solid transparent;
    border-left-color: #DC2626;
  }
`;

export const FloatingEmergencyButton = ({
  language = 'en',
  apiBaseUrl = 'http://127.0.0.1:8001'
}) => {
  const [isTriageOpen, setIsTriageOpen] = useState(false);
  const [showLabel, setShowLabel] = useState(true);
  const t = translations[language] || translations.en;

  // Hide label after 5 seconds
  React.useEffect(() => {
    const timer = setTimeout(() => setShowLabel(false), 5000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      <FloatingButtonContainer>
        <AnimatePresence>
          {showLabel && (
            <FloatingLabel
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              {t.bannerTitle}
            </FloatingLabel>
          )}
        </AnimatePresence>
        
        <FloatingButton
          onClick={() => setIsTriageOpen(true)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onMouseEnter={() => setShowLabel(true)}
          onMouseLeave={() => setShowLabel(false)}
        >
          <FaAmbulance />
        </FloatingButton>
      </FloatingButtonContainer>

      <EmergencyTriage
        isOpen={isTriageOpen}
        onClose={() => setIsTriageOpen(false)}
        language={language}
        apiBaseUrl={apiBaseUrl}
      />
    </>
  );
};

export default EmergencyButton;
