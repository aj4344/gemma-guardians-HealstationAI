import React from 'react';
import styled from 'styled-components';
import { FaGithub, FaLinkedin, FaTwitter } from 'react-icons/fa';

export const Footer = ({ theme }) => {
  const year = new Date().getFullYear();
  
  return (
    <FooterWrapper theme={theme}>
      <FooterContent>
        <FooterText>
          &copy; {year} HealStation AI: Doctor Assistant. All rights reserved.
        </FooterText>
        
        <SocialLinks>
          <SocialLink href="https://github.com" target="_blank" rel="noopener noreferrer">
            <FaGithub />
          </SocialLink>
          <SocialLink href="https://linkedin.com" target="_blank" rel="noopener noreferrer">
            <FaLinkedin />
          </SocialLink>
          <SocialLink href="https://twitter.com" target="_blank" rel="noopener noreferrer">
            <FaTwitter />
          </SocialLink>
        </SocialLinks>
      </FooterContent>
      
      <DisclaimerText theme={theme}>
        This application provides information for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment.
      </DisclaimerText>
    </FooterWrapper>
  );
};

const FooterWrapper = styled.footer`
  background-color: ${props => props.theme === 'dark' ? '#252525' : 'var(--background-alt)'};
  padding: 1rem 0;
  margin-top: auto;
`;

const FooterContent = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
  }
`;

const FooterText = styled.p`
  margin: 0;
  font-size: 0.9rem;
`;

const SocialLinks = styled.div`
  display: flex;
  gap: 1rem;
`;

const SocialLink = styled.a`
  color: inherit;
  font-size: 1.25rem;
  transition: color 0.2s;
  
  &:hover {
    color: var(--primary-color);
  }
`;

const DisclaimerText = styled.p`
  text-align: center;
  font-size: 0.8rem;
  margin: 1rem auto 0;
  max-width: 800px;
  padding: 0 1rem;
  color: ${props => props.theme === 'dark' ? '#aaa' : '#666'};
`;


