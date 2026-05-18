import React from 'react';
import styled from 'styled-components';
import { FaGlobe, FaInfoCircle, FaCog } from 'react-icons/fa';

export const Sidebar = ({ language, setLanguage, theme }) => {
  const languages = [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'Hindi' },
    { code: 'mr', name: 'Marathi' }
  ];
  
  return (
    <SidebarContainer theme={theme}>
      <SectionTitle theme={theme}>
        <FaGlobe /> Language
      </SectionTitle>
      
      <LanguageSelector>
        {languages.map(lang => (
          <LanguageOption
            key={lang.code}
            selected={language === lang.code}
            theme={theme}
            onClick={() => setLanguage(lang.code)}
          >
            {lang.name}
          </LanguageOption>
        ))}
      </LanguageSelector>
      
      <SectionTitle theme={theme}>
        <FaInfoCircle /> Information
      </SectionTitle>
      
      <InfoText theme={theme}>
        Speak naturally or type your symptoms, medical concerns, or questions.
        Upload images if you have visible symptoms (skin conditions, rashes, etc.)
      </InfoText>
      
      <SectionTitle theme={theme}>
        <FaCog /> Settings
      </SectionTitle>
      
      <SettingOption theme={theme}>
        <label>
          <input type="checkbox" defaultChecked={true} />
          Enable doctor's voice
        </label>
      </SettingOption>
      
      <SettingOption theme={theme}>
        <label>
          <input type="checkbox" defaultChecked={true} />
          Auto-transcribe audio
        </label>
      </SettingOption>
    </SidebarContainer>
  );
};

const SidebarContainer = styled.aside`
  width: 250px;
  padding: 1.5rem 1rem;
  background-color: ${props => props.theme === 'dark' ? '#252525' : 'var(--background-alt)'};
  border-radius: var(--border-radius);
  margin-right: 1.5rem;
  
  @media (max-width: 768px) {
    width: 100%;
    margin-right: 0;
    margin-bottom: 1.5rem;
  }
`;

const SectionTitle = styled.h3`
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 1.5rem 0 0.75rem;
  color: ${props => props.theme === 'dark' ? '#f0f0f0' : 'var(--secondary-color)'};
  
  &:first-child {
    margin-top: 0;
  }
`;

const LanguageSelector = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const LanguageOption = styled.button`
  background-color: ${props => props.selected 
    ? (props.theme === 'dark' ? 'var(--primary-color)' : 'var(--primary-color)')
    : (props.theme === 'dark' ? '#333' : 'var(--background-color)')
  };
  color: ${props => props.selected ? 'white' : (props.theme === 'dark' ? '#ddd' : 'var(--text-color)')};
  border: 1px solid ${props => props.theme === 'dark' ? '#555' : 'var(--border-color)'};
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-radius: var(--border-radius);
  transition: all var(--transition-speed);
  
  &:hover {
    background-color: ${props => props.selected 
      ? (props.theme === 'dark' ? '#0056b3' : '#0056b3')
      : (props.theme === 'dark' ? '#444' : '#f0f0f0')
    };
  }
`;

const InfoText = styled.p`
  font-size: 0.9rem;
  line-height: 1.5;
  color: ${props => props.theme === 'dark' ? '#bbb' : 'var(--text-color)'};
  margin-bottom: 1rem;
`;

const SettingOption = styled.div`
  padding: 0.5rem 0;
  color: ${props => props.theme === 'dark' ? '#ddd' : 'var(--text-color)'};
  
  label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
  }
  
  input[type="checkbox"] {
    accent-color: var(--primary-color);
  }
`;


