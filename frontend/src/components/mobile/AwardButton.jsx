import { useState, useEffect } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';

function AwardButton({ clipId }) {
  const [myAwards, setMyAwards] = useState([]);
  const [selectedAward, setSelectedAward] = useState(null);
  const [showMenu, setShowMenu] = useState(false);
  const [loading, setLoading] = useState(false);
  const [longPressTimer, setLongPressTimer] = useState(null);

  useEffect(() => {
    fetchMyAwards();
  }, []);

  const fetchMyAwards = async () => {
    try {
      const response = await api.get('/awards/my-awards');
      const awards = response.data.available_awards;
      setMyAwards(awards);
      if (awards.length > 0 && !selectedAward) {
        setSelectedAward(awards[0]);
      }
    } catch (err) {
      console.error('Failed to fetch awards:', err);
    }
  };

  const handleTouchStart = () => {
    const timer = setTimeout(() => {
      setShowMenu(true);
    }, 500);
    setLongPressTimer(timer);
  };

  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
  };

  const handleQuickAward = async () => {
    if (!selectedAward || loading) return;

    setLoading(true);
    try {
      await api.post(`/awards/clips/${clipId}`, {
        award_name: selectedAward.award_name
      });

      // Animacja sukcesu
      toast.success(`Przyznano: ${selectedAward.display_name}`, {
        icon: selectedAward.icon,
        duration: 2000
      });
    } catch (err) {
      toast.error(err.response?.data?.message || 'Nie udało się przyznać nagrody');
    } finally {
      setLoading(false);
    }
  };

  const selectAward = (award) => {
    setSelectedAward(award);
    setShowMenu(false);
  };

  if (myAwards.length === 0) return null;

  return (
    <>
      {/* Award Button */}
      <button
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onClick={handleQuickAward}
        disabled={loading}
        className="fixed right-4 top-1/2 -translate-y-1/2 z-30 w-16 h-16 bg-gradient-to-br from-purple-500 to-fuchsia-500 rounded-full flex items-center justify-center shadow-glow transition-transform active:scale-95 disabled:opacity-50"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      >
        <span className="text-3xl">{selectedAward?.icon || '🏆'}</span>
      </button>

      {/* Award Menu */}
      {showMenu && (
        <div
          className="fixed inset-0 bg-black/80 z-40 flex items-center justify-center p-4"
          onClick={() => setShowMenu(false)}
        >
          <div
            className="bg-gray-800 rounded-2xl p-4 max-w-sm w-full space-y-2"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold mb-3 text-center">Wybierz nagrodę</h3>

            {myAwards.map((award) => (
              <button
                key={award.award_name}
                onClick={() => selectAward(award)}
                className={`w-full p-4 rounded-lg flex items-center gap-3 transition ${
                  selectedAward?.award_name === award.award_name
                    ? 'bg-purple-500/20 border-2 border-purple-500'
                    : 'bg-gray-700 hover:bg-gray-600 border-2 border-transparent'
                }`}
              >
                <span className="text-3xl">{award.icon}</span>
                <div className="flex-1 text-left">
                  <p className="font-semibold">{award.display_name}</p>
                  <p className="text-xs text-gray-400">{award.description}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

export default AwardButton;