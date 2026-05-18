// 🔄 Enhanced Loading Component with Medical Animations
import React from 'react';
import styled, { keyframes } from 'styled-components';
import { motion } from 'framer-motion';

// Animations
const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const progress = keyframes`
  0% { width: 0%; }
  50% { width: 75%; }
  100% { width: 100%; }
`;

const pulse = keyframes`
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
`;

// Styled Components
const LoadingOverlay = styled(motion.div)`
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

const LoadingContainer = styled(motion.div)`
  text-align: center;
  padding: 3rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  max-width: 400px;
  width: 90%;
`;

const MedicalSpinner = styled.div`
  width: 80px;
  height: 80px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top: 4px solid #4CAF50;
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
  margin: 0 auto 2rem;
  position: relative;
  
  &::before {
    content: '🩺';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.5rem;
    animation: ${pulse} 2s ease-in-out infinite;
  }
`;

const LoadingTitle = styled(motion.h2)`
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: white;
  font-weight: 600;
`;

const LoadingSubtext = styled(motion.p)`
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 1rem;
`;

const ProgressContainer = styled.div`
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  margin: 1rem auto;
  overflow: hidden;
`;

const ProgressBar = styled(motion.div)`
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #81C784);
  border-radius: 3px;
  animation: ${progress} 2s ease-in-out infinite;
`;

const StepsContainer = styled.div`
  text-align: left;
  margin-top: 2rem;
`;

const Step = styled(motion.div)`
  display: flex;
  align-items: center;
  margin: 0.5rem 0;
  color: ${props => props.$active ? '#4CAF50' : 'rgba(255, 255, 255, 0.6)'};
  transition: all 0.3s ease;
  
  .icon {
    margin-right: 1rem;
    width: 20px;
    font-size: 1.2rem;
  }
  
  .text {
    font-size: 0.9rem;
  }
`;

// Enhanced Loading Component
export const DiagnosisLoading = ({ stage, message }) => {
  const stages = [
    { id: 'analyzing', icon: '🧠', text: 'Analyzing symptoms and medical data...' },
    { id: 'generating', icon: '📝', text: 'Generating comprehensive diagnosis...' },
    { id: 'audio', icon: '🎵', text: 'Creating audio response...' },
    { id: 'finalizing', icon: '✅', text: 'Finalizing diagnosis...' }
  ];

  const currentStageIndex = stages.findIndex(s => s.id === stage);

  return (
    <LoadingOverlay
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <LoadingContainer
        initial={{ scale: 0.8, y: 50 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ duration: 0.5, type: "spring" }}
      >
        <MedicalSpinner />
        
        <LoadingTitle
          animate={{ opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          🩺 AI Doctor is Working
        </LoadingTitle>
        
        <LoadingSubtext>
          {message || 'Processing your medical consultation...'}
        </LoadingSubtext>
        
        <ProgressContainer>
          <ProgressBar />
        </ProgressContainer>
        
        <StepsContainer>
          {stages.map((step, index) => (
            <Step 
              key={step.id} 
              $active={currentStageIndex >= index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ 
                opacity: currentStageIndex >= index ? 1 : 0.6,
                x: 0
              }}
              transition={{ delay: index * 0.1 }}
            >
              <motion.span 
                className="icon"
                animate={currentStageIndex === index ? { 
                  scale: [1, 1.2, 1],
                  rotate: [0, 5, -5, 0]
                } : {}}
                transition={{ duration: 1, repeat: Infinity }}
              >
                {step.icon}
              </motion.span>
              <span className="text">{step.text}</span>
            </Step>
          ))}
        </StepsContainer>
      </LoadingContainer>
    </LoadingOverlay>
  );
};

export default DiagnosisLoading;
