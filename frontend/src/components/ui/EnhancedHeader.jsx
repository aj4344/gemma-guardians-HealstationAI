// 🏥 Enhanced Medical Header with Glass Morphism
import React, { useState } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { FaStethoscope, FaMoon, FaSun, FaGlobe, FaHeartbeat, FaInfoCircle, FaCoffee, FaBars, FaTimes } from 'react-icons/fa';
import { media } from '../../styles/breakpoints';

const HeaderContainer = styled(motion.header)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);

  ${media.md} {
    padding: 0.75rem 1rem;
  }
`;

const LogoSection = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const LogoIcon = styled(motion.div)`
  background: linear-gradient(135deg, #4CAF50, #45a049);
  padding: 0.8rem;
  border-radius: 15px;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);

  ${media.sm} {
    padding: 0.6rem;
    border-radius: 10px;
  }
`;

const LogoText = styled.div`
  h1 {
    margin: 0;
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #4CAF50, #2196F3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;

    ${media.sm} {
      font-size: 1.4rem;
    }
    
    ${media.xs} {
      font-size: 1.2rem;
    }
  }
  
  p {
    margin: 0;
    font-size: 0.9rem;
    color: ${props => props.theme.textSecondary};
    font-weight: 500;
    
    ${media.md} {
      font-size: 0.8rem;
    }
    
    ${media.xs} {
      display: none;
    }
  }
`;

const NavControls = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  
  ${media.md} {
    gap: 0.5rem;
  }
  
  ${media.sm} {
    display: none;
  }
`;

const MobileMenuButton = styled(motion.button)`
  display: none;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 0.7rem;
  color: ${props => props.theme.text};
  cursor: pointer;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  }
  
  ${media.sm} {
    display: flex;
  }
`;

const MobileMenu = styled(motion.div)`
  display: none;
  position: fixed;
  top: 0;
  right: 0;
  width: 80%;
  max-width: 300px;
  height: 100vh;
  background: rgba(30, 30, 30, 0.95);
  backdrop-filter: blur(20px);
  z-index: 200;
  padding: 2rem;
  flex-direction: column;
  gap: 1.5rem;
  
  ${media.sm} {
    display: flex;
  }
`;

const MobileNavControls = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 2rem;
`;

const MobileBackdrop = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 199;
`;

const ControlButton = styled(motion.button)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 0.7rem;
  color: ${props => props.theme.text};
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  }
  
  ${media.md} {
    padding: 0.6rem;
    font-size: 1rem;
  }
`;

const AboutButton = styled(ControlButton)`
  gap: 0.5rem;
  padding: 0.7rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  
  ${media.md} {
    padding: 0.6rem 0.8rem;
    font-size: 0.8rem;
    
    span {
      display: none;
    }
  }
`;

const CoffeeButton = styled(ControlButton)`
  gap: 0.5rem;
  padding: 0.7rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  background: linear-gradient(135deg, rgba(192, 57, 43, 0.2), rgba(230, 126, 34, 0.2));
  border: 1px solid rgba(230, 126, 34, 0.3);
  color: #e67e22;
  
  ${media.md} {
    padding: 0.6rem 0.8rem;
    font-size: 0.8rem;
    
    span {
      display: none;
    }
  }
  
  &:hover {
    background: linear-gradient(135deg, rgba(192, 57, 43, 0.3), rgba(230, 126, 34, 0.3));
    box-shadow: 0 4px 15px rgba(230, 126, 34, 0.2);
  }
`;

const LanguageSelector = styled(motion.select)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 0.5rem 1rem;
  color: ${props => props.theme.text};
  cursor: pointer;
  font-size: 0.9rem;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
  
  option {
    background: ${props => props.theme.cardBg};
    color: ${props => props.theme.text};
  }
`;

const StatusIndicator = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 20px;
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  color: #4CAF50;
`;

const PulseIcon = styled(motion.div)`
  color: #4CAF50;
`;

export const EnhancedHeader = ({ 
  isDarkMode, 
  toggleTheme, 
  language, 
  setLanguage, 
  translations,
  onAboutClick,
  onBuyCoffeeClick
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const languages = [
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'hi', name: 'हिंदी', flag: '🇮🇳' },
    { code: 'mr', name: 'मराठी', flag: '🇮🇳' }
  ];

  return (
    <HeaderContainer
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, type: "spring" }}
    >
      <LogoSection>
        <LogoIcon
          whileHover={{ scale: 1.05, rotate: 5 }}
          whileTap={{ scale: 0.95 }}
        >
          <FaStethoscope size={24} />
        </LogoIcon>
        
        <LogoText>
          <motion.h1
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            {translations?.header || 'HealStation AI: Doctor Assistant'}
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            {translations?.subheader || 'AI-Powered Medical Consultation'}
          </motion.p>
        </LogoText>
      </LogoSection>
      
      {/* Mobile Menu Button */}
      <MobileMenuButton 
        onClick={() => setMobileMenuOpen(true)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <FaBars />
      </MobileMenuButton>
      
      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <MobileBackdrop 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileMenuOpen(false)}
            />
            <MobileMenu
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25 }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <LogoText>
                  <h1>{translations?.header || 'HealStation AI: Doctor Assistant'}</h1>
                </LogoText>
                <ControlButton 
                  onClick={() => setMobileMenuOpen(false)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <FaTimes />
                </ControlButton>
              </div>
              
              <MobileNavControls>
                <AboutButton
                  onClick={() => {
                    onAboutClick();
                    setMobileMenuOpen(false);
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  style={{ width: '100%', justifyContent: 'flex-start', gap: '0.5rem' }}
                >
                  <FaInfoCircle size={16} /> About
                </AboutButton>
                
                <CoffeeButton
                  onClick={() => {
                    onBuyCoffeeClick();
                    setMobileMenuOpen(false);
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  style={{ width: '100%', justifyContent: 'flex-start', gap: '0.5rem' }}
                >
                  <FaCoffee size={16} /> Buy me a coffee
                </CoffeeButton>
                
                <ControlButton
                  onClick={toggleTheme}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  style={{ width: '100%', justifyContent: 'flex-start', gap: '0.5rem', marginTop: '1rem' }}
                >
                  {isDarkMode ? <FaSun size={16} /> : <FaMoon size={16} />} 
                  {isDarkMode ? "Light Mode" : "Dark Mode"}
                </ControlButton>
              </MobileNavControls>
            </MobileMenu>
          </>
        )}
      </AnimatePresence>

      <NavControls>
        <AboutButton
          onClick={onAboutClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <FaInfoCircle size={16} /> About
        </AboutButton>
        
        <CoffeeButton
          onClick={onBuyCoffeeClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <FaCoffee size={16} /> Buy me a coffee
        </CoffeeButton>
      
        <StatusIndicator
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
        >
          <PulseIcon
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.7, 1, 0.7]
            }}
            transition={{ 
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <FaHeartbeat />
          </PulseIcon>
          AI Online
        </StatusIndicator>

        <LanguageSelector
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          whileHover={{ scale: 1.02 }}
        >
          {languages.map(lang => (
            <option key={lang.code} value={lang.code}>
              {lang.flag} {lang.name}
            </option>
          ))}
        </LanguageSelector>

        <ControlButton
          onClick={toggleTheme}
          whileHover={{ scale: 1.1, rotate: 15 }}
          whileTap={{ scale: 0.9 }}
        >
          {isDarkMode ? <FaSun /> : <FaMoon />}
        </ControlButton>
      </NavControls>
    </HeaderContainer>
  );
};

export default EnhancedHeader;
