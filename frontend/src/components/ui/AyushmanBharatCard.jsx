// AyushmanBharatCard.jsx - Ayushman Bharat (PM-JAY) Health Insurance Eligibility Checker
import React, { useState } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { FaTimes, FaHospital, FaCheckCircle, FaInfoCircle, FaQrcode, FaIdCard } from 'react-icons/fa';

// Glass Morphism Modal Backdrop
const Backdrop = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
`;

// Glass Morphism Modal Container
const ModalContainer = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 25px;
  padding: 2rem;
  max-width: 650px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  color: white;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  
  @media (max-width: 768px) {
    padding: 1.5rem;
    border-radius: 20px;
  }
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const TitleSection = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  .icon {
    font-size: 2rem;
    background: linear-gradient(135deg, #ff9933 0%, #138808 50%, #000080 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
`;

const TitleGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const Title = styled.h2`
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ff9933, #138808);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  
  @media (max-width: 640px) {
    font-size: 1.2rem;
  }
`;

const Subtitle = styled.p`
  margin: 0;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
`;

const CloseButton = styled.button`
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: rotate(90deg);
  }
`;

const Description = styled.p`
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 1.5rem;
  line-height: 1.6;
  text-align: center;
  padding: 0.75rem;
  background: rgba(255, 153, 51, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(255, 153, 51, 0.2);
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const Label = styled.label`
  font-size: 0.9rem;
  font-weight: 600;
  color: white;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  font-size: 0.95rem;
  font-family: inherit;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: #ff9933;
    background: rgba(255, 255, 255, 0.1);
    box-shadow: 0 0 0 3px rgba(255, 153, 51, 0.1);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  font-size: 0.95rem;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: #ff9933;
    background: rgba(255, 255, 255, 0.1);
    box-shadow: 0 0 0 3px rgba(255, 153, 51, 0.1);
  }
  
  option {
    background: #2d3748;
    color: white;
  }
`;

const RadioGroup = styled.div`
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
`;

const RadioLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid ${props => props.$checked ? '#ff9933' : 'rgba(255, 255, 255, 0.1)'};
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #ff9933;
  }
  
  input {
    cursor: pointer;
  }
`;

const SubmitButton = styled(motion.button)`
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #ff9933, #138808);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1.05rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(255, 153, 51, 0.3);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const ResultsContainer = styled(motion.div)`
  margin-top: 2rem;
  padding: 1.5rem;
  background: ${props => props.$eligible ? 
    'linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(76, 175, 80, 0.05))' : 
    'linear-gradient(135deg, rgba(33, 150, 243, 0.1), rgba(33, 150, 243, 0.05))'};
  border: 2px solid ${props => props.$eligible ? 
    'rgba(76, 175, 80, 0.3)' : 
    'rgba(33, 150, 243, 0.3)'};
  border-radius: 16px;
`;

const ResultTitle = styled.h3`
  margin: 0 0 1rem 0;
  font-size: 1.3rem;
  color: ${props => props.$eligible ? '#4CAF50' : '#2196F3'};
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ResultMessage = styled.p`
  margin: 0 0 1.5rem 0;
  font-size: 0.95rem;
  line-height: 1.6;
  color: white;
`;

const HealthCard = styled(motion.div)`
  background: linear-gradient(135deg, #ff9933 0%, #138808 50%, #000080 100%);
  border-radius: 16px;
  padding: 1.5rem;
  margin: 1.5rem 0;
  color: white;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  position: relative;
  z-index: 1;
`;

const CardTitle = styled.h4`
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
`;

const CardBody = styled.div`
  position: relative;
  z-index: 1;
`;

const CardRow = styled.div`
  margin: 0.75rem 0;
  font-size: 0.9rem;
  
  strong {
    display: block;
    font-size: 0.75rem;
    opacity: 0.9;
    margin-bottom: 0.25rem;
  }
`;

const BeneficiaryID = styled.div`
  background: rgba(255, 255, 255, 0.2);
  padding: 0.75rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-family: 'Courier New', monospace;
  font-size: 1rem;
  font-weight: 700;
  text-align: center;
  letter-spacing: 1px;
`;

const CoverageInfo = styled.div`
  background: rgba(255, 255, 255, 0.95);
  color: #138808;
  padding: 1rem;
  border-radius: 12px;
  margin: 1.5rem 0;
  text-align: center;
  font-weight: 700;
  font-size: 1.1rem;
`;

