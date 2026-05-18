import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { 
  FaUserMd, FaStar, FaMapMarkerAlt, FaPhone, FaGlobe, 
  FaClock, FaDirections, FaHeart, FaFilter, FaSearch,
  FaStethoscope, FaEye, FaBone, FaBrain, FaHeartbeat,
  FaChild, FaVenus, FaLungs, FaUserCheck, FaTimes,
  FaHospital, FaFlask, FaHeadphones
} from 'react-icons/fa';
import axios from 'axios';
import { media } from '../styles/breakpoints';

// Use existing icons instead of importing new ones
const FaKidney = FaStethoscope;   // Using stethoscope icon for kidney
const FaEarListen = FaHeadphones; // Using headphones icon for ear

const RecommendationContainer = styled.div`
  background: ${props => props.theme.cardBg};
  border-radius: 20px;
  padding: 2rem;
  margin-top: 2rem;
  border: 1px solid ${props => props.theme.border};
  box-shadow: ${props => props.theme.shadow};
  
  ${media.md} {
    padding: 1.5rem;
    border-radius: 16px;
  }
  
  ${media.sm} {
    padding: 1.2rem;
    border-radius: 14px;
  }
  
  ${media.xs} {
    padding: 1rem;
    border-radius: 12px;
  }
`;

const RecommendationHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  position: relative;
  
  h3 {
    color: ${props => props.theme.text};
    margin: 0;
    font-size: 1.5rem;
    flex: 1;
    
    ${media.md} {
      font-size: 1.3rem;
    }
    
    ${media.sm} {
      font-size: 1.2rem;
    }
    
    ${media.xs} {
      font-size: 1.1rem;
    }
  }
  
  .icon {
    font-size: 2rem;
    color: ${props => props.theme.primary};
    
    ${media.sm} {
      font-size: 1.8rem;
    }
    
    ${media.xs} {
      font-size: 1.6rem;
    }
  }
  
  .close-button {
    position: absolute;
    top: -10px;
    right: -10px;
    background: ${props => props.theme.primary};
    color: white;
    border: none;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.3s ease;
    
    &:hover {
      background: ${props => props.theme.primaryHover || '#0056b3'};
      transform: scale(1.1);
    }
  }
`;

const SpecialtyBadge = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: ${props => props.theme.primary};
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 1rem;
`;

const LoadingSpinner = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: ${props => props.theme.textSecondary};
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid ${props => props.theme.border};
    border-top: 4px solid ${props => props.theme.primary};
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-right: 1rem;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const DoctorGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
  
  ${media.md} {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.2rem;
  }
  
  ${media.sm} {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
  }
  
  ${media.xs} {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
`;

const DoctorCard = styled.div`
  background: ${props => props.theme.cardBg};
  border: 1px solid ${props => props.theme.border};
  border-radius: 15px;
  padding: 1.5rem;
  transition: all 0.3s ease;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: ${props => props.theme.shadow};
    border-color: ${props => props.theme.primary};
  }
  
  ${media.md} {
    padding: 1.2rem;
    border-radius: 12px;
  }
  
  ${media.sm} {
    padding: 1rem;
    border-radius: 10px;
  }
`;

const DoctorHeader = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
`;

const DoctorAvatar = styled.div`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: ${props => props.theme.primary};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  flex-shrink: 0;
`;

const DoctorInfo = styled.div`
  flex: 1;
  
  h4 {
    margin: 0 0 0.5rem 0;
    color: ${props => props.theme.text};
    font-size: 1.2rem;
  }
  
  .specialty {
    color: ${props => props.theme.primary};
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }
  
  .clinic {
    color: ${props => props.theme.textSecondary};
    font-size: 0.9rem;
  }
`;

const DoctorRating = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  
  .stars {
    display: flex;
    gap: 0.2rem;
  }
  
  .rating-value {
    font-weight: 600;
    color: ${props => props.theme.text};
  }
  
  .review-count {
    color: ${props => props.theme.textSecondary};
    font-size: 0.9rem;
  }
