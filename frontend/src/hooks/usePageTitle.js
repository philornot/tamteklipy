/**
 * usePageTitle - Custom React Hook
 *
 * Automatycznie ustawia tytuł strony w formacie "TamteKlipy - {title}"
 * i przywraca poprzedni tytuł przy unmount komponentu.
 *
 * Użycie:
 *   import { usePageTitle } from "../hooks/usePageTitle";
 *
 *   function DashboardPage() {
 *     usePageTitle("Dashboard");  // → "TamteKlipy - Dashboard"
 *     // ... reszta komponentu
 *   }
 *
 * Lokalizacja: frontend/src/hooks/usePageTitle.js
 */

import { useEffect } from 'react';

/**
 * Hook do dynamicznego ustawiania tytułu strony
 *
 * @param {string} title - Tytuł sekcji (np. "Dashboard", "Upload")
 *
 * @example
 * usePageTitle("Dashboard");  // → "TamteKlipy - Dashboard"
 * usePageTitle("Upload");     // → "TamteKlipy - Upload"
 * usePageTitle(null);         // → "TamteKlipy"
 */
export const usePageTitle = (title) => {
  useEffect(() => {
    // Zapisz poprzedni tytuł (dla cleanup)
    const prevTitle = document.title;

    // Ustaw nowy tytuł
    if (title) {
      document.title = `TamteKlipy - ${title}`;
    } else {
      document.title = 'TamteKlipy';
    }

    // Cleanup function - przywróć poprzedni tytuł przy unmount
    // (opcjonalne - w praktyce nie jest potrzebne dla SPA)
    return () => {
      document.title = prevTitle;
    };
  }, [title]); // Re-run jeśli title się zmieni
};

// Default export dla wygody
export default usePageTitle;