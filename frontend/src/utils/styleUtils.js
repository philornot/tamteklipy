// Style utilities - pomocnicze funkcje do generowania klas

// ============================================
// CLASS NAMES HELPERS
// ============================================

/**
 * Łączy klasy CSS, pomijając falsy values
 */
export const cn = (...classes) => {
  return classes.filter(Boolean).join(' ');
};

/**
 * Warunkowe klasy
 */
export const conditional = (condition, trueClass, falseClass = '') => {
  return condition ? trueClass : falseClass;
};

// ============================================
// CARD STYLES
// ============================================

export const cardStyles = {
  base: 'bg-gray-800 rounded-card border border-gray-700 p-4 transition-all duration-300',

  hoverable: 'hover:border-purple-500/50 hover:shadow-card-hover cursor-pointer',

  selected: 'border-purple-500 shadow-glow bg-purple-500/10',

  elevated: 'shadow-card',

  gradient: 'bg-gradient-card',

  // Kombinacje
  default: 'bg-gray-800 rounded-card border border-gray-700 p-4 transition-all duration-300',

  interactive: 'bg-gray-800 rounded-card border border-gray-700 p-4 transition-all duration-300 hover:border-purple-500/50 hover:shadow-card-hover cursor-pointer',

  glowing: 'bg-gray-800 rounded-card border border-purple-500/30 p-4 shadow-glow transition-all duration-300',
};

/**
 * Generuje klasy dla karty
 */
export const getCardClasses = ({
  variant = 'default',
  hoverable = false,
  selected = false,
  className = ''
} = {}) => {
  return cn(
    cardStyles.base,
    variant === 'elevated' && cardStyles.elevated,
    variant === 'gradient' && cardStyles.gradient,
    variant === 'glow' && 'border-purple-500/30 shadow-glow',
    hoverable && cardStyles.hoverable,
    selected && cardStyles.selected,
    className
  );
};

// ============================================
// BUTTON STYLES
// ============================================

export const buttonStyles = {
  base: 'font-medium rounded-button transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed',

  variants: {
    primary: 'bg-purple-500 hover:bg-purple-600 text-white shadow-glow-sm hover:shadow-glow',
    secondary: 'bg-gray-700 hover:bg-gray-600 text-white border border-gray-600',
    accent: 'bg-fuchsia-500 hover:bg-fuchsia-600 text-white shadow-glow-sm hover:shadow-glow',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
    success: 'bg-green-500 hover:bg-green-600 text-white',
    ghost: 'bg-transparent hover:bg-gray-700 text-gray-300',
    outline: 'bg-transparent hover:bg-purple-500/10 text-purple-400 border border-purple-500',
  },

  sizes: {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  },
};

/**
 * Generuje klasy dla przycisku
 */
export const getButtonClasses = ({
  variant = 'primary',
  size = 'md',
  className = ''
} = {}) => {
  return cn(
    buttonStyles.base,
    buttonStyles.variants[variant],
    buttonStyles.sizes[size],
    className
  );
};

// ============================================
// INPUT STYLES
// ============================================

export const inputStyles = {
  base: 'w-full bg-gray-700 border text-white px-4 py-2 rounded-input transition focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent',

  default: 'border-gray-600',
  error: 'border-red-500',
  success: 'border-green-500',

  disabled: 'opacity-50 cursor-not-allowed',
};

/**
 * Generuje klasy dla inputa
 */
export const getInputClasses = ({
  error = false,
  success = false,
  disabled = false,
  className = ''
} = {}) => {
  return cn(
    inputStyles.base,
    error && inputStyles.error,
    success && inputStyles.success,
    !error && !success && inputStyles.default,
    disabled && inputStyles.disabled,
    className
  );
};

// ============================================
// BADGE STYLES
// ============================================

export const badgeStyles = {
  base: 'inline-flex items-center gap-1 px-2 py-1 rounded-badge text-xs font-medium',

  variants: {
    default: 'bg-gray-700 text-gray-300',
    primary: 'bg-purple-500 text-white',
    accent: 'bg-fuchsia-500 text-white',
    success: 'bg-green-500 text-white',
    warning: 'bg-yellow-500 text-white',
    danger: 'bg-red-500 text-white',
    info: 'bg-blue-500 text-white',
    outline: 'bg-transparent border border-purple-500 text-purple-400',
  },
};

/**
 * Generuje klasy dla badge
 */
export const getBadgeClasses = ({
  variant = 'default',
  className = ''
} = {}) => {
  return cn(
    badgeStyles.base,
    badgeStyles.variants[variant],
    className
  );
};

// ============================================
// ANIMATION UTILITIES
// ============================================

