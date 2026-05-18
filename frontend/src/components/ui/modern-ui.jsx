// Modern UI Components - shadcn/ui inspired
import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';

// Utility function for merging class names
export const cn = (...inputs) => {
  return clsx(inputs);
};

// Card Component
export const Card = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.15);
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  }
`;

export const CardHeader = styled.div`
  padding: 1.5rem 1.5rem 0 1.5rem;
`;

export const CardContent = styled.div`
  padding: 1.5rem;
`;

export const CardTitle = styled.h3`
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #4CAF50, #2196F3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

export const CardDescription = styled.p`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.875rem;
  line-height: 1.5;
`;

// Input Components
export const Input = styled.input`
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  font-size: 0.875rem;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: #4CAF50;
    background: rgba(255, 255, 255, 0.08);
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

export const Textarea = styled.textarea`
  width: 100%;
  min-height: 100px;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  font-size: 0.875rem;
  resize: vertical;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: #4CAF50;
    background: rgba(255, 255, 255, 0.08);
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

// Button Components
export const Button = styled(motion.button)`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &.primary {
    background: linear-gradient(135deg, #4CAF50, #45a049);
    color: white;
    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
    
    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #45a049, #4CAF50);
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(76, 175, 80, 0.3);
    }
  }
  
  &.secondary {
    background: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    &:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);
    }
  }
  
  &.outline {
    background: transparent;
    color: #4CAF50;
    border: 1px solid #4CAF50;
    
    &:hover:not(:disabled) {
      background: rgba(76, 175, 80, 0.1);
    }
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// Badge Component
export const Badge = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 8px;
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
  border: 1px solid rgba(76, 175, 80, 0.2);
`;

// Separator Component
export const Separator = styled.div`
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  margin: 1rem 0;
`;

// Loading Skeleton
export const Skeleton = styled.div`
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.2) 50%, rgba(255, 255, 255, 0.1) 100%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 8px;
  height: ${props => props.height || '1rem'};
  width: ${props => props.width || '100%'};
  
  @keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
`;

// Alert Component
export const Alert = styled.div`
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  
  &.info {
    background: rgba(33, 150, 243, 0.1);
    border-color: rgba(33, 150, 243, 0.3);
    color: #64B5F6;
  }
  
  &.warning {
    background: rgba(255, 193, 7, 0.1);
    border-color: rgba(255, 193, 7, 0.3);
    color: #FFD54F;
  }
  
  &.success {
    background: rgba(76, 175, 80, 0.1);
    border-color: rgba(76, 175, 80, 0.3);
    color: #81C784;
  }
  
  &.error {
    background: rgba(244, 67, 54, 0.1);
    border-color: rgba(244, 67, 54, 0.3);
    color: #E57373;
  }
`;

export const AlertTitle = styled.h4`
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
`;

export const AlertDescription = styled.p`
  font-size: 0.8rem;
  line-height: 1.4;
  opacity: 0.9;
`;
