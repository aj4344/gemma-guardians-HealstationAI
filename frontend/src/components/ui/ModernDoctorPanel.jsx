// Enhanced Doctor Consultation Panel - Modern UI
import React from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { FaUserMd, FaPlay, FaPause, FaVolumeUp, FaMapMarkerAlt, FaRedo } from 'react-icons/fa';
import { media } from '../../styles/breakpoints';
import { Card, CardHeader, CardContent, CardTitle, CardDescription, Button, Alert, AlertTitle, AlertDescription, Badge, Separator } from './modern-ui';

const DoctorPanel = styled(Card)`
  height: fit-content;
`;

const AnalysisContainer = styled(motion.div)`
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.5rem;
  margin-top: 1rem;
  
  ${media.md} {
    padding: 1.2rem;
  }
  
  ${media.sm} {
    padding: 1rem;
    border-radius: 10px;
  }
  
  ${media.xs} {
    padding: 0.8rem;
    border-radius: 8px;
  }
`;

const AnalysisHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  
  ${media.sm} {
    gap: 0.5rem;
    margin-bottom: 0.8rem;
  }
`;

const AnalysisIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2196F3, #1976D2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.1rem;
  box-shadow: 0 4px 15px rgba(33, 150, 243, 0.2);
  
  ${media.sm} {
    width: 36px;
    height: 36px;
    font-size: 1rem;
    border-radius: 8px;
  }
  
  ${media.xs} {
    width: 32px;
    height: 32px;
    font-size: 0.9rem;
  }
`;

const AnalysisTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  margin: 0;
  
  ${media.sm} {
    font-size: 1rem;
  }
  
  ${media.xs} {
    font-size: 0.95rem;
  }
`;

const AnalysisContent = styled.div`
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.7;
  font-size: 0.9rem;
  
  ${media.sm} {
    font-size: 0.85rem;
    line-height: 1.6;
  }
  
  ${media.xs} {
    font-size: 0.8rem;
    line-height: 1.5;
  }
  
  p {
    margin-bottom: 0.8rem;
  }
  
  strong {
    color: #4CAF50;
    font-weight: 600;
  }
  
  ul, ol {
    margin: 0.5rem 0;
    padding-left: 1.2rem;
  }
  
  li {
    margin-bottom: 0.3rem;
  }
`;

const AudioSection = styled.div`
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  
  ${media.sm} {
    margin-top: 1.2rem;
    padding-top: 1.2rem;
  }
  
  ${media.xs} {
    margin-top: 1rem;
    padding-top: 1rem;
  }
`;

const AudioControls = styled.div`
  margin-top: 1rem;
  
  ${media.xs} {
    margin-top: 0.8rem;
  }
