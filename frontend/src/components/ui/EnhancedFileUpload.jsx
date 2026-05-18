// 📁 Enhanced File Upload with Glass Morphism & Drag/Drop
import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { FaUpload, FaFilePdf, FaImage, FaTrash, FaEye } from 'react-icons/fa';
import { media } from '../../styles/breakpoints';

// Glass Morphism Styled Components
const UploadContainer = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 2px dashed ${props => props.$isDragOver ? '#4CAF50' : 'rgba(255, 255, 255, 0.3)'};
  border-radius: ${props => props.$compact ? '12px' : '20px'};
  padding: ${props => props.$compact ? '1.5rem' : '2rem'};
  margin: 1rem 0;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: #4CAF50;
    transform: translateY(-2px);
  }
  
  ${media.md} {
    padding: ${props => props.$compact ? '1.2rem' : '1.5rem'};
  }
  
  ${media.sm} {
    padding: ${props => props.$compact ? '1rem' : '1.2rem'};
    border-radius: ${props => props.$compact ? '10px' : '16px'};
  }
  
  ${media.xs} {
    padding: ${props => props.$compact ? '0.8rem' : '1rem'};
    border-radius: ${props => props.$compact ? '8px' : '12px'};
    margin: 0.8rem 0;
  }
`;

const UploadIcon = styled(motion.div)`
  font-size: ${props => props.$compact ? '2rem' : '3rem'};
  color: ${props => props.$isDragOver ? '#4CAF50' : 'rgba(255, 255, 255, 0.7)'};
  margin-bottom: ${props => props.$compact ? '0.5rem' : '1rem'};
  
  ${media.md} {
    font-size: ${props => props.$compact ? '1.8rem' : '2.5rem'};
  }
  
  ${media.sm} {
    font-size: ${props => props.$compact ? '1.6rem' : '2.2rem'};
    margin-bottom: ${props => props.$compact ? '0.4rem' : '0.8rem'};
  }
  
  ${media.xs} {
    font-size: ${props => props.$compact ? '1.4rem' : '2rem'};
    margin-bottom: ${props => props.$compact ? '0.3rem' : '0.6rem'};
  }
`;

const UploadText = styled.div`
  color: ${props => props.theme.text};
  font-size: ${props => props.$compact ? '0.9rem' : '1.1rem'};
  margin-bottom: 0.5rem;
  
  ${media.sm} {
    font-size: ${props => props.$compact ? '0.85rem' : '1rem'};
    margin-bottom: 0.4rem;
  }
  
  ${media.xs} {
    font-size: ${props => props.$compact ? '0.8rem' : '0.9rem'};
    margin-bottom: 0.3rem;
  }
`;

const UploadSubtext = styled.div`
  color: ${props => props.theme.textSecondary};
  font-size: ${props => props.$compact ? '0.8rem' : '0.9rem'};
  
  ${media.sm} {
    font-size: ${props => props.$compact ? '0.75rem' : '0.85rem'};
  }
  
  ${media.xs} {
    font-size: ${props => props.$compact ? '0.7rem' : '0.8rem'};
  }
`;

const FilesGrid = styled(motion.div)`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(${props => props.$compact ? '150px' : '200px'}, 1fr));
  gap: ${props => props.$compact ? '0.75rem' : '1rem'};
  margin-top: 1rem;
  
  ${media.md} {
    grid-template-columns: repeat(auto-fill, minmax(${props => props.$compact ? '140px' : '180px'}, 1fr));
    gap: ${props => props.$compact ? '0.7rem' : '0.9rem'};
  }
  
  ${media.sm} {
    grid-template-columns: repeat(auto-fill, minmax(${props => props.$compact ? '130px' : '160px'}, 1fr));
    gap: ${props => props.$compact ? '0.6rem' : '0.8rem'};
  }
  
  ${media.xs} {
    grid-template-columns: repeat(auto-fill, minmax(${props => props.$compact ? '120px' : '140px'}, 1fr));
    gap: ${props => props.$compact ? '0.5rem' : '0.7rem'};
  }
`;

const FileCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 15px;
  padding: 1rem;
  text-align: center;
  position: relative;
  overflow: hidden;
  
  &:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: translateY(-2px);
  }
  
  ${media.md} {
    padding: 0.9rem;
    border-radius: 12px;
  }
  
  ${media.sm} {
    padding: 0.8rem;
    border-radius: 10px;
  }
  
  ${media.xs} {
    padding: 0.7rem;
    border-radius: 8px;
  }
`;

const FileIcon = styled.div`
  font-size: 2rem;
  margin-bottom: 0.5rem;
  color: ${props => {
    if (props.$type?.includes('image')) return '#4CAF50';
    if (props.$type?.includes('pdf')) return '#f44336';
    return '#2196F3';
  }};
  
  ${media.sm} {
    font-size: 1.8rem;
    margin-bottom: 0.4rem;
  }
  
  ${media.xs} {
    font-size: 1.6rem;
    margin-bottom: 0.3rem;
  }
`;