`;

const DoctorDetails = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
  
  .detail-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: ${props => props.theme.textSecondary};
    font-size: 0.9rem;
    
    svg {
      color: ${props => props.theme.primary};
      width: 14px;
    }
  }
`;

const DoctorActions = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  
  ${media.sm} {
    flex-direction: column;
    gap: 0.7rem;
  }
`;

const ActionButton = styled.button`
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  
  &.primary {
    background: ${props => props.theme.primary};
    color: white;
    
    &:hover {
      background: ${props => props.theme.primaryHover};
    }
  }
  
  &.secondary {
    background: transparent;
    color: ${props => props.theme.primary};
    border: 1px solid ${props => props.theme.primary};
    
    &:hover {
      background: ${props => props.theme.primary};
      color: white;
    }
  }
  
  ${media.sm} {
    padding: 0.8rem;
    font-size: 0.85rem;
  }
  
  ${media.xs} {
    height: 44px; /* Minimum touch target size */
  }
`;

const FilterSection = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  
  ${media.sm} {
    gap: 0.8rem;
    justify-content: center;
  }
  
  ${media.xs} {
    gap: 0.6rem;
    flex-direction: row;
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 0.5rem;
    
    &::-webkit-scrollbar {
      height: 4px;
    }
    
    &::-webkit-scrollbar-track {
      background: ${props => props.theme.border};
      border-radius: 10px;
    }
    
    &::-webkit-scrollbar-thumb {
      background: ${props => props.theme.primary};
      border-radius: 10px;
    }
  }
`;

const FilterButton = styled.button`
  padding: 0.5rem 1rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 20px;
  background: ${props => props.$active ? props.theme.primary : 'transparent'};
  color: ${props => props.$active ? 'white' : props.theme.textSecondary};
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: ${props => props.theme.primary};
    color: white;
  }
  
  ${media.sm} {
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
  }
  
  ${media.xs} {
    padding: 0.3rem 0.7rem;
    font-size: 0.8rem;
    flex-shrink: 0;
  }
`;

const CitySearchContainer = styled.div`
  background: ${props => props.theme.cardBg};
  border: 2px solid ${props => props.theme.primary}20;
  border-radius: 15px;
  padding: 1.5rem;
  margin: 1rem 0;
  
  h4 {
    color: ${props => props.theme.text};
    margin: 0 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  ${media.md} {
    padding: 1.2rem;
    border-radius: 12px;
  }
  
  ${media.sm} {
    padding: 1rem;
    border-radius: 10px;
  }
  
  ${media.xs} {
    padding: 0.8rem;
    border-radius: 8px;
    
    h4 {
      font-size: 0.95rem;
      margin-bottom: 0.8rem;
    }
  }
`;

const CitySearchForm = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  
  ${media.md} {
    flex-direction: row;
  }
  
  ${media.xs} {
    gap: 0.8rem;
  }
`;

const CitySearchInput = styled.input`
  flex: 1;
  padding: 0.75rem;
  border: 1px solid ${props => props.theme.border};
  border-radius: 8px;
  background: ${props => props.theme.inputBg || props.theme.cardBg};
  color: ${props => props.theme.text};
  font-size: 0.9rem;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.primary}20;
  }
  
  &::placeholder {
    color: ${props => props.theme.textSecondary};
  }
`;

const CitySearchButton = styled.button`
  background: ${props => props.theme.primary};
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  
  &:hover {
    background: ${props => props.theme.primaryDark || props.theme.primary};
    transform: translateY(-1px);
  }
  
  &:disabled {
    background: ${props => props.theme.textSecondary};
    cursor: not-allowed;
    transform: none;
  }
  
  ${media.sm} {
    padding: 0.7rem 1.2rem;
    font-size: 0.85rem;
  }
  
  ${media.xs} {
    width: 100%;
    padding: 0.8rem 1rem;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem;
  color: ${props => props.theme.textSecondary};
  
  .icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: ${props => props.theme.primary};
  }
