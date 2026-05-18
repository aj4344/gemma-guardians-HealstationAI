// 🎨 MedMind AI Theme Configuration
// Professional medical themes with glass morphism support

export const lightTheme = {
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  cardBg: 'rgba(255, 255, 255, 0.95)',
  text: '#2d3748',
  textSecondary: '#718096',
  primary: '#4299e1',
  primaryHover: '#3182ce',
  success: '#48bb78',
  error: '#f56565',
  danger: '#e53e3e',
  border: 'rgba(255, 255, 255, 0.2)',
  shadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
};

export const darkTheme = {
  background: 'linear-gradient(135deg, #1a202c 0%, #2d3748 100%)',
  cardBg: 'rgba(45, 55, 72, 0.95)',
  text: '#f7fafc',
  textSecondary: '#a0aec0',
  primary: '#63b3ed',
  primaryHover: '#4299e1',
  success: '#68d391',
  error: '#fc8181',
  danger: '#fc8181',
  border: 'rgba(255, 255, 255, 0.1)',
  shadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
};

// 🌟 Enhanced Glass Morphism Theme
export const glassMorphismTheme = {
  light: {
    ...lightTheme,
    cardBg: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(20px)',
    glassBorder: '1px solid rgba(255, 255, 255, 0.2)',
    glassHover: 'rgba(255, 255, 255, 0.15)',
  },
  dark: {
    ...darkTheme,
    cardBg: 'rgba(45, 55, 72, 0.1)',
    backdropFilter: 'blur(20px)',
    glassBorder: '1px solid rgba(255, 255, 255, 0.1)',
    glassHover: 'rgba(45, 55, 72, 0.15)',
  }
};
