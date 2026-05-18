// 🏥 Quick Welcome Landing - HealStation AI: Doctor Assistant
import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { 
  FaStethoscope, FaExclamationTriangle, FaCheckCircle, 
  FaMicrophone, FaUpload, FaUserMd
} from 'react-icons/fa';

const LandingOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(15px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
`;

const LandingContainer = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 25px;
  padding: 2.5rem;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 2rem;
`;

const Logo = styled(motion.div)`
  background: linear-gradient(135deg, #4CAF50, #45a049);
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 2rem;
  color: white;
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.3);
`;

const Title = styled(motion.h1)`
  font-size: 2.2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #4CAF50, #2196F3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
`;

const Subtitle = styled(motion.p)`
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 2rem;
`;

const QuickFeatures = styled.div`
  display: flex;
  justify-content: space-around;
  margin: 1.5rem 0;
`;

const FeatureItem = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.9);
  
  svg {
    font-size: 1.5rem;
  }
`;

const DisclaimerBox = styled.div`
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 10px;
  padding: 1rem;
  margin: 1.5rem 0;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
`;

const DisclaimerText = styled.p`
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.4;
  text-align: left;
`;

const ButtonContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 2rem;
`;

const GetStartedButton = styled(motion.button)`
  background: linear-gradient(135deg, #4CAF50, #45a049);
  border: none;
  border-radius: 15px;
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
  
  &:hover {
    background: linear-gradient(135deg, #45a049, #4CAF50);
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(76, 175, 80, 0.4);
  }
`;

const SkipButton = styled(motion.button)`
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 15px;
  padding: 0.8rem 2rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.5);
    color: white;
  }
`;

export const QuickWelcome = ({ onGetStarted, onSkip }) => {
  return (
    <LandingOverlay
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <LandingContainer
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <Header>
          <Logo
            initial={{ rotateY: -180 }}
            animate={{ rotateY: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <FaStethoscope />
          </Logo>
          
          <Title
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            HealStation AI: Doctor Assistant
          </Title>
          
          <Subtitle
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            AI-Powered Medical Consultation
          </Subtitle>
        </Header>

        <QuickFeatures>
          <FeatureItem>
            <FaMicrophone style={{ color: '#4CAF50' }} />
            <span>Voice Input</span>
          </FeatureItem>
          <FeatureItem>
            <FaUpload style={{ color: '#2196F3' }} />
            <span>File Upload</span>
          </FeatureItem>
          <FeatureItem>
            <FaUserMd style={{ color: '#FF9800' }} />
            <span>AI Analysis</span>
          </FeatureItem>
        </QuickFeatures>

        <DisclaimerBox>
          <FaExclamationTriangle style={{ color: '#FFC107', fontSize: '1.2rem', marginTop: '0.2rem' }} />
          <DisclaimerText>
            This AI provides medical information for reference only. 
            Always consult healthcare professionals for actual medical advice.
          </DisclaimerText>
        </DisclaimerBox>

        <ButtonContainer>
          <GetStartedButton
            onClick={onGetStarted}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <FaCheckCircle />
            Let's Go!
          </GetStartedButton>
          
          <SkipButton
            onClick={onSkip}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Skip Tutorial
          </SkipButton>
        </ButtonContainer>
      </LandingContainer>
    </LandingOverlay>
  );
};