const BenefitsList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 1rem 0;
`;

const BenefitItem = styled.li`
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin: 0.75rem 0;
  font-size: 0.9rem;
  line-height: 1.5;
  color: white;
  
  svg {
    color: #4CAF50;
    margin-top: 0.2rem;
    flex-shrink: 0;
  }
`;

const FindHospitalsButton = styled(motion.button)`
  width: 100%;
  padding: 0.9rem;
  background: linear-gradient(135deg, #2196F3, #1976D2);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 1rem;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(33, 150, 243, 0.3);
  }
`;

const AyushmanBharatCard = ({ onClose, translations }) => {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    state: '',
    income: '',
    areaType: ''
  });
  
  const [showResults, setShowResults] = useState(false);
  const [isEligible, setIsEligible] = useState(false);

  const t = translations || {};

  const indianStates = [
    'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Gujarat', 'Rajasthan',
    'Uttar Pradesh', 'Madhya Pradesh', 'Bihar', 'West Bengal', 'Andhra Pradesh',
    'Telangana', 'Kerala', 'Odisha', 'Punjab', 'Haryana', 'Delhi'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const checkEligibility = (e) => {
    e.preventDefault();
    const eligible = formData.income === 'below_2l' || formData.income === '2_5l';
    setIsEligible(eligible);
    setShowResults(true);
  };

  const generateBeneficiaryID = () => {
    const state = formData.state.substring(0, 2).toUpperCase();
    const random = Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
    return `AB-${state}-2025-${random}`;
  };

  return (
    <AnimatePresence>
      <Backdrop
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <ModalContainer
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ duration: 0.3 }}
          onClick={(e) => e.stopPropagation()}
        >
          <ModalHeader>
            <TitleSection>
              <FaHospital className="icon" />
              <TitleGroup>
                <Title>{t.ayushman_title || 'Ayushman Bharat - PM-JAY'}</Title>
                <Subtitle>{t.ayushman_subtitle || 'Pradhan Mantri Jan Arogya Yojana'}</Subtitle>
              </TitleGroup>
            </TitleSection>
            <CloseButton onClick={onClose}>
              <FaTimes />
            </CloseButton>
          </ModalHeader>

          <Description>
            {t.ayushman_desc || 'Free health insurance for economically vulnerable families covering ₹5 lakh per family per year'}
          </Description>

          {!showResults ? (
            <Form onSubmit={checkEligibility}>
              <FormGroup>
                <Label>{t.name_label || 'Full Name:'}</Label>
                <Input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Enter your full name"
                  required
                />
              </FormGroup>

              <FormGroup>
                <Label>{t.age_label || 'Age:'}</Label>
                <Input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleInputChange}
                  placeholder="Enter your age"
                  min="1"
                  max="120"
                  required
                />
              </FormGroup>

              <FormGroup>
                <Label>{t.state_label || 'State:'}</Label>
                <Select
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">Select your state</option>
                  {indianStates.map(state => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </Select>
              </FormGroup>

              <FormGroup>
                <Label>{t.income_label || 'Annual Family Income:'}</Label>
                <RadioGroup>
                  <RadioLabel $checked={formData.income === 'below_2l'}>
                    <input
                      type="radio"
                      name="income"
                      value="below_2l"
                      checked={formData.income === 'below_2l'}
                      onChange={handleInputChange}
                      required
                    />
                    {t.income_below_2l || 'Below ₹2 Lakh'}
                  </RadioLabel>
                  <RadioLabel $checked={formData.income === '2_5l'}>
                    <input
                      type="radio"
                      name="income"
                      value="2_5l"
                      checked={formData.income === '2_5l'}
                      onChange={handleInputChange}
                    />
                    {t.income_2_5l || '₹2-5 Lakh'}
                  </RadioLabel>
                  <RadioLabel $checked={formData.income === 'above_5l'}>
                    <input
                      type="radio"
                      name="income"
                      value="above_5l"
                      checked={formData.income === 'above_5l'}
                      onChange={handleInputChange}
                    />
                    {t.income_above_5l || 'Above ₹5 Lakh'}
                  </RadioLabel>
                </RadioGroup>
              </FormGroup>

              <FormGroup>
                <Label>{t.area_label || 'Area Type:'}</Label>
                <RadioGroup>
                  <RadioLabel $checked={formData.areaType === 'rural'}>
                    <input
                      type="radio"
                      name="areaType"
                      value="rural"
                      checked={formData.areaType === 'rural'}
                      onChange={handleInputChange}
                      required
                    />
                    {t.rural || 'Rural'}
                  </RadioLabel>
                  <RadioLabel $checked={formData.areaType === 'urban'}>
                    <input
                      type="radio"
                      name="areaType"
                      value="urban"
                      checked={formData.areaType === 'urban'}
                      onChange={handleInputChange}
                    />
                    {t.urban || 'Urban'}
                  </RadioLabel>
                </RadioGroup>
              </FormGroup>

              <SubmitButton
                type="submit"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <FaCheckCircle /> {t.check_eligibility || 'Check Eligibility'}
              </SubmitButton>
            </Form>
          ) : (
            <ResultsContainer
              $eligible={isEligible}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <ResultTitle $eligible={isEligible}>
                {isEligible ? (
                  <>
                    <FaCheckCircle /> {t.eligible_title || '✅ Congratulations! You may be eligible'}
                  </>
                ) : (
                  <>
                    <FaInfoCircle /> {t.not_eligible_title || 'ℹ️ Not Eligible Currently'}
                  </>
                )}
              </ResultTitle>

              <ResultMessage>
                {isEligible ? 
                  (t.eligible_message || 'Based on the information provided, you appear to qualify for Ayushman Bharat scheme.') :
                  (t.not_eligible_message || 'Based on income criteria, you may not qualify. Consider state-specific health schemes.')
                }
              </ResultMessage>

              {isEligible && (
                <>
                  <HealthCard
                    initial={{ rotateY: 90 }}
                    animate={{ rotateY: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                  >
                    <CardHeader>
                      <div style={{fontSize: '2rem'}}><FaIdCard /></div>
                      <CardTitle>PMJAY Health Card</CardTitle>
                    </CardHeader>
                    <CardBody>
                      <CardRow>
                        <strong>NAME</strong>
                        {formData.name.toUpperCase()}
                      </CardRow>
                      <CardRow>
                        <strong>AGE</strong>
                        {formData.age} years
                      </CardRow>
                      <CardRow>
                        <strong>STATE</strong>
                        {formData.state}
                      </CardRow>
                      <BeneficiaryID>
                        <div style={{ fontSize: '0.7rem', opacity: 0.9, marginBottom: '0.25rem' }}>
                          {t.beneficiary_id || 'Sample Beneficiary ID:'}
                        </div>
                        {generateBeneficiaryID()}
                      </BeneficiaryID>
                    </CardBody>
                  </HealthCard>

                  <CoverageInfo>
                    {t.coverage_info || 'Coverage: ₹5,00,000 per family/year'}
                  </CoverageInfo>

                  <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem', fontSize: '1.1rem' }}>
                    {t.benefits_title || 'Key Benefits:'}
                  </h4>
                  <BenefitsList>
                    <BenefitItem>
                      <FaCheckCircle />
                      {t.benefit_1 || 'Cashless treatment at empaneled hospitals'}
                    </BenefitItem>
                    <BenefitItem>
                      <FaCheckCircle />
                      {t.benefit_2 || 'Coverage for hospitalization expenses'}
                    </BenefitItem>
                    <BenefitItem>
                      <FaCheckCircle />
                      {t.benefit_3 || 'Pre and post-hospitalization expenses'}
                    </BenefitItem>
                    <BenefitItem>
                      <FaCheckCircle />
                      {t.benefit_4 || 'No cap on family size'}
                    </BenefitItem>
                  </BenefitsList>

                  <FindHospitalsButton
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => alert('Hospital finder feature coming soon!')}
                  >
                    <FaHospital /> {t.find_hospitals || 'Find Empaneled Hospitals'}
                  </FindHospitalsButton>
                </>
              )}

              <SubmitButton
                style={{ marginTop: '1.5rem', background: 'rgba(255, 255, 255, 0.1)' }}
                onClick={() => {
                  setShowResults(false);
                  setFormData({
                    name: '',
                    age: '',
                    state: '',
                    income: '',
                    areaType: ''
                  });
                }}
              >
                Check Again
              </SubmitButton>
            </ResultsContainer>
          )}
        </ModalContainer>
      </Backdrop>
    </AnimatePresence>
  );
};

export default AyushmanBharatCard;
