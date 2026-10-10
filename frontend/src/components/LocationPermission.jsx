import React, { useState } from 'react';
import styled from 'styled-components';
import { FaMapMarkerAlt, FaShieldAlt, FaTimes, FaCheck } from 'react-icons/fa';

const LocationModal = styled.div`
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
  z-index: 10000;
`;

const LocationCard = styled.div`
  background: ${props => props.theme.cardBg};
  border-radius: 20px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  box-shadow: ${props => props.theme.shadow};
  border: 1px solid ${props => props.theme.border};
  text-align: center;
`;

const LocationIcon = styled.div`
  font-size: 3rem;
  color: ${props => props.theme.primary};
  margin-bottom: 1rem;
`;

const LocationTitle = styled.h2`
  color: ${props => props.theme.text};
  margin-bottom: 1rem;
  font-size: 1.5rem;
`;

const LocationDescription = styled.p`
  color: ${props => props.theme.textSecondary};
  margin-bottom: 1.5rem;
  line-height: 1.6;
`;

const LocationBenefits = styled.ul`
  text-align: left;
  margin: 1.5rem 0;
  padding-left: 1rem;
  
  li {
    color: ${props => props.theme.textSecondary};
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    
    svg {
      color: ${props => props.theme.success};
      font-size: 0.9rem;
    }
  }
`;

const LocationButtons = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
`;

const LocationButton = styled.button`
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  border: none;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  
  &.primary {
    background: ${props => props.theme.primary};
    color: white;
    
    &:hover {
      background: ${props => props.theme.primaryHover};
      transform: translateY(-2px);
    }
  }
  
  &.secondary {
    background: transparent;
    color: ${props => props.theme.textSecondary};
    border: 2px solid ${props => props.theme.border};
    
    &:hover {
      background: ${props => props.theme.border};
    }
  }
