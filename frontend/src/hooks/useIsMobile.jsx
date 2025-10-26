import { useState, useEffect } from 'react';

/**
 * Hook do wykrywania czy user jest na mobile
 * Breakpoint: 768px (Tailwind md)
 *
 * @returns {boolean} true jeśli viewport < 768px
 */
export function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Media query
    const mediaQuery = window.matchMedia('(max-width: 767px)');

    // Set initial value
    setIsMobile(mediaQuery.matches);

    // Handler
    const handler = (e) => setIsMobile(e.matches);

    // Modern API
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    } else {
      // Fallback dla starszych przeglądarek
      mediaQuery.addListener(handler);
      return () => mediaQuery.removeListener(handler);
    }
  }, []);

  return isMobile;
}

export default useIsMobile;