const FileName = styled.div`
  font-size: 0.9rem;
  color: ${props => props.theme.text};
  margin-bottom: 0.5rem;
  word-break: break-word;
  
  ${media.sm} {
    font-size: 0.85rem;
    margin-bottom: 0.4rem;
  }
  
  ${media.xs} {
    font-size: 0.8rem;
    margin-bottom: 0.3rem;
  }
`;

const FileSize = styled.div`
  font-size: 0.8rem;
  color: ${props => props.theme.textSecondary};
  margin-bottom: 1rem;
  
  ${media.sm} {
    font-size: 0.75rem;
    margin-bottom: 0.8rem;
  }
  
  ${media.xs} {
    font-size: 0.7rem;
    margin-bottom: 0.7rem;
  }
`;

const FileActions = styled.div`
  display: flex;
  justify-content: center;
  gap: 0.5rem;
`;

const ActionButton = styled(motion.button)`
  padding: 0.3rem 0.6rem;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
`;

const PreviewModal = styled(motion.div)`
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
  z-index: 1000;
`;

const PreviewContent = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 2rem;
  max-width: 80%;
  max-height: 80%;
  overflow: auto;
`;

const PreviewImage = styled.img`
  max-width: 100%;
  max-height: 70vh;
  border-radius: 10px;
`;

const HiddenInput = styled.input`
  display: none;
`;

export const EnhancedFileUpload = ({ 
  files, 
  onFilesChange, 
  maxFiles = 8,
  translations,
  compact = false
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [previewFile, setPreviewFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    handleFiles(selectedFiles);
  };

  const handleFiles = (newFiles) => {
    const remainingSlots = maxFiles - files.length;
    const filesToAdd = newFiles.slice(0, remainingSlots);
    
    const processedFiles = filesToAdd.map(file => ({
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      id: Date.now() + Math.random(),
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    }));
    
    onFilesChange([...files, ...processedFiles]);
  };

  const removeFile = (fileId) => {
    const updatedFiles = files.filter(f => f.id !== fileId);
    onFilesChange(updatedFiles);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type) => {
    if (type.includes('image')) return <FaImage />;
    if (type.includes('pdf')) return <FaFilePdf />;
    return <FaUpload />;
  };

  return (
    <>
      <UploadContainer
        $isDragOver={isDragOver}
        $compact={compact}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        whileHover={{ scale: 1.02 }}
      >
        <UploadIcon $isDragOver={isDragOver} $compact={compact}>
          <motion.div
            animate={isDragOver ? { scale: [1, 1.1, 1] } : {}}
            transition={{ duration: 0.3 }}
          >
            <FaUpload />
          </motion.div>
        </UploadIcon>
        
        <UploadText $compact={compact}>
          {isDragOver 
            ? 'Drop files here...' 
            : translations?.upload_medical_files || 'Upload Medical Files'
          }
        </UploadText>
        
        <UploadSubtext $compact={compact}>
          {files.length >= maxFiles 
            ? translations?.max_files_reached || `Maximum ${maxFiles} files allowed`
            : 'Drag & drop or click to select medical images, PDFs, reports'
          }
        </UploadSubtext>
        
        <HiddenInput
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,.pdf,.doc,.docx"
          onChange={handleFileSelect}
          disabled={files.length >= maxFiles}
        />
      </UploadContainer>

      <AnimatePresence>
        {files.length > 0 && (
          <FilesGrid
            $compact={compact}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            {files.map((fileObj, index) => (
              <FileCard
                key={fileObj.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -5 }}
              >
                <FileIcon $type={fileObj.type}>
                  {getFileIcon(fileObj.type)}
                </FileIcon>
                
                <FileName>{fileObj.name}</FileName>
                <FileSize>{formatFileSize(fileObj.size)}</FileSize>
                
                <FileActions>
                  {fileObj.preview && (
                    <ActionButton
                      onClick={(e) => {
                        e.stopPropagation();
                        setPreviewFile(fileObj);
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <FaEye />
                      Preview
                    </ActionButton>
                  )}
                  
                  <ActionButton
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(fileObj.id);
                    }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <FaTrash />
                    Remove
                  </ActionButton>
                </FileActions>
              </FileCard>
            ))}
          </FilesGrid>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {previewFile && (
          <PreviewModal
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setPreviewFile(null)}
          >
            <PreviewContent
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.8 }}
              onClick={(e) => e.stopPropagation()}
            >
              <PreviewImage src={previewFile.preview} alt={previewFile.name} />
              <div style={{ textAlign: 'center', marginTop: '1rem', color: 'white' }}>
                {previewFile.name}
              </div>
            </PreviewContent>
          </PreviewModal>
        )}
      </AnimatePresence>
    </>
  );
};

export default EnhancedFileUpload;