`;

const DoctorRecommendations = ({ 
  onClose,
  userLocation, 
  recommendedSpecialty, 
  diagnosis, 
  language = 'en' 
}) => {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState('distance');
  const [showCitySearch, setShowCitySearch] = useState(false);
  const [searchCity, setSearchCity] = useState('');
  const [searchSpecialty, setSearchSpecialty] = useState('');

  const translations = {
    en: {
      title: "🏥 Medical Facilities Near You",
      specialty: "Recommended for",
      loading: "Finding medical facilities in your area...",
      error: "Unable to find medical facilities. Please try again.",
      no_results: "No medical facilities found in your area.",
      try_expanding: "Try expanding your search radius.",
      filters: {
        distance: "Nearest",
        rating: "Top Rated",
        reviews: "Most Reviews",
        city_search: "Search by City"
      },
      rating: "Rating",
      reviews: "reviews",
      verified_hospital: "Verified Hospital",
      no_reviews: "No reviews available",
      distance: "away",
      call: "Call Hospital",
      directions: "Directions",
      website: "Website",
      hours: "Hours",
      specialties: {
        dermatologist: "Dermatologist",
        cardiologist: "Cardiologist",
        orthopedic: "Orthopedic Surgeon",
        ophthalmologist: "Ophthalmologist",
        neurologist: "Neurologist",
        psychiatrist: "Psychiatrist",
        pediatrician: "Pediatrician",
        gynecologist: "Gynecologist",
        pulmonologist: "Pulmonologist",
        urologist: "Urologist",
        nephrologist: "Nephrologist",
        vascular: "Vascular Surgeon",
        ent: "ENT Specialist",
        endocrinologist: "Endocrinologist",
        general: "General Practitioner"
      }
    },
    hi: {
      title: "🩺 आपके पास अनुशंसित डॉक्टर",
      specialty: "अनुशंसित विशेषता",
      loading: "आपके क्षेत्र में सर्वश्रेष्ठ डॉक्टर खोज रहे हैं...",
      error: "डॉक्टर नहीं मिले। कृपया पुनः प्रयास करें।",
      no_results: "आपके क्षेत्र में कोई डॉक्टर नहीं मिले।",
      try_expanding: "अपने खोज क्षेत्र का विस्तार करने का प्रयास करें।",
      filters: {
        distance: "निकटतम",
        rating: "शीर्ष रेटेड",
        reviews: "अधिकांश समीक्षाएं",
        city_search: "शहर द्वारा खोजें"
      },
      rating: "रेटिंग",
      reviews: "समीक्षाएं",
      distance: "दूर",
      call: "कॉल करें",
      directions: "दिशा",
      website: "वेबसाइट",
      hours: "समय",
      specialties: {
        dermatologist: "त्वचा विशेषज्ञ",
        cardiologist: "हृदय विशेषज्ञ",
        orthopedic: "आर्थोपेडिक सर्जन",
        ophthalmologist: "नेत्र विशेषज्ञ",
        neurologist: "न्यूरोलॉजिस्ट",
        psychiatrist: "मनोचिकित्सक",
        pediatrician: "बाल चिकित्सक",
        gynecologist: "स्त्री रोग विशेषज्ञ",
        pulmonologist: "फेफड़ों के विशेषज्ञ",
        urologist: "मूत्र रोग विशेषज्ञ",
        nephrologist: "गुर्दा रोग विशेषज्ञ",
        vascular: "वैस्कुलर सर्जन",
        ent: "ईएनटी विशेषज्ञ",
        endocrinologist: "अंतःस्रावी विशेषज्ञ",
        general: "सामान्य चिकित्सक"
      }
    },
    mr: {
      title: "🩺 तुमच्या जवळचे शिफारस केलेले डॉक्टर",
      specialty: "शिफारस केलेली विशेषता",
      loading: "तुमच्या क्षेत्रातील सर्वोत्तम डॉक्टर शोधत आहे...",
      error: "डॉक्टर सापडले नाहीत. कृपया पुन्हा प्रयत्न करा.",
      no_results: "तुमच्या क्षेत्रात कोणतेही डॉक्टर सापडले नाहीत.",
      try_expanding: "तुमच्या शोध क्षेत्राचा विस्तार करण्याचा प्रयत्न करा.",
      filters: {
        distance: "जवळचे",
        rating: "उच्च रेटेड",
        reviews: "अधिक पुनरावलोकन",
        city_search: "शहरानुसार शोध"
      },
      rating: "रेटिंग",
      reviews: "पुनरावलोकन",
      distance: "दूर",
      call: "कॉल करा",
      directions: "दिशा",
      website: "वेबसाइट",
      hours: "वेळ",
      specialties: {
        dermatologist: "त्वचा तज्ञ",
        cardiologist: "हृदय तज्ञ",
        orthopedic: "हाडांचे सर्जन",
        ophthalmologist: "नेत्र तज्ञ",
        neurologist: "न्यूरोलॉजिस्ट",
        psychiatrist: "मानसिक आरोग्य तज्ञ",
        pediatrician: "बाल तज्ञ",
        gynecologist: "स्त्री रोग तज्ञ",
        pulmonologist: "फुफ्फुसाचे तज्ञ",
        urologist: "मूत्रमार्ग तज्ञ",
        nephrologist: "मूत्रपिंड तज्ञ",
        vascular: "रक्तवाहिन्या सर्जन",
        ent: "कान, नाक, घसा तज्ञ",
        endocrinologist: "अंतःस्त्रावी तज्ञ",
        general: "सामान्य डॉक्टर"
      }
    }
  };

  const t = translations[language] || translations.en;

  const specialtyIcons = {
    dermatologist: <FaStethoscope />,
    cardiologist: <FaHeartbeat />,
    orthopedic: <FaBone />,
    ophthalmologist: <FaEye />,
    neurologist: <FaBrain />,
    psychiatrist: <FaBrain />,
    pediatrician: <FaChild />,
    gynecologist: <FaVenus />,
    pulmonologist: <FaLungs />,
    urologist: <FaUserMd />, 
    nephrologist: <FaKidney />,
    vascular: <FaHeart />, // Using heart icon for vascular surgeons who deal with blood vessels
    ent: <FaEarListen />,
    endocrinologist: <FaFlask />,
    general: <FaUserCheck />
  };

  useEffect(() => {
    console.log('🔄 Filter changed to:', selectedFilter);
    console.log('📍 Current userLocation:', userLocation);
    console.log('🩺 Current recommendedSpecialty:', recommendedSpecialty);
    
    // Clear previous results when switching filters
    setDoctors([]);
    setError(null);
    
    if (selectedFilter === 'city_search') {
      setShowCitySearch(true);
      console.log('🏙️ Switching to city search mode');
    } else {
      setShowCitySearch(false);
      console.log('📍 Switching to location-based search mode');
      
      if (recommendedSpecialty) {
        if (userLocation) {
          console.log('✅ Prerequisites met, starting location-based search');
          console.log('📊 User coordinates:', userLocation.latitude, userLocation.longitude);
          searchDoctors();
        } else {
          console.log('⚠️ Location not available, suggesting city search');
          // Automatically switch to city search when location isn't available
          setSelectedFilter('city_search');
          setShowCitySearch(true);
          
          // Set a default city if we're confident about it (e.g., from IP)
          setSearchCity('Pune'); // Default city
          setSearchSpecialty(recommendedSpecialty);
        }
      } else {
        console.log('❌ Missing prerequisites:');
        console.log('   - userLocation:', !!userLocation);
        console.log('   - recommendedSpecialty:', !!recommendedSpecialty);
      }
    }
  }, [userLocation, recommendedSpecialty, selectedFilter]);

  const searchDoctors = async () => {
    setLoading(true);
    setError(null);
    
    // 🐛 Debug logging with coordinate validation
    console.log('🔍 Starting doctor search with params:');
    console.log('📍 User Location:', userLocation);
    console.log('🩺 Recommended Specialty:', recommendedSpecialty);
    console.log('🌍 Language:', language);
    console.log('📏 Selected Filter:', selectedFilter);
    
    // Default coordinates for Pune if location is not available
    let searchLatitude = 18.5204;
    let searchLongitude = 73.8567;
    let isDefaultLocation = false;
    
    // 🚨 CRITICAL: Validate coordinates to detect location issues
    if (userLocation) {
      const { latitude, longitude } = userLocation;
      console.log(`🌍 Coordinates: ${latitude}, ${longitude}`);
      searchLatitude = latitude;
      searchLongitude = longitude;
      
      // Pune coordinates: ~18.5204°N, 73.8567°E
      // Mumbai coordinates: ~19.0760°N, 72.8777°E
      if (latitude > 18.3 && latitude < 18.8 && longitude > 73.5 && longitude < 74.2) {
        console.log('✅ CORRECT: Coordinates appear to be in Pune area');
      } else if (latitude > 18.9 && latitude < 19.3 && longitude > 72.5 && longitude < 73.2) {
        console.log('❌ ERROR: Coordinates appear to be in Mumbai area - THIS IS WRONG!');
        console.log('🚨 User is in Pune but location shows Mumbai coordinates!');
      } else {
        console.log('⚠️ WARNING: Coordinates are in unknown area');
        console.log(`   Expected Pune: ~18.52, ~73.86`);
        console.log(`   Expected Mumbai: ~19.08, ~72.88`);
        console.log(`   Actual: ${latitude}, ${longitude}`);
      }
    } else {
      console.log('⚠️ No user location available, using default Pune coordinates');
      isDefaultLocation = true;
    }
    
    try {
      const requestData = {
        latitude: searchLatitude,
        longitude: searchLongitude,
        specialty: recommendedSpecialty,
        radius: 25000, // 25km radius
        language: language,
        sort_by: selectedFilter,
        ai_response: diagnosis,  // 🤖 Include AI diagnosis for semantic analysis
        is_default_location: isDefaultLocation  // Let the API know if we're using default coordinates
      };
      
      console.log('📤 API Request Data:', requestData);
      console.log('🎯 Expected: Hospitals near Pune coordinates');
      
      const response = await axios.post('http://127.0.0.1:8001/api/search-doctors', requestData);
      
      console.log('📥 API Response:', response.data);
      console.log('👨‍⚕️ Doctors found:', response.data.doctors?.length || 0);
      
      // 🚨 Validate response to check if we got Mumbai results for Pune user
      if (response.data.doctors && response.data.doctors.length > 0) {
        const firstDoctor = response.data.doctors[0];
        console.log('🏥 First hospital location:', firstDoctor.location);
        console.log('📍 First hospital coordinates:', firstDoctor.latitude, firstDoctor.longitude);
        
        if (firstDoctor.location && firstDoctor.location.toLowerCase().includes('mumbai')) {
          console.log('🚨 CRITICAL ERROR: Got Mumbai hospitals for location-based search!');
          console.log('🚨 This indicates a serious bug in location handling!');
        }
      }
      
      setDoctors(response.data.doctors || []);
    } catch (err) {
      console.error('❌ Doctor search failed:', err);
      console.error('🔍 Error details:', err.response?.data || err.message);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilter) => {
    console.log(`🔄 Filter change: ${selectedFilter} → ${newFilter}`);
    
    // Clear previous results immediately
    setDoctors([]);
    setError(null);
    setLoading(false);
    
    // Clear city search data when switching away from city search
    if (selectedFilter === 'city_search' && newFilter !== 'city_search') {
      console.log('🧹 Clearing city search state');
      setSearchCity('');
      setSearchSpecialty('');
    }
    
    setSelectedFilter(newFilter);
    console.log('✅ Filter changed, useEffect will trigger search');
  };

  const searchDoctorsByCity = async () => {
    if (!searchCity.trim() || !searchSpecialty.trim()) {
      setError('Please enter both city and specialty');
      return;
    }

    console.log(`🏙️ Searching doctors by city: ${searchCity}, specialty: ${searchSpecialty}`);
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('http://127.0.0.1:8001/api/search-doctors-by-city', {
        city: searchCity.trim(),
        specialty: searchSpecialty.trim(),
        language: language,
        sort_by: 'distance',
        user_latitude: userLocation?.latitude,
        user_longitude: userLocation?.longitude,
        limit: 20
      });
      
      setDoctors(response.data.doctors || []);
      if (response.data.doctors.length === 0) {
        setError(`No ${searchSpecialty} specialists found in ${searchCity}. Try a different city or specialty.`);
      }
    } catch (err) {
      console.error('City-based doctor search failed:', err);
      setError(`Failed to search for doctors in ${searchCity}. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const renderStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    
    for (let i = 0; i < fullStars; i++) {
      stars.push(<FaStar key={i} color="#FFD700" />);
    }
    
    if (hasHalfStar) {
      stars.push(<FaStar key="half" color="#FFD700" style={{ opacity: 0.5 }} />);
    }
    
    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<FaStar key={`empty-${i}`} color="#E2E8F0" />);
    }
    
    return stars;
  };

  const getDirections = (doctor) => {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${doctor.latitude},${doctor.longitude}`;
    window.open(url, '_blank');
  };

  const callDoctor = (phone) => {
    window.location.href = `tel:${phone}`;
  };

  const visitWebsite = (website) => {
    window.open(website, '_blank');
  };

  if (loading) {
    return (
      <RecommendationContainer>
        <RecommendationHeader>
          <div className="icon">
            <FaUserMd />
          </div>
          <h3>{t.title}</h3>
          {onClose && (
            <button className="close-button" onClick={onClose} title="Close">
              <FaTimes />
            </button>
          )}
        </RecommendationHeader>
        <LoadingSpinner>
          <div className="spinner"></div>
          {t.loading}
        </LoadingSpinner>
      </RecommendationContainer>
    );
  }

  if (error) {
    return (
      <RecommendationContainer>
        <RecommendationHeader>
          <div className="icon">
            <FaUserMd />
          </div>
          <h3>{t.title}</h3>
          {onClose && (
            <button className="close-button" onClick={onClose} title="Close">
              <FaTimes />
            </button>
          )}
        </RecommendationHeader>
        <EmptyState>
          <div className="icon">
            <FaUserMd />
          </div>
          <h3>{t.error}</h3>
          <p>{error}</p>
        </EmptyState>
      </RecommendationContainer>
    );
  }

  return (
    <RecommendationContainer>
      <RecommendationHeader>
        <div className="icon">
          <FaUserMd />
        </div>
        <h3>{t.title}</h3>
        {onClose && (
          <button className="close-button" onClick={onClose} title="Close">
            <FaTimes />
          </button>
        )}
      </RecommendationHeader>

      <SpecialtyBadge>
        {specialtyIcons[recommendedSpecialty]}
        {t.specialty}: {t.specialties[recommendedSpecialty]}
      </SpecialtyBadge>

      <FilterSection>
        {Object.entries(t.filters).map(([key, label]) => (
          <FilterButton
            key={key}
            $active={selectedFilter === key}
            onClick={() => handleFilterChange(key)}
          >
            <FaFilter />
            {label}
          </FilterButton>
        ))}
      </FilterSection>

      {showCitySearch && (
        <CitySearchContainer>
          <h4>
            <FaSearch />
            {language === 'hi' ? 'शहर द्वारा खोजें' : 
             language === 'mr' ? 'शहरानुसार शोध' : 
             'Search by City'}
          </h4>
          <CitySearchForm>
            <CitySearchInput
              type="text"
              placeholder={language === 'hi' ? 'शहर का नाम दर्ज करें (जैसे मुंबई, दिल्ली)' : 
                          language === 'mr' ? 'शहराचे नाव टाका (जसे मुंबई, दिल्ली)' :
                          'Enter city name (e.g., Mumbai, Delhi, Bangalore)'}
              value={searchCity}
              onChange={(e) => setSearchCity(e.target.value)}
            />
            <CitySearchInput
              type="text"
              placeholder={language === 'hi' ? 'विशेषता दर्ज करें (जैसे कार्डियोलॉजिस्ट, त्वचा विशेषज्ञ)' : 
                          language === 'mr' ? 'तज्ञता टाका (जसे कार्डियोलॉजिस्ट, त्वचा तज्ञ)' :
                          'Enter specialty (e.g., cardiologist, dermatologist)'}
              value={searchSpecialty}
              onChange={(e) => setSearchSpecialty(e.target.value)}
            />
            <CitySearchButton 
              onClick={searchDoctorsByCity}
              disabled={!searchCity.trim() || !searchSpecialty.trim() || loading}
            >
              <FaSearch />
              {language === 'hi' ? 'खोजें' : 
               language === 'mr' ? 'शोध' : 
               'Search'}
            </CitySearchButton>
          </CitySearchForm>
        </CitySearchContainer>
      )}

      {doctors.length === 0 ? (
        <EmptyState>
          <div className="icon">
            <FaSearch />
          </div>
          <h3>{t.no_results}</h3>
          <p>{t.try_expanding}</p>
        </EmptyState>
      ) : (
        <DoctorGrid>
          {doctors.map((doctor, index) => (
            <DoctorCard key={index}>
              <DoctorHeader>
                <DoctorAvatar>
                  {doctor.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </DoctorAvatar>
                <DoctorInfo>
                  <h4>{doctor.name}</h4>
                  <div className="specialty">{doctor.specialty}</div>
                  <div className="clinic">{doctor.clinic_name}</div>
                </DoctorInfo>
              </DoctorHeader>

              <DoctorRating>
                <div className="stars">
                  {doctor.rating ? renderStars(doctor.rating) : renderStars(0)}
                </div>
                {doctor.rating && doctor.rating > 0 ? (
                  <>
                    <span className="rating-value">{doctor.rating}</span>
                    <span className="review-count">
                      ({doctor.review_count || 0} real {doctor.review_count === 1 ? 'review' : 'reviews'})
                    </span>
                  </>
                ) : (
                  <>
                    <span className="rating-value">No rating</span>
                    <span className="review-count">
                      {doctor.hospital_verified ? 
                        '(Verified Hospital - No reviews needed)' : 
                        '(No user reviews available)'
                      }
                    </span>
                  </>
                )}
              </DoctorRating>

              <DoctorDetails>
                <div className="detail-item">
                  <FaMapMarkerAlt />
                  {doctor.distance}km {t.distance}
                </div>
                <div className="detail-item">
                  <FaClock />
                  {doctor.hours || 'Call for hours'}
                </div>
                <div className="detail-item">
                  <FaPhone />
                  {doctor.phone && doctor.phone !== 'N/A' ? doctor.phone : 'N/A'}
                </div>
                <div className="detail-item">
                  <FaUserCheck />
                  {doctor.source === 'VerifiedHospitalDatabase' ? 
                    'Verified Hospital' : 
                    'Real Location Data'
                  }
                </div>
              </DoctorDetails>

              <DoctorActions>
                {doctor.phone && doctor.phone !== 'N/A' && (
                  <ActionButton 
                    className="primary" 
                    onClick={() => callDoctor(doctor.phone)}
                  >
                    <FaPhone />
                    {t.call}
                  </ActionButton>
                )}
                <ActionButton 
                  className="secondary" 
                  onClick={() => getDirections(doctor)}
                >
                  <FaDirections />
                  {t.directions}
                </ActionButton>
                {doctor.website && (
                  <ActionButton 
                    className="secondary" 
                    onClick={() => visitWebsite(doctor.website)}
                  >
                    <FaGlobe />
                    {t.website}
                  </ActionButton>
                )}
              </DoctorActions>
            </DoctorCard>
          ))}
        </DoctorGrid>
      )}
    </RecommendationContainer>
  );
};

export default DoctorRecommendations;
