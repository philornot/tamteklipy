// Design Tokens - Centralne zarządzanie stylami aplikacji

// ============================================
// KOLORY
// ============================================
export const colors = {
  // Główne kolory marki
  brand: {
    primary: '#a855f7',      // purple-500
    primaryLight: '#c084fc', // purple-400
    primaryDark: '#7e22ce',  // purple-700
    accent: '#d946ef',       // fuchsia-500
    accentLight: '#e879f9',  // fuchsia-400
    accentDark: '#a21caf',   // fuchsia-700
  },

  // Tło i powierzchnie
  surface: {
    base: '#111827',        // bg-gray-900 (main background)
    elevated: '#1f2937',    // bg-gray-800 (cards)
    hover: '#374151',       // bg-gray-700 (hover states)
    overlay: 'rgba(0, 0, 0, 0.8)', // modals backdrop
  },

  // Granice i separatory
  border: {
    default: '#374151',     // border-gray-700
    hover: '#4b5563',       // border-gray-600
    focus: '#a855f7',       // border-primary
    accent: 'rgba(168, 85, 247, 0.3)', // border-primary/30
  },

  // Tekst
  text: {
    primary: '#f3f4f6',     // text-white/gray-100
    secondary: '#9ca3af',   // text-gray-400
    tertiary: '#6b7280',    // text-gray-500
    disabled: '#4b5563',    // text-gray-600
  },

  // Semantyczne kolory
  semantic: {
    success: '#10b981',     // green-500
    warning: '#f59e0b',     // yellow-500
    error: '#ef4444',       // red-500
    info: '#3b82f6',        // blue-500
  },

  // Status użytkowników
  status: {
    active: '#10b981',
    inactive: '#ef4444',
    pending: '#f59e0b',
  }
};

// ============================================
// GRADIENTY
// ============================================
export const gradients = {
  // Główny gradient marki
  primary: 'linear-gradient(135deg, #a855f7, #d946ef, #c084fc)',

  // Gradienty tła
  card: 'linear-gradient(to bottom right, #1f2937, rgba(30, 27, 75, 0.4))',
  cardHover: 'linear-gradient(to bottom right, transparent, transparent, rgba(168, 85, 247, 0.1))',

  // Efekty świetlne
  glow: 'linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(217, 70, 239, 0.1))',
  glowStrong: 'linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(217, 70, 239, 0.2))',

  // Gradient tekstu
  textPrimary: 'linear-gradient(to right, #c084fc, #e879f9, #c084fc)',
  textAccent: 'linear-gradient(to right, #a855f7, #d946ef)',

  // Gradienty przycisków
  buttonHover: 'linear-gradient(to right, rgba(255, 255, 255, 0.1), transparent)',
  shimmer: 'linear-gradient(to right, transparent, rgba(255, 255, 255, 0.1), transparent)',
};

// ============================================
// CIENIE
// ============================================
export const shadows = {
  // Karty
  card: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
  cardHover: '0 10px 15px -3px rgba(168, 85, 247, 0.2), 0 4px 6px -2px rgba(168, 85, 247, 0.1)',

  // Efekty świetlne
  glow: {
    sm: '0 0 20px rgba(168, 85, 247, 0.15)',
    md: '0 0 30px rgba(168, 85, 247, 0.25)',
    lg: '0 0 50px rgba(168, 85, 247, 0.35)',
    xl: '0 0 80px rgba(168, 85, 247, 0.45)',
  },

  // Akcenty kolorystyczne
  colored: {
    primary: '0 0 40px rgba(168, 85, 247, 0.3)',
    accent: '0 0 40px rgba(217, 70, 239, 0.3)',
    blue: '0 0 40px rgba(59, 130, 246, 0.3)',
    red: '0 0 40px rgba(239, 68, 68, 0.3)',
    green: '0 0 40px rgba(16, 185, 129, 0.3)',
  }
};

// ============================================
// ROZMIARY I SPACING
// ============================================
export const spacing = {
  // Padding dla różnych elementów
  card: '1.5rem',
  modal: '1.5rem',
  section: '2rem',
  button: {
    sm: '0.5rem 1rem',
    md: '0.75rem 1.5rem',
    lg: '1rem 2rem',
  },

  // Gaps
  gap: {
    xs: '0.5rem',
    sm: '0.75rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  }
};

// ============================================
// BORDER RADIUS
// ============================================
export const borderRadius = {
  card: '0.75rem',    // 12px
  button: '0.5rem',   // 8px
  modal: '1rem',      // 16px
  input: '0.5rem',    // 8px
  badge: '9999px',    // pill
};

// ============================================
// TRANSITIONS & TIMING
// ============================================
export const transitions = {
  duration: {
    fast: '150ms',
    normal: '300ms',
    slow: '500ms',
  },

  easing: {
    smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
  },

  // Gotowe deklaracje
  default: 'all 300ms cubic-bezier(0.4, 0, 0.2, 1)',
  fast: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: 'all 500ms cubic-bezier(0.4, 0, 0.2, 1)',
};

// ============================================
// Z-INDEX LAYERING
// ============================================
export const zIndex = {
  dropdown: 10,
  sticky: 20,
  fixed: 30,
  modalBackdrop: 40,
  modal: 50,
  popover: 60,
  tooltip: 70,
};

// ============================================
// TYPOGRAPHY (opcjonalnie, jeśli chcesz kontrolować fonty)
// ============================================
export const typography = {
  fontSize: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
  },

  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  }
};

// ============================================
// BREAKPOINTS (dla media queries)
// ============================================
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// Export domyślny z całym theme
const theme = {
  colors,
  gradients,
  shadows,
  spacing,
  borderRadius,
  transitions,
  zIndex,
  typography,
  breakpoints,
};

export default theme;
