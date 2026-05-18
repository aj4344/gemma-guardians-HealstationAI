// 🏥 Welcome Landing Page - HealStation AI: Doctor Assistant Information
import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { 
  FaStethoscope, FaShieldAlt, FaUserMd, FaExclamationTriangle, 
  FaCheckCircle, FaMicrophone, FaUpload, FaGlobe, FaInfoCircle
} from 'react-icons/fa';
import { EmergencyButton } from './EmergencyButton';

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
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #4CAF50, #2196F3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
`;

const Subtitle = styled(motion.p)`
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 2rem;
`;

const Section = styled(motion.div)`
  margin: 2rem 0;
`;

const SectionTitle = styled.h2`
  font-size: 1.5rem;
  color: white;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
`;

const FeatureCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 1.5rem;
  text-align: center;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
  }
  
  transition: all 0.3s ease;
`;

const FeatureIcon = styled.div`
  font-size: 2rem;
  color: #4CAF50;
  margin-bottom: 1rem;
`;

const FeatureTitle = styled.h3`
  font-size: 1.1rem;
  color: white;
  margin-bottom: 0.5rem;
`;

const FeatureDescription = styled.p`
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
`;

const InstructionsList = styled.ul`
  list-style: none;
  padding: 0;
`;

const InstructionItem = styled(motion.li)`
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin: 1rem 0;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border-left: 4px solid #4CAF50;
`;

const StepNumber = styled.div`
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
  flex-shrink: 0;
`;

const StepContent = styled.div`
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  
  strong {
    color: white;
  }
`;

const WarningBox = styled(motion.div)`
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 15px;
  padding: 1.5rem;
  margin: 1rem 0;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
`;

const WarningIcon = styled.div`
  font-size: 1.5rem;
  color: #FFC107;
  flex-shrink: 0;
  margin-top: 0.2rem;
`;

const WarningText = styled.div`
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  
  strong {
    color: #FFC107;
  }
`;

const DisclaimerBox = styled(motion.div)`
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  border-radius: 15px;
  padding: 1.5rem;
  margin: 1rem 0;
  text-align: center;
`;

const DisclaimerText = styled.div`
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  font-size: 0.95rem;
  
  strong {
    color: #f44336;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
  flex-wrap: wrap;
`;

const ActionButton = styled(motion.button)`
  padding: 1rem 2rem;
  border: none;
  border-radius: 15px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &.primary {
    background: linear-gradient(135deg, #4CAF50, #45a049);
    color: white;
    
    &:hover {
      background: linear-gradient(135deg, #45a049, #4CAF50);
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(76, 175, 80, 0.3);
    }
  }
  
  &.secondary {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    
    &:hover {
      background: rgba(255, 255, 255, 0.2);
      transform: translateY(-2px);
    }
  }
`;

export const WelcomeLanding = ({ onGetStarted, onSkip, language = 'en' }) => {
  const features = [
    {
      icon: <FaMicrophone />,
      title: "Voice Input",
      description: "Record your symptoms in your preferred language"
    },
    {
      icon: <FaUpload />,
      title: "File Upload",
      description: "Upload medical images, reports, and test results"
    },
    {
      icon: <FaUserMd />,
      title: "AI Analysis",
      description: "Advanced AI provides comprehensive medical analysis"
    },
    {
      icon: <FaGlobe />,
      title: "Multilingual",
      description: "Available in English, Hindi, and Marathi"
    }
  ];

  const instructions = [
    {
      title: "Record or Type Symptoms",
      content: "Describe your symptoms clearly using voice recording or text input. Include medical history and concerns."
    },
    {
      title: "Upload Medical Files (Optional)",
      content: "Upload relevant medical images, reports, X-rays, or test results for better analysis."
    },
    {
      title: "Get AI Diagnosis",
      content: "Our AI doctor will analyze your input and provide comprehensive medical consultation."
    },
    {
      title: "Find Nearby Doctors",
      content: "If needed, search for nearby medical professionals and facilities based on your diagnosis."
    }
  ];

  return (
    <LandingOverlay
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <LandingContainer
        initial={{ scale: 0.8, y: 50 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ duration: 0.5, type: "spring" }}
      >
        <Header>
          <Logo
            whileHover={{ scale: 1.05, rotate: 5 }}
            whileTap={{ scale: 0.95 }}
          >
            <FaStethoscope />
          </Logo>
          
          <Title
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            HealStation AI: Doctor Assistant
          </Title>
          
          <Subtitle
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            Advanced AI-Powered Medical Consultation Platform
          </Subtitle>
        </Header>

        {/* 🚨 Emergency Button - Quick access for emergencies */}
        <EmergencyButton 
          language={language} 
          showBanner={true} 
          showQuickActions={true}
        />

        <Section>
          <SectionTitle>
            <FaInfoCircle />
            About HealStation AI
          </SectionTitle>
          <p style={{ color: 'rgba(255, 255, 255, 0.8)', lineHeight: 1.6 }}>
            HealStation AI is an advanced artificial intelligence system designed to provide preliminary medical consultation. 
            Our AI analyzes your symptoms, medical history, and uploaded documents to offer comprehensive health insights 
            and recommendations.
          </p>
        </Section>

        <Section>
          <SectionTitle>
            <FaCheckCircle />
            Key Features
          </SectionTitle>
          <FeatureGrid>
            {features.map((feature, index) => (
              <FeatureCard
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                whileHover={{ y: -5 }}
              >
                <FeatureIcon>{feature.icon}</FeatureIcon>
                <FeatureTitle>{feature.title}</FeatureTitle>
                <FeatureDescription>{feature.description}</FeatureDescription>
              </FeatureCard>
            ))}
          </FeatureGrid>
        </Section>

        <Section>
          <SectionTitle>
            <FaUserMd />
            How to Use HealStation AI
          </SectionTitle>
          <InstructionsList>
            {instructions.map((instruction, index) => (
              <InstructionItem
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
              >
                <StepNumber>{index + 1}</StepNumber>
                <StepContent>
                  <strong>{instruction.title}</strong><br />
                  {instruction.content}
                </StepContent>
              </InstructionItem>
            ))}
          </InstructionsList>
        </Section>

        <WarningBox
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.8 }}
        >
          <WarningIcon>
            <FaExclamationTriangle />
          </WarningIcon>
          <WarningText>
            <strong>Important:</strong> HealStation AI provides preliminary medical insights and should not replace professional medical advice. 
            Always consult with qualified healthcare professionals for accurate diagnosis and treatment. Our doctor recommendations 
            are sourced from Google and other public databases - we are not responsible for the accuracy of this information.
          </WarningText>
        </WarningBox>

        <DisclaimerBox
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.9 }}
        >
          <DisclaimerText>
            <strong>Medical Disclaimer:</strong> This AI tool is for educational and informational purposes only. 
            It is not intended to diagnose, treat, cure, or prevent any disease. In case of medical emergencies, 
            contact emergency services immediately. Doctor and hospital recommendations are provided by third-party services 
            and we do not guarantee their accuracy or quality.
          </DisclaimerText>
        </DisclaimerBox>

        <ActionButtons>
          <ActionButton
            className="primary"
            onClick={onGetStarted}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <FaStethoscope />
            Get Started
          </ActionButton>
          
          <ActionButton
            className="secondary"
            onClick={onSkip}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Skip Introduction
          </ActionButton>
        </ActionButtons>
      </LandingContainer>
    </LandingOverlay>
  );
};

export default WelcomeLanding;