`;

const AudioPlayer = styled.audio`
  width: 100%;
  height: 40px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  outline: none;
  
  /* Remove custom styling that might interfere */
  &::-webkit-media-controls-panel {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  &::-webkit-media-controls-play-button,
  &::-webkit-media-controls-pause-button {
    background-color: #4CAF50;
    border-radius: 50%;
  }
`;

const ActionSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  
  ${media.sm} {
    margin-top: 1.2rem;
    padding-top: 1.2rem;
    gap: 0.6rem;
  }
  
  ${media.xs} {
    margin-top: 1rem;
    padding-top: 1rem;
    gap: 0.5rem;
  }
`;

const ActionButton = styled(Button)`
  width: 100%;
  padding: 0.8rem 1rem;
  font-size: 0.9rem;
  
  ${media.sm} {
    padding: 0.7rem 0.9rem;
    font-size: 0.85rem;
  }
  
  ${media.xs} {
    padding: 0.8rem 0.8rem;
    font-size: 0.8rem;
    height: 44px; /* Minimum touch target size */
  }
`;

const PlaceholderContainer = styled.div`
  text-align: center;
  padding: 3rem 1rem;
  color: rgba(255, 255, 255, 0.5);
  
  ${media.md} {
    padding: 2.5rem 1rem;
  }
  
  ${media.sm} {
    padding: 2rem 0.8rem;
  }
  
  ${media.xs} {
    padding: 1.5rem 0.6rem;
  }
`;

const PlaceholderIcon = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 2rem;
  border: 2px dashed rgba(255, 255, 255, 0.1);
  
  ${media.md} {
    width: 70px;
    height: 70px;
    border-radius: 16px;
    font-size: 1.8rem;
  }
  
  ${media.sm} {
    width: 60px;
    height: 60px;
    border-radius: 14px;
    font-size: 1.6rem;
    margin-bottom: 0.8rem;
  }
  
  ${media.xs} {
    width: 50px;
    height: 50px;
    border-radius: 12px;
    font-size: 1.4rem;
    margin-bottom: 0.6rem;
  }
`;

const PlaceholderText = styled.p`
  font-size: 1rem;
  line-height: 1.5;
  
  ${media.sm} {
    font-size: 0.9rem;
    line-height: 1.4;
  }
  
  ${media.xs} {
    font-size: 0.85rem;
    line-height: 1.3;
  }
`;

export const ModernDoctorPanel = ({ 
  doctorResponse, 
  audioUrl, 
  resetConsultation, 
  setShowLocationPermission,
  recommendedSpecialty,
  translations: t 
}) => {
  // Debug logging
  console.log('ModernDoctorPanel received audioUrl:', audioUrl);
  console.log('ModernDoctorPanel received recommendedSpecialty:', recommendedSpecialty);
  
  return (
    <DoctorPanel
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.7, delay: 0.2 }}
    >
      <CardHeader>
        <CardTitle>
          <FaUserMd style={{ marginRight: '0.5rem' }} />
          {t.doctor_panel}
        </CardTitle>
        <CardDescription>{t.doctor_desc}</CardDescription>
      </CardHeader>

      <CardContent>
        <AnimatePresence mode="wait">
          {doctorResponse ? (
            <AnalysisContainer
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
            >
              <AnalysisHeader>
                <AnalysisIcon>
                  <FaUserMd />
                </AnalysisIcon>
                <div>
                  <AnalysisTitle>{t.analysis_title}</AnalysisTitle>
                  <Badge>AI Diagnosis Complete</Badge>
                </div>
              </AnalysisHeader>
              
              <AnalysisContent
                dangerouslySetInnerHTML={{ 
                  __html: doctorResponse.replace(/\n/g, '<br/>') 
                }}
              />
              
              {audioUrl && (
                <AudioSection>
                  <AnalysisHeader>
                    <AnalysisIcon style={{ background: 'linear-gradient(135deg, #FF9800, #F57C00)' }}>
                      <FaVolumeUp />
                    </AnalysisIcon>
                    <div>
                      <AnalysisTitle>{t.audio_title}</AnalysisTitle>
                      <Badge style={{ background: 'rgba(255, 152, 0, 0.1)', color: '#FFB74D' }}>
                        Audio Available
                      </Badge>
                    </div>
                  </AnalysisHeader>
                  
                  <AudioControls>
                    <audio 
                      controls 
                      autoPlay 
                      preload="auto"
                      style={{ 
                        width: '100%', 
                        height: '40px',
                        background: 'rgba(255, 255, 255, 0.05)',
                        borderRadius: '8px'
                      }}
                    >
                      <source src={audioUrl} type="audio/mpeg" />
                      <source src={audioUrl} type="audio/wav" />
                      Your browser does not support the audio element.
                    </audio>
                  </AudioControls>
                </AudioSection>
              )}

              <ActionSection>
                {recommendedSpecialty && (
                  <ActionButton
                    className="outline"
                    onClick={() => setShowLocationPermission(true)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <FaMapMarkerAlt />
                    {t.find_doctors_button}
                  </ActionButton>
                )}

                <ActionButton
                  className="secondary"
                  onClick={resetConsultation}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <FaRedo />
                  {t.reset_button}
                </ActionButton>
              </ActionSection>
            </AnalysisContainer>
          ) : (
            <PlaceholderContainer>
              <PlaceholderIcon>
                <FaUserMd />
              </PlaceholderIcon>
              <PlaceholderText>
                Complete the patient input to receive your AI medical consultation and analysis.
              </PlaceholderText>
            </PlaceholderContainer>
          )}
        </AnimatePresence>
      </CardContent>
    </DoctorPanel>
  );
};
