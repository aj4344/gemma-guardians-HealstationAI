// AboutSection.jsx - Modern About Us modal with glass morphism effects
import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaTimes, FaStethoscope, FaCode, FaRobot, FaGlobeAsia } from 'react-icons/fa';
import { media } from '../../styles/breakpoints';

// Glass Morphism Modal Backdrop
const Backdrop = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
`;

// Glass Morphism Modal Container
const ModalContainer = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 25px;
  padding: 2rem;
  max-width: 750px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  color: ${props => props.theme.text};
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  
  ${media.md} {
    padding: 1.5rem;
    border-radius: 20px;
  }
  
  ${media.sm} {
    padding: 1.2rem;
    border-radius: 15px;
    max-height: 85vh;
  }
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  ${media.md} {
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
  }
  
  ${media.sm} {
    margin-bottom: 1rem;
    padding-bottom: 0.7rem;
  }
`;

const Title = styled.h2`
  font-size: 2rem;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #4CAF50, #2196F3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  
  ${media.md} {
    font-size: 1.7rem;
  }
  
  ${media.sm} {
    font-size: 1.5rem;
    gap: 0.3rem;
  }
`;

const CloseButton = styled.button`
  background: transparent;
  border: none;
  color: ${props => props.theme.text};
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: scale(1.1);
  }
`;

const Content = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  
  ${media.md} {
    gap: 1.2rem;
  }
  
  ${media.sm} {
    gap: 1rem;
  }
`;

const Section = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  
  ${media.sm} {
    gap: 0.6rem;
  }
`;

const SectionTitle = styled.h3`
  font-size: 1.5rem;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: ${props => props.theme.text};
  
  ${media.md} {
    font-size: 1.3rem;
    gap: 0.6rem;
  }
  
  ${media.sm} {
    font-size: 1.2rem;
    gap: 0.5rem;
  }
`;

const SectionContent = styled.div`
  font-size: 1rem;
  line-height: 1.8;
  color: ${props => props.theme.textSecondary};
`;

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
  
  ${media.md} {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 1.2rem;
  }
  
  ${media.sm} {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
`;

const FeatureCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  padding: 1.25rem;
  border-radius: 15px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  
  &:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-3px);
  }
  
  transition: all 0.3s ease;
`;

const FeatureTitle = styled.h4`
  font-size: 1.2rem;
  margin: 0;
  color: ${props => props.theme.text};
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const FeatureDescription = styled.p`
  font-size: 0.9rem;
  margin: 0;
  color: ${props => props.theme.textSecondary};
  line-height: 1.6;
`;

const IconContainer = styled.div`
  background: linear-gradient(135deg, #4CAF50, #2196F3);
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
`;

const AboutSection = ({ onClose }) => {
  return (
    <Backdrop
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <ModalContainer
        onClick={(e) => e.stopPropagation()}
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        transition={{ type: "spring", damping: 20 }}
      >
        <ModalHeader>
          <Title>
            <FaStethoscope size={30} /> About HealStation AI
          </Title>
          <CloseButton onClick={onClose}>
            <FaTimes />
          </CloseButton>
        </ModalHeader>
        
        <Content>
          <Section>
            <SectionTitle><FaRobot /> Our Mission</SectionTitle>
            <SectionContent>
              HealStation AI — Emergency Triage Assistant is an offline-first clinical triage tool for frontline health
              workers in rural India. Powered by Gemma 4, running entirely on your device. No internet required.
              No data sent anywhere. Built for the Google Gemma 4 Impact Challenge 2026.
            </SectionContent>
          </Section>

          <Section>
            <SectionTitle><FaGlobeAsia /> Key Features</SectionTitle>
            <FeatureGrid>
              <FeatureCard>
                <IconContainer>
                  <FaGlobeAsia color="white" size={20} />
                </IconContainer>
                <FeatureTitle>Multilingual Support</FeatureTitle>
                <FeatureDescription>
                  Full support for English, Hindi, and Marathi — ASHA workers can describe symptoms in their own language.
                </FeatureDescription>
              </FeatureCard>

              <FeatureCard>
                <IconContainer>
                  <FaRobot color="white" size={20} />
                </IconContainer>
                <FeatureTitle>Gemma 4 — Fully Offline</FeatureTitle>
                <FeatureDescription>
                  Runs Gemma 4 (gemma4:e2b) locally via Ollama. No cloud API. No internet. Patient data never leaves the device.
                </FeatureDescription>
              </FeatureCard>

              <FeatureCard>
                <IconContainer>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                    <path d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3M9.5 11.5C9.5 12.3 8.8 13 8 13H7V15H5.5V9H8C8.8 9 9.5 9.7 9.5 10.5V11.5M14.5 15H13V13.5H11.5V15H10V9H11.5V12H13V9H14.5V15M19 12.5C19 13.9 17.9 15 16.5 15H14V9H16.5C17.9 9 19 10.1 19 11.5V12.5M16.5 10.5H15.5V13.5H16.5C17.1 13.5 17.5 13.1 17.5 12.5V11.5C17.5 10.9 17.1 10.5 16.5 10.5Z" />
                  </svg>
                </IconContainer>
                <FeatureTitle>Clinical Protocols</FeatureTitle>
                <FeatureDescription>
                  Validated HEART Score (chest pain), BE-FAST (stroke), and Trauma Score protocols. Validated by practicing physicians.
                </FeatureDescription>
              </FeatureCard>

              <FeatureCard>
                <IconContainer>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                    <path d="M22,5.5V7H23V13H22V14.5C22,16.43 20.43,18 18.5,18H5.5C3.57,18 2,16.43 2,14.5V9.5C2,7.57 3.57,6 5.5,6H9V5.5A1.5,1.5 0 0,1 10.5,4H13.5A1.5,1.5 0 0,1 15,5.5V6H18.5A3.5,3.5 0 0,1 22,9.5V5.5M4,12V14.5A1.5,1.5 0 0,0 5.5,16H18.5A1.5,1.5 0 0,0 20,14.5V9.5A1.5,1.5 0 0,0 18.5,8H5.5A1.5,1.5 0 0,0 4,9.5V12M11,10H13V12H15V14H13V16H11V14H9V12H11V10M13,5.5V6H10.5V5.5H13Z" />
                  </svg>
                </IconContainer>
                <FeatureTitle>Offline Hospital Routing</FeatureTitle>
                <FeatureDescription>
                  Static hospital database works without internet. No external services required.
                </FeatureDescription>
              </FeatureCard>
            </FeatureGrid>
          </Section>

          <Section>
            <SectionTitle><FaCode /> Technology Stack</SectionTitle>
            <SectionContent>
              React + FastAPI frontend and backend. Gemma 4 (gemma4:e2b) via Ollama for local inference.
              faster-whisper for offline speech-to-text. pyttsx3 for offline TTS. Fully reproducible — clone, install, run.
            </SectionContent>
          </Section>

          <Section>
            <SectionTitle>Important Disclaimer</SectionTitle>
            <SectionContent>
              <strong>HealStation AI is designed for educational and triage-assistance purposes only.</strong> It does not
              replace professional medical diagnosis or treatment. Always consult a qualified healthcare provider.
              In emergencies, call 108 (ambulance) or 112 immediately.
            </SectionContent>
          </Section>
        </Content>
      </ModalContainer>
    </Backdrop>
  );
};

export default AboutSection;
