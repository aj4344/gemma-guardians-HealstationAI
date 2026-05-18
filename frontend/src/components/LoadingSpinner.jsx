import React from 'react';
import styled, { keyframes } from 'styled-components';

export const LoadingSpinner = () => {
  return (
    <SpinnerOverlay>
      <Spinner />
      <LoadingText>Processing your consultation...</LoadingText>
    </SpinnerOverlay>
  );
};

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const SpinnerOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const Spinner = styled.div`
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: ${spin} 1s ease-in-out infinite;
`;

const LoadingText = styled.p`
  color: white;
  margin-top: 1rem;
  font-size: 1.1rem;
`;


