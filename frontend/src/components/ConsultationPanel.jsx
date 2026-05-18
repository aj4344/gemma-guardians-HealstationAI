import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { FaMicrophone, FaStop, FaImage, FaPaperPlane, FaVolumeUp, FaPause, FaPlay } from 'react-icons/fa';
import { AudioRecorder, useAudioRecorder } from 'react-audio-voice-recorder';
import axios from 'axios';

export const ConsultationPanel = ({ language, theme, setLoading }) => {
  const [patientInput, setPatientInput] = useState('');
  const [conversation, setConversation] = useState([]);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);
  const messageEndRef = useRef(null);
  
  const recorderControls = useAudioRecorder();
  
  // Handle audio recording completion
  const handleRecordingComplete = async (audioBlob) => {
    setIsRecording(false);
    setLoading(true);
    
    try {
      // Create form data to send
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('language', language);
      
      // Send to transcription API
      const response = await axios.post('/api/transcribe-audio', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      // Set the transcribed text as patient input
      setPatientInput(response.data.text);
    } catch (error) {
      console.error('Error transcribing audio:', error);
      alert('Failed to transcribe audio. Please try again or type your message.');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle image upload
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!patientInput.trim()) return;
    
    // Add patient message to conversation
    const newMessage = { 
      text: patientInput, 
      sender: 'patient',
      timestamp: new Date().toISOString()
    };
    
    setConversation(prev => [...prev, newMessage]);
    setLoading(true);
    
    try {
      let imageData = null;
      
      // Convert image to base64 if available
      if (imageFile) {
        const reader = new FileReader();
        const imageBase64 = await new Promise((resolve) => {
          reader.onload = (e) => resolve(e.target.result);
          reader.readAsDataURL(imageFile);
        });
        
        imageData = imageBase64.split(',')[1]; // Remove data URL prefix
      }
      
      // Send request to API
      const response = await axios.post('/api/get-doctor-response', {
        patient_text: patientInput,
        language,
        image_data: imageData
      });
      
      // Add doctor response to conversation
      setConversation(prev => [...prev, {
        text: response.data.doctor_response,
        sender: 'doctor',
        timestamp: new Date().toISOString(),
        audioUrl: response.data.audio_url
      }]);
      
      // Clear input and image
      setPatientInput('');
      setImageFile(null);
      setImagePreview('');
      
      // Play audio if available
      if (response.data.audio_url && audioRef.current) {
        audioRef.current.src = response.data.audio_url;
        audioRef.current.play();
        setIsPlaying(true);
      }
      
    } catch (error) {
      console.error('Error getting AI response:', error);
      alert('Failed to get doctor response. Please try again.');
      
    } finally {
      setLoading(false);
      
      // Scroll to bottom of conversation
      setTimeout(() => {
        messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  };
  
  // Handle audio playback controls
  const toggleAudio = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };
  
  // Handle audio events
  const handleAudioEnded = () => {
    setIsPlaying(false);
  };
  
  return (
    <PanelContainer theme={theme}>
      <ConversationContainer theme={theme}>
        {conversation.length === 0 ? (
          <WelcomeMessage theme={theme}>
            <h2>Welcome to HealStation AI: Doctor Assistant</h2>
            <p>How can I help you today? Please describe your symptoms or ask any health-related questions.</p>
          </WelcomeMessage>
        ) : (
          conversation.map((msg, index) => (
            <MessageBubble 
              key={index} 
              isPatient={msg.sender === 'patient'}
              theme={theme}
            >
              <MessageText>{msg.text}</MessageText>
              {msg.sender === 'doctor' && msg.audioUrl && (
                <AudioControls>
                  <AudioButton onClick={toggleAudio}>
                    {isPlaying ? <FaPause /> : <FaPlay />}
                  </AudioButton>
                  <audio 
                    ref={audioRef}
                    src={msg.audioUrl} 
                    onEnded={handleAudioEnded}
                  />
                </AudioControls>
              )}
            </MessageBubble>
          ))
        )}
        <div ref={messageEndRef} />
      </ConversationContainer>
      
      <InputContainer onSubmit={handleSubmit}>
        {imagePreview && (
          <ImagePreviewContainer>
            <ImagePreview src={imagePreview} alt="Upload preview" />
            <RemoveImageButton 
              onClick={() => {
                setImageFile(null);
                setImagePreview('');
              }}
            >
              ✕
            </RemoveImageButton>
          </ImagePreviewContainer>
        )}
        
        <InputRow>
          <InputField
            value={patientInput}
            onChange={(e) => setPatientInput(e.target.value)}
            placeholder="Describe your symptoms or ask a question..."
            theme={theme}
          />
          
          <InputActions>
            <RecordingButton 
              type="button" 
              isRecording={isRecording}
              onClick={() => {
                if (isRecording) {
                  recorderControls.stopRecording();
                  setIsRecording(false);
                } else {
                  recorderControls.startRecording();
                  setIsRecording(true);
                }
              }}
              title={isRecording ? "Stop recording" : "Start recording"}
            >
              {isRecording ? <FaStop /> : <FaMicrophone />}
            </RecordingButton>
            
            <ImageLabel htmlFor="image-upload" title="Upload image">
              <FaImage />
              <input
                id="image-upload"
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                style={{ display: 'none' }}
              />
            </ImageLabel>
            
            <SubmitButton type="submit" title="Send message">
              <FaPaperPlane />
            </SubmitButton>
          </InputActions>
        </InputRow>
      </InputContainer>
      
      <HiddenRecorder>
        <AudioRecorder
          onRecordingComplete={handleRecordingComplete}
          recorderControls={recorderControls}
        />
      </HiddenRecorder>
    </PanelContainer>
  );
};

const PanelContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: ${props => props.theme === 'dark' ? '#2a2a2a' : 'white'};
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  overflow: hidden;
`;

const ConversationContainer = styled.div`
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background-color: ${props => props.theme === 'dark' ? '#2a2a2a' : 'white'};
`;

const WelcomeMessage = styled.div`
  text-align: center;
  margin: auto;
  max-width: 500px;
  padding: 2rem;
  background-color: ${props => props.theme === 'dark' ? '#333' : 'var(--primary-light)'};
  border-radius: var(--border-radius);
  
  h2 {
    color: ${props => props.theme === 'dark' ? '#f0f0f0' : 'var(--primary-color)'};
    margin-bottom: 1rem;
  }
  
  p {
    color: ${props => props.theme === 'dark' ? '#ddd' : 'var(--text-color)'};
  }
`;

const MessageBubble = styled.div`
  max-width: 80%;
  padding: 1rem;
  border-radius: 1rem;
  align-self: ${props => props.isPatient ? 'flex-end' : 'flex-start'};
  background-color: ${props => {
    if (props.isPatient) {
      return props.theme === 'dark' ? 'var(--primary-color)' : 'var(--primary-color)';
    } else {
      return props.theme === 'dark' ? '#333' : 'var(--background-alt)';
    }
  }};
  color: ${props => props.isPatient ? 'white' : (props.theme === 'dark' ? '#f0f0f0' : 'var(--text-color)')};
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
`;

const MessageText = styled.p`
  margin: 0;
  white-space: pre-wrap;
`;

const AudioControls = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
`;

const AudioButton = styled.button`
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    opacity: 0.8;
    background: none;
    transform: none;
  }
`;

const InputContainer = styled.form`
  padding: 1rem;
  border-top: 1px solid var(--border-color);
`;

const InputRow = styled.div`
  display: flex;
  gap: 0.75rem;
`;

const InputField = styled.textarea`
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-family: inherit;
  font-size: 1rem;
  resize: none;
  min-height: 50px;
  max-height: 120px;
  background-color: ${props => props.theme === 'dark' ? '#333' : 'white'};
  color: ${props => props.theme === 'dark' ? '#f0f0f0' : 'var(--text-color)'};
  
  &::placeholder {
    color: ${props => props.theme === 'dark' ? '#999' : '#aaa'};
  }
  
  &:focus {
    outline: none;
    border-color: var(--primary-color);
  }
`;

const InputActions = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const RecordingButton = styled.button`
  background-color: ${props => props.isRecording ? 'var(--danger-color)' : 'var(--primary-color)'};
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-speed);
  
  &:hover {
    transform: scale(1.05);
  }
`;

const ImageLabel = styled.label`
  background-color: var(--secondary-color);
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-speed);
  
  &:hover {
    transform: scale(1.05);
  }
`;

const SubmitButton = styled.button`
  background-color: var(--success-color);
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-speed);
  
  &:hover {
    transform: scale(1.05);
  }
`;

const ImagePreviewContainer = styled.div`
  position: relative;
  margin-bottom: 1rem;
  max-width: 200px;
  border-radius: var(--border-radius);
  overflow: hidden;
`;

const ImagePreview = styled.img`
  width: 100%;
  height: auto;
  display: block;
`;

const RemoveImageButton = styled.button`
  position: absolute;
  top: 5px;
  right: 5px;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0;
  
  &:hover {
    background-color: rgba(220, 53, 69, 0.8);
    transform: none;
  }
`;

const HiddenRecorder = styled.div`
  position: absolute;
  left: -9999px;
  top: -9999px;
`;


