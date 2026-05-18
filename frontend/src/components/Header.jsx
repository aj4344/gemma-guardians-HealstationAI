import React from 'react';
import styled from 'styled-components';
import { FaMoon, FaSun, FaStethoscope } from 'react-icons/fa';

// Use named export
export const Header = ({ theme, toggleTheme }) => {
  return (
    <HeaderWrapper theme={theme}>
      <LogoContainer>
        <FaStethoscope size={24} />
        <Logo>HealStation AI: Doctor Assistant</Logo>
      </LogoContainer>
      
      <NavLinks>
        <NavLink href="#" theme={theme}>Home</NavLink>
        <NavLink href="#about" theme={theme}>About</NavLink>
        <NavLink href="#contact" theme={theme}>Contact</NavLink>
      </NavLinks>
      
      <ThemeToggle onClick={toggleTheme}>
        {theme === 'light' ? <FaMoon size={20} /> : <FaSun size={20} />}
      </ThemeToggle>
    </HeaderWrapper>
  );
};

const HeaderWrapper = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: ${props => props.theme === 'dark' ? '#252525' : 'var(--primary-color)'};
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const LogoContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
`;

const Logo = styled.h1`
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  
  @media (max-width: 768px) {
    font-size: 1.2rem;
  }
`;

const NavLinks = styled.div`
  display: flex;
  gap: 20px;
  
  @media (max-width: 768px) {
    display: none;
  }
`;

const NavLink = styled.a`
  color: white;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.2s;
  
  &:hover {
    opacity: 0.8;
  }
`;

const ThemeToggle = styled.button`
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.3s;
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
    transform: none;
  }
`;