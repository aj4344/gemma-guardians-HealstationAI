// Responsive breakpoints for consistent media queries
export const breakpoints = {
  xs: '480px',    // Extra small devices (phones)
  sm: '640px',    // Small devices (large phones, small tablets)
  md: '768px',    // Medium devices (tablets)
  lg: '1024px',   // Large devices (desktops)
  xl: '1280px',   // Extra large devices (large desktops)
  xxl: '1536px',  // Extra extra large devices
};

// Media query helper functions
export const media = {
  xs: `@media (max-width: ${breakpoints.xs})`,
  sm: `@media (max-width: ${breakpoints.sm})`,
  md: `@media (max-width: ${breakpoints.md})`,
  lg: `@media (max-width: ${breakpoints.lg})`,
  xl: `@media (max-width: ${breakpoints.xl})`,
  xxl: `@media (max-width: ${breakpoints.xxl})`,
  
  // Min-width queries (mobile-first approach)
  xsUp: `@media (min-width: ${breakpoints.xs})`,
  smUp: `@media (min-width: ${breakpoints.sm})`,
  mdUp: `@media (min-width: ${breakpoints.md})`,
  lgUp: `@media (min-width: ${breakpoints.lg})`,
  xlUp: `@media (min-width: ${breakpoints.xl})`,
  xxlUp: `@media (min-width: ${breakpoints.xxl})`,
  
  // Range queries
  xsToSm: `@media (min-width: ${breakpoints.xs}) and (max-width: ${breakpoints.sm})`,
  smToMd: `@media (min-width: ${breakpoints.sm}) and (max-width: ${breakpoints.md})`,
  mdToLg: `@media (min-width: ${breakpoints.md}) and (max-width: ${breakpoints.lg})`,
  lgToXl: `@media (min-width: ${breakpoints.lg}) and (max-width: ${breakpoints.xl})`,
};
