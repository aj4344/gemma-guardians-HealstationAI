import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import FileUpload3DCanvas from './FileUpload3D';

const DragDropContainer = styled.div`
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 200px;
  transition: all 0.3s ease;
  
  &.drag-over {
    transform: scale(1.02);
    filter: brightness(1.1);
  }
`;

const DragOverlay = styled(motion.div)`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(66, 153, 225, 0.1);
  border: 2px dashed #4299e1;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 600;
  color: #4299e1;
  backdrop-filter: blur(5px);
  z-index: 100;
`;

const Enhanced3DFileUpload = ({ onFilesAdded, medicalFiles, children }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [dragCounter, setDragCounter] = useState(0);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter(prev => prev + 1);
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragOver(true);
    }
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter(prev => prev - 1);
    if (dragCounter <= 1) {
      setIsDragOver(false);
    }
  }, [dragCounter]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    setDragCounter(0);
    
    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(file => 
      file.type.startsWith('image/') || file.type === 'application/pdf'
    );
    
    if (validFiles.length > 0) {
      onFilesAdded(validFiles);
    }
  }, [onFilesAdded]);

  return (
    <DragDropContainer
      className={isDragOver ? 'drag-over' : ''}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {/* 3D File Upload Animation */}
      <FileUpload3DCanvas
        isDragOver={isDragOver}
        hasFiles={medicalFiles.length > 0}
        fileCount={medicalFiles.length}
        files={medicalFiles}
        isVisible={isDragOver || medicalFiles.length > 0}
      />
      
      {/* Original Content */}
      {children}
      
      {/* Drag Over Overlay */}
      <AnimatePresence>
        {isDragOver && (
          <DragOverlay
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2 }}
          >
            📁 Drop medical files here
          </DragOverlay>
        )}
      </AnimatePresence>
    </DragDropContainer>
  );
};

export default Enhanced3DFileUpload;
