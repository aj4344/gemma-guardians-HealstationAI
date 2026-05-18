// 🎤 Enhanced Audio Recorder with Glass Morphism
import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { FaMicrophone, FaStop, FaTrash, FaDownload, FaPlay, FaPause } from 'react-icons/fa';

// Glass Morphism Styled Components
const RecorderContainer = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: ${props => props.$compact ? '12px' : '20px'};
  padding: ${props => props.$compact ? '1rem' : '2rem'};
  margin: 1rem 0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  }
`;

const RecordButton = styled(motion.button)`
  width: ${props => props.$compact ? '60px' : '80px'};
  height: ${props => props.$compact ? '60px' : '80px'};
  border-radius: 50%;
  border: none;
  background: ${props => props.$recording ? 
    'linear-gradient(135deg, #ff4757, #ff3838)' : 
    'linear-gradient(135deg, #4CAF50, #45a049)'
  };
  color: white;
  font-size: ${props => props.$compact ? '1.3rem' : '2rem'};
  cursor: pointer;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.3);
  }
  
  &:active {
    transform: scale(0.95);
  }
`;

const AudioControls = styled(motion.div)`
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
`;

const ControlButton = styled(motion.button)`
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }
`;

const WaveForm = styled(motion.div)`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2px;
  height: 40px;
  margin: 1rem 0;
`;

const WaveBar = styled(motion.div)`
  width: 3px;
  background: linear-gradient(to top, #4CAF50, #81C784);
  border-radius: 2px;
`;

const RecordingTimer = styled(motion.div)`
  text-align: center;
  font-size: 1.2rem;
  font-weight: 600;
  color: ${props => props.theme.text};
  margin: 1rem 0;
`;

const TranscriptionDisplay = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 1rem;
  margin-top: 1rem;
  min-height: 60px;
  color: ${props => props.theme.text};
  font-size: 0.9rem;
  line-height: 1.5;
`;

export const EnhancedAudioRecorder = ({ 
  onRecordingComplete, 
  transcription, 
  isTranscribing,
  translations,
  compact = false
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  
  const mediaRecorderRef = useRef(null);
  const audioRef = useRef(null);
  const timerRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const options = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? { mimeType: 'audio/webm;codecs=opus' }
        : {};
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      
      const chunks = [];
      mediaRecorder.ondataavailable = (event) => {
        chunks.push(event.data);
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'audio/webm' });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        onRecordingComplete(blob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  const clearRecording = () => {
    setAudioBlob(null);
    setAudioUrl(null);
    setIsPlaying(false);
    setRecordingTime(0);
  };

  const togglePlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const downloadAudio = () => {
    if (audioUrl) {
      const a = document.createElement('a');
      a.href = audioUrl;
      a.download = `medical-recording-${Date.now()}.wav`;
      a.click();
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <RecorderContainer
      $compact={compact}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div style={{ textAlign: 'center' }}>
        <RecordButton
          $recording={isRecording}
          $compact={compact}
          onClick={isRecording ? stopRecording : startRecording}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {isRecording ? <FaStop /> : <FaMicrophone />}
        </RecordButton>
        
        <AnimatePresence>
          {isRecording && (
            <RecordingTimer
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              🔴 {formatTime(recordingTime)}
            </RecordingTimer>
          )}
        </AnimatePresence>

        {isRecording && (
          <WaveForm>
            {[...Array(12)].map((_, i) => (
              <WaveBar
                key={i}
                animate={{
                  height: [10, Math.random() * 30 + 10, 10]
                }}
                transition={{
                  duration: 0.5,
                  repeat: Infinity,
                  delay: i * 0.1
                }}
              />
            ))}
          </WaveForm>
        )}

        <AnimatePresence>
          {audioBlob && (
            <AudioControls
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <ControlButton onClick={togglePlayback}>
                {isPlaying ? <FaPause /> : <FaPlay />}
                {isPlaying ? 'Pause' : 'Play'}
              </ControlButton>
              
              <ControlButton onClick={downloadAudio}>
                <FaDownload />
                Download
              </ControlButton>
              
              <ControlButton onClick={clearRecording}>
                <FaTrash />
                Clear
              </ControlButton>
            </AudioControls>
          )}
        </AnimatePresence>

        {audioUrl && (
          <audio
            ref={audioRef}
            src={audioUrl}
            onEnded={() => setIsPlaying(false)}
            style={{ display: 'none' }}
          />
        )}

        <AnimatePresence>
          {(transcription || isTranscribing) && (
            <TranscriptionDisplay
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <strong>{translations?.transcription_label || 'Transcription:'}</strong>
              <div style={{ marginTop: '0.5rem' }}>
                {isTranscribing ? (
                  <motion.span
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    {translations?.transcribing_audio || 'Transcribing...'}
                  </motion.span>
                ) : (
                  transcription
                )}
              </div>
            </TranscriptionDisplay>
          )}
        </AnimatePresence>
      </div>
    </RecorderContainer>
  );
};

export default EnhancedAudioRecorder;
