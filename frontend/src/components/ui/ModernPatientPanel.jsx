// Enhanced Patient Input Panel - Modern UI
import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { media } from '../../styles/breakpoints';
import { FaMicrophone, FaUpload, FaKeyboard, FaStethoscope } from 'react-icons/fa';
import { Card, CardHeader, CardContent, CardTitle, CardDescription, Button, Textarea, Badge, Separator } from './modern-ui';
import { EnhancedAudioRecorder } from './EnhancedAudioRecorder';
import { EnhancedFileUpload } from './EnhancedFileUpload';

const PatientPanel = styled(Card)`
  height: fit-content;
`;

const SectionContainer = styled.div`
  margin-bottom: 1.5rem;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  ${media.sm} {
    margin-bottom: 1.2rem;
  }
  
  ${media.xs} {
    margin-bottom: 1rem;
  }
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  
  ${media.sm} {
    gap: 0.6rem;
    margin-bottom: 0.8rem;
  }
  
  ${media.xs} {
    gap: 0.5rem;
    margin-bottom: 0.7rem;
  }
`;

const SectionIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4CAF50, #45a049);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.1rem;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
  
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
    border-radius: 8px;
  }
`;

const SectionTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: white;
  margin: 0;
  
  ${media.sm} {
    font-size: 0.95rem;
  }
  
  ${media.xs} {
    font-size: 0.9rem;
  }
`;

const SectionSubtitle = styled.p`
  font-size: 0.8rem;
  
  ${media.sm} {
    font-size: 0.75rem;
  }
  
  ${media.xs} {
    font-size: 0.7rem;
  }
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  line-height: 1.3;
`;

const InputContainer = styled.div`
  margin: 1rem 0;
  
  ${media.sm} {
    margin: 0.8rem 0;
  }
`;

const StatusBadge = styled(Badge)`
  margin-left: 0.5rem;
  font-size: 0.7rem;
`;

const CompactTextarea = styled(Textarea)`
  min-height: 80px;
  font-size: 0.85rem;
  
  ${media.sm} {
    min-height: 70px;
    font-size: 0.8rem;
  }
  
  ${media.xs} {
    min-height: 60px;
  }
`;

const ActionButton = styled(Button)`
  width: 100%;
  padding: 1rem;
  font-size: 1rem;
  font-weight: 600;
  margin-top: 1rem;
  
  ${media.sm} {
    padding: 0.8rem;
    font-size: 0.9rem;
    margin-top: 0.8rem;
  }
  
  ${media.xs} {
    padding: 0.7rem;
    height: 44px; /* Minimum touch target size */
  }
`;

export const ModernPatientPanel = ({ 
  textInput, 
  setTextInput, 
  transcription, 
  handleRecordingComplete, 
  isTranscribing, 
  medicalFiles, 
  handleFilesChange, 
  handleSubmit, 
  isGeneratingDiagnosis, 
  translations: t 
}) => {
  return (
    <PatientPanel
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.7 }}
    >
      <CardHeader>
        <CardTitle>
          <FaStethoscope style={{ marginRight: '0.5rem' }} />
          {t.patient_panel}
        </CardTitle>
        <CardDescription>{t.patient_desc}</CardDescription>
      </CardHeader>

      <CardContent>
        {/* Voice Input Section */}
        <SectionContainer>
          <SectionHeader>
            <SectionIcon>
              <FaMicrophone />
            </SectionIcon>
            <div>
              <SectionTitle>
                {t.step1_title}
                {isTranscribing && <StatusBadge>Recording...</StatusBadge>}
                {transcription && <StatusBadge>Transcribed ✓</StatusBadge>}
              </SectionTitle>
              <SectionSubtitle>{t.step1_desc}</SectionSubtitle>
            </div>
          </SectionHeader>
          
          <EnhancedAudioRecorder
            onRecordingComplete={handleRecordingComplete}
            transcription={transcription}
            isTranscribing={isTranscribing}
            translations={t}
            compact={true}
          />
        </SectionContainer>

        <Separator />

        {/* Text Input Section */}
        <SectionContainer>
          <SectionHeader>
            <SectionIcon>
              <FaKeyboard />
            </SectionIcon>
            <div>
              <SectionTitle>
                {t.step1_text_title}
                {textInput && <StatusBadge>Typed ✓</StatusBadge>}
              </SectionTitle>
              <SectionSubtitle>{t.step1_text_desc}</SectionSubtitle>
            </div>
          </SectionHeader>
          
          <InputContainer>
            <CompactTextarea
              placeholder={t.text_input_placeholder}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
            />
          </InputContainer>
        </SectionContainer>

        <Separator />

        {/* File Upload Section */}
        <SectionContainer>
          <SectionHeader>
            <SectionIcon>
              <FaUpload />
            </SectionIcon>
            <div>
              <SectionTitle>
                {t.step2_title}
                {medicalFiles.length > 0 && (
                  <StatusBadge>{medicalFiles.length} file{medicalFiles.length !== 1 ? 's' : ''} ✓</StatusBadge>
                )}
              </SectionTitle>
              <SectionSubtitle>{t.step2_desc}</SectionSubtitle>
            </div>
          </SectionHeader>
          
          <EnhancedFileUpload
            files={medicalFiles}
            onFilesChange={handleFilesChange}
            maxFiles={8}
            translations={t}
            compact={true}
          />
        </SectionContainer>

        {/* Submit Section */}
        <SectionContainer>
          <ActionButton
            className="primary"
            onClick={handleSubmit}
            disabled={isGeneratingDiagnosis || (!transcription && !textInput)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isGeneratingDiagnosis ? 'Analyzing...' : t.diagnosis_button}
          </ActionButton>
        </SectionContainer>
      </CardContent>
    </PatientPanel>
  );
};