export const animations = {
  fadeIn: 'animate-fade-in',
  slideUp: 'animate-slide-up',
  scaleIn: 'animate-scale-in',
  spin: 'animate-spin',
  pulse: 'animate-pulse',
  glowPulse: 'animate-glow-pulse',
  shimmer: 'animate-shimmer',
};

// ============================================
// GLOW EFFECTS
// ============================================

/**
 * Generuje klasy dla efektu świecenia
 */
export const getGlowClasses = (color = 'primary', intensity = 'md') => {
  const colors = {
    primary: 'shadow-colored-primary',
    accent: 'shadow-colored-accent',
    blue: 'shadow-colored-blue',
    red: 'shadow-colored-red',
    green: 'shadow-colored-green',
  };

  const intensities = {
    sm: 'shadow-glow-sm',
    md: 'shadow-glow',
    lg: 'shadow-glow-lg',
  };

  return colors[color] || intensities[intensity];
};

// ============================================
// SELECTION STYLES (dla bulk selection)
// ============================================

export const selectionStyles = {
  // Overlay na zaznaczonym elemencie
  overlay: 'absolute inset-0 bg-purple-500/10 pointer-events-none z-10 animate-fade-in',

  // Border dla zaznaczonego
  border: 'border-purple-500 shadow-glow',

  // Checkbox
  checkbox: {
    base: 'w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200',
    unchecked: 'bg-gray-900/80 border-gray-600 hover:border-purple-400 backdrop-blur-sm',
    checked: 'bg-purple-500 border-purple-500 shadow-glow',
  },
};

/**
 * Generuje klasy dla checkbox zaznaczania
 */
export const getSelectionCheckboxClasses = (isChecked = false) => {
  return cn(
    selectionStyles.checkbox.base,
    isChecked ? selectionStyles.checkbox.checked : selectionStyles.checkbox.unchecked
  );
};

// ============================================
// MODAL BACKDROP
// ============================================

export const modalStyles = {
  backdrop: 'fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 animate-fade-in',

  container: 'bg-gray-800 rounded-modal border border-gray-700 w-full max-h-[90vh] overflow-y-auto',

  header: 'flex items-center justify-between p-6 border-b border-gray-700',

  body: 'p-6',

  footer: 'flex items-center justify-end gap-3 p-6 border-t border-gray-700',
};

// ============================================
// GRADIENT TEXT
// ============================================

/**
 * Generuje klasy dla gradientowego tekstu
 */
export const getGradientTextClasses = (gradient = 'primary') => {
  const gradients = {
    primary: 'bg-gradient-to-r from-purple-400 via-fuchsia-400 to-purple-300',
    accent: 'bg-gradient-to-r from-purple-500 to-fuchsia-500',
    blue: 'bg-gradient-to-r from-blue-400 to-cyan-400',
  };

  return cn(
    gradients[gradient] || gradients.primary,
    'bg-clip-text text-transparent'
  );
};

// ============================================
// RESPONSIVE HELPERS
// ============================================

/**
 * Media query hooks do użycia w komponenach
 */
export const mediaQueries = {
  sm: '@media (min-width: 640px)',
  md: '@media (min-width: 768px)',
  lg: '@media (min-width: 1024px)',
  xl: '@media (min-width: 1280px)',
  '2xl': '@media (min-width: 1536px)',
};

// ============================================
// GRID LAYOUTS (często używane)
// ============================================

export const gridLayouts = {
  // Responsive grid dla kart
  cards: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6',

  // 2 kolumny desktop, 1 mobile
  twoColumn: 'grid grid-cols-1 lg:grid-cols-2 gap-6',

  // Sidebar layout
  sidebar: 'grid grid-cols-1 lg:grid-cols-4 gap-6',
  sidebarMain: 'lg:col-span-3',
  sidebarAside: 'lg:col-span-1',
};

// ============================================
// FLEX LAYOUTS
// ============================================

export const flexLayouts = {
  center: 'flex items-center justify-center',
  between: 'flex items-center justify-between',
  start: 'flex items-center justify-start',
  end: 'flex items-center justify-end',
  column: 'flex flex-col',
  columnCenter: 'flex flex-col items-center justify-center',
};

// Export wszystkiego
export default {
  cn,
  conditional,
  getCardClasses,
  getButtonClasses,
  getInputClasses,
  getBadgeClasses,
  getGlowClasses,
  getSelectionCheckboxClasses,
  getGradientTextClasses,
  animations,
  cardStyles,
  buttonStyles,
  inputStyles,
  badgeStyles,
  selectionStyles,
  modalStyles,
  mediaQueries,
  gridLayouts,
  flexLayouts,
};