`;

const LocationStatus = styled.div`
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 10px;
  background: ${props => props.$success ? 'rgba(72, 187, 120, 0.1)' : 'rgba(245, 101, 101, 0.1)'};
  color: ${props => props.$success ? props.theme.success : props.theme.error};
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
`;

const LocationPermission = ({ onLocationGranted, onLocationDenied, language = 'en' }) => {
  const [isRequesting, setIsRequesting] = useState(false);
  const [locationStatus, setLocationStatus] = useState(null);

  const translations = {
    en: {
      title: "📍 Enable Location for Better Care",
      description: "We need your location to find the best doctors near you based on your diagnosis.",
      benefits: [
        "Find top-rated specialists in your area",
        "Get accurate distance and directions",
        "Discover doctors with excellent reviews",
        "Save time with location-based recommendations"
      ],
      allow: "Allow Location",
      deny: "Skip for Now",
      requesting: "Getting Your Location...",
      success: "Location Detected Successfully!",
      error: "Location Permission Denied",
      searchByCity: "🏙️ Search by City Instead",
      privacy: "🔒 Your location is only used to find nearby doctors and is not stored."
    },
    hi: {
      title: "📍 बेहतर देखभाल के लिए स्थान सक्षम करें",
      description: "आपके निदान के आधार पर आपके पास सबसे अच्छे डॉक्टर खोजने के लिए हमें आपके स्थान की आवश्यकता है।",
      benefits: [
        "अपने क्षेत्र में शीर्ष-रेटेड विशेषज्ञ खोजें",
        "सटीक दूरी और दिशा प्राप्त करें",
        "उत्कृष्ट समीक्षाओं वाले डॉक्टर खोजें",
        "स्थान-आधारित सुझावों के साथ समय बचाएं"
      ],
      allow: "स्थान की अनुमति दें",
      deny: "अभी के लिए छोड़ें",
      requesting: "आपका स्थान प्राप्त कर रहे हैं...",
      success: "स्थान सफलतापूर्वक पहचान लिया गया!",
      error: "स्थान अनुमति अस्वीकार कर दी गई",
      searchByCity: "🏙️ शहर द्वारा खोजें",
      privacy: "🔒 आपका स्थान केवल आस-पास के डॉक्टरों को खोजने के लिए उपयोग किया जाता है और संग्रहीत नहीं किया जाता।"
    },
    mr: {
      title: "📍 चांगल्या काळजीसाठी स्थान सक्षम करा",
      description: "तुमच्या निदानाच्या आधारावर तुमच्या जवळचे सर्वोत्तम डॉक्टर शोधण्यासाठी आम्हाला तुमच्या स्थानाची गरज आहे.",
      benefits: [
        "तुमच्या क्षेत्रातील शीर्ष-रेटेड तज्ञ शोधा",
        "अचूक अंतर आणि दिशा मिळवा",
        "उत्कृष्ट पुनरावलोकनांसह डॉक्टर शोधा",
        "स्थान-आधारित शिफारशींसह वेळ वाचवा"
      ],
      allow: "स्थानाची परवानगी द्या",
      deny: "आत्तासाठी वगळा",
      requesting: "तुमचे स्थान मिळवत आहे...",
      success: "स्थान यशस्वीरित्या ओळखले गेले!",
      error: "स्थान परवानगी नाकारण्यात आली",
      searchByCity: "🏙️ शहरानुसार शोधा",
      privacy: "🔒 तुमचे स्थान फक्त जवळच्या डॉक्टरांना शोधण्यासाठी वापरले जाते आणि संग्रहीत केले जात नाही."
    }
  };

  const t = translations[language] || translations.en;

  const requestLocation = async () => {
    setIsRequesting(true);
    setLocationStatus(null);

    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          resolve,
          reject,
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000 // 5 minutes
          }
        );
      });

      const location = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        timestamp: Date.now()
      };

      setLocationStatus('success');
      
      // Call success callback after a brief delay to show success message
      setTimeout(() => {
        onLocationGranted(location);
      }, 1500);

    } catch (error) {
      console.error('Location request failed:', error);
      setLocationStatus('error');
      
      // Don't auto-close - let user click "Search by City" button
      // This gives user clear path forward instead of just showing error
    } finally {
      setIsRequesting(false);
    }
  };

  const handleDeny = () => {
    setLocationStatus('denied');
    // Proceed to city search instead of just closing
    onLocationDenied();
  };

  const handleSearchByCity = () => {
    // User chose to search by city after location denial/error
    onLocationDenied();
  };

  return (
    <LocationModal>
      <LocationCard>
        <LocationIcon>
          <FaMapMarkerAlt />
        </LocationIcon>
        
        <LocationTitle>{t.title}</LocationTitle>
        <LocationDescription>{t.description}</LocationDescription>
        
        <LocationBenefits>
          {t.benefits.map((benefit, index) => (
            <li key={index}>
              <FaCheck />
              {benefit}
            </li>
          ))}
        </LocationBenefits>
        
        {!locationStatus && (
          <LocationButtons>
            <LocationButton 
              className="primary" 
              onClick={requestLocation}
              disabled={isRequesting}
            >
              <FaMapMarkerAlt />
              {isRequesting ? t.requesting : t.allow}
            </LocationButton>
            
            <LocationButton 
              className="secondary" 
              onClick={handleDeny}
              disabled={isRequesting}
            >
              <FaTimes />
              {t.deny}
            </LocationButton>
          </LocationButtons>
        )}
        
        {locationStatus && (
          <>
            <LocationStatus $success={locationStatus === 'success'}>
              {locationStatus === 'success' ? <FaCheck /> : <FaTimes />}
              {locationStatus === 'success' ? t.success : t.error}
            </LocationStatus>
            
            {/* Show "Search by City" button when location is denied/error */}
            {locationStatus === 'error' && (
              <LocationButtons style={{ marginTop: '1rem' }}>
                <LocationButton 
                  className="primary" 
                  onClick={handleSearchByCity}
                >
                  {t.searchByCity}
                </LocationButton>
              </LocationButtons>
            )}
          </>
        )}
        
        <LocationDescription style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
          {t.privacy}
        </LocationDescription>
      </LocationCard>
    </LocationModal>
  );
};

export default LocationPermission;
