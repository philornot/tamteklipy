/**
 * Color class mappings for Tailwind CSS 4 compatibility
 * Używaj tych klas zamiast custom dark-* i primary-* w komponentach
 */

export const colors = {
  // Background colors
  bg: {
    dark900: 'bg-gray-900',
    dark800: 'bg-gray-800',
    dark700: 'bg-gray-700',
    dark600: 'bg-gray-600',

    primary: 'bg-purple-500',
    primaryHover: 'bg-purple-600',
    primaryLight: 'bg-purple-400',
    primaryDark: 'bg-purple-700',

    accent: 'bg-fuchsia-500',
    accentHover: 'bg-fuchsia-600',

    success: 'bg-green-500',
    danger: 'bg-red-500',
    warning: 'bg-yellow-500',
    info: 'bg-blue-500',
  },

  // Text colors
  text: {
    primary: 'text-gray-100',
    secondary: 'text-gray-400',
    tertiary: 'text-gray-500',

    primary500: 'text-purple-500',
    primary400: 'text-purple-400',

    accent: 'text-fuchsia-500',
    accent400: 'text-fuchsia-400',

    success: 'text-green-500',
    danger: 'text-red-500',
    warning: 'text-yellow-500',
    info: 'text-blue-500',
  },

  // Border colors
  border: {
    dark700: 'border-gray-700',
    dark600: 'border-gray-600',

    primary: 'border-purple-500',
    success: 'border-green-500',
    danger: 'border-red-500',
    warning: 'border-yellow-500',
  }
};

// Helper function to get classes
export const getColorClass = (type, name) => {
  return colors[type]?.[name] || '';
};