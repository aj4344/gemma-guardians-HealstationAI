import React from 'react';
import { FaFacebook, FaTwitter, FaLinkedinIn, FaInstagram } from 'react-icons/fa';

const GlowCard = ({ children, className = '', showSocial = false }) => {
  return (
    <div className={`glow-card ${className}`}>
      <b></b>
      <div className="content">
        {children}
        {showSocial && (
          <ul className="sci">
            <li>
              <a href="#" target="_blank" rel="noopener noreferrer">
                <FaFacebook />
              </a>
            </li>
            <li>
              <a href="#" target="_blank" rel="noopener noreferrer">
                <FaTwitter />
              </a>
            </li>
            <li>
              <a href="#" target="_blank" rel="noopener noreferrer">
                <FaLinkedinIn />
              </a>
            </li>
            <li>
              <a href="#" target="_blank" rel="noopener noreferrer">
                <FaInstagram />
              </a>
            </li>
          </ul>
        )}
      </div>
    </div>
  );
};

export default GlowCard;
