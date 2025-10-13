// frontend/src/components/comments/MentionAutocomplete.jsx
import { useState, useEffect } from 'react';
import { User } from 'lucide-react';
import api from '../../services/api';
import { logger } from '../../utils/logger';

function MentionAutocomplete({ query, onSelect, onClose }) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!query || query.length < 2) {
        setSuggestions([]);
        return;
      }

      setLoading(true);
      try {
        const response = await api.get('/users/mentions', {
          params: { query, limit: 5 }
        });
        setSuggestions(response.data);
        setSelectedIndex(0);
      } catch (err) {
        logger.error('Failed to fetch mention suggestions:', err);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(fetchSuggestions, 200);
    return () => clearTimeout(debounceTimer);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (suggestions.length === 0) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
      } else if (e.key === 'Enter' && suggestions[selectedIndex]) {
        e.preventDefault();
        onSelect(suggestions[selectedIndex].username);
      } else if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [suggestions, selectedIndex, onSelect, onClose]);

  if (loading) {
    return (
      <div className="absolute bottom-full left-0 mb-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-3 z-50">
        <div className="text-gray-400 text-sm">Szukam...</div>
      </div>
    );
  }

  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className="absolute bottom-full left-0 mb-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl overflow-hidden z-50 min-w-[200px]">
      {suggestions.map((suggestion, index) => (
        <button
          key={suggestion.user_id}
          onClick={() => onSelect(suggestion.username)}
          onMouseEnter={() => setSelectedIndex(index)}
          className={`w-full flex items-center gap-3 px-4 py-2 transition ${
            index === selectedIndex
              ? 'bg-purple-600 text-white'
              : 'text-gray-300 hover:bg-gray-700'
          }`}
        >
          <User size={16} />
          <div className="flex-1 text-left">
            <div className="font-medium">@{suggestion.username}</div>
            {suggestion.full_name && (
              <div className="text-xs opacity-75">{suggestion.full_name}</div>
            )}
          </div>
        </button>
      ))}

      <div className="px-4 py-2 bg-gray-900 border-t border-gray-700 text-xs text-gray-500">
        ↑↓ nawiguj, Enter wybierz, Esc anuluj
      </div>
    </div>
  );
}

export default MentionAutocomplete;
