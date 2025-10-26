import { useCallback, useEffect, useRef, useState } from "react";
import { AlertCircle, Loader } from "lucide-react";
import VerticalVideoPlayer from "./VerticalVideoPlayer.jsx";

/**
 * Vertical Feed Container - główny komponent
 */
function VerticalFeed() {
  const [clips, setClips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);

  // Fetch initial clips
  const fetchClips = useCallback(async (excludeIds = []) => {
    try {
      const token = localStorage.getItem("access_token");
      const excludeQuery =
        excludeIds.length > 0
          ? `&${excludeIds.map((id) => `exclude_ids=${id}`).join("&")}`
          : "";

      const response = await fetch(
        `${
          import.meta.env.VITE_API_URL || ""
        }/api/files/clips/random?limit=10${excludeQuery}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        setError("Nie udało się załadować klipów");
        return [];
      }
      const data = await response.json();
      return data.clips;
    } catch (err) {
      console.error("Fetch error:", err);
      setError("Nie udało się załadować klipów");
      return [];
    }
  }, []);

  useEffect(() => {
    fetchClips().then((initialClips) => {
      setClips(initialClips);
      setLoading(false);
    });
  }, [fetchClips]);

  useEffect(() => {
  if (clips.length > 0) {
    // Prefetch następnych 2 klipów
    const nextClips = clips.slice(currentIndex + 1, currentIndex + 3);

    nextClips.forEach((clip) => {
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.src = getStreamUrl(clip.id);

      // Memory cleanup - usuń po 30s jeśli nie użyty
      setTimeout(() => {
        video.src = '';
      }, 30000);
    });

    // Cleanup poprzednich (>3 klipy wstecz)
    if (currentIndex > 3) {
      // Browser GC powinien to obsłużyć automatycznie
    }
  }
}, [clips, currentIndex]);

  // Snap scroll handler
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const scrollTop = containerRef.current.scrollTop;
    const windowHeight = window.innerHeight;
    const newIndex = Math.round(scrollTop / windowHeight);

    if (newIndex !== currentIndex) {
      setCurrentIndex(newIndex);

      // Prefetch more clips gdy zbliżamy się do końca
      if (newIndex >= clips.length - 3) {
        const excludeIds = clips.map((c) => c.id);
        fetchClips(excludeIds).then((newClips) => {
          if (newClips.length > 0) {
            setClips((prev) => [...prev, ...newClips]);
          }
        });
      }
    }
  }, [currentIndex, clips, fetchClips]);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-black">
        <Loader className="animate-spin text-purple-500" size={48} />
      </div>
    );
  }

  if (error || clips.length === 0) {
    return (
      <div className="h-screen flex items-center justify-center bg-black px-4">
        <div className="text-center">
          <AlertCircle size={64} className="mx-auto mb-4 text-red-400" />
          <p className="text-white text-lg mb-2">
            {error || "Brak klipów do wyświetlenia"}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg"
          >
            Spróbuj ponownie
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
        className="h-screen overflow-y-scroll snap-y snap-mandatory vertical-feed smooth-scroll"
      style={{
        scrollSnapType: "y mandatory",
        WebkitOverflowScrolling: "touch",
      }}
      onScroll={handleScroll}
    >
      {clips.map((clip, index) => (
        <div key={clip.id} className="h-screen snap-start snap-always">
          <VerticalVideoPlayer
            clip={clip}
            isActive={index === currentIndex}
            onEnded={() => {
              // Auto-scroll to next
              if (index < clips.length - 1) {
                containerRef.current?.scrollTo({
                  top: (index + 1) * window.innerHeight,
                  behavior: "smooth",
                });
              }
            }}
          />
        </div>
      ))}
    </div>
  );
}

const [touchStart, setTouchStart] = useState(0);
const [touchEnd, setTouchEnd] = useState(0);

const handleTouchStart = (e) => {
  setTouchStart(e.targetTouches[0].clientY);
};

const handleTouchMove = (e) => {
  setTouchEnd(e.targetTouches[0].clientY);
};

const handleTouchEnd = () => {
  if (!touchStart || !touchEnd) return;

  const distance = touchStart - touchEnd;
  const isSwipe = Math.abs(distance) > 50;

  if (isSwipe) {
    if (distance > 0) {
      // Swipe up - następny klip
      const nextIndex = currentIndex + 1;
      if (nextIndex < clips.length) {
        containerRef.current?.scrollTo({
          top: nextIndex * window.innerHeight,
          behavior: "smooth",
        });
      }
    } else {
      // Swipe down - poprzedni klip
      const prevIndex = currentIndex - 1;
      if (prevIndex >= 0) {
        containerRef.current?.scrollTo({
          top: prevIndex * window.innerHeight,
          behavior: "smooth",
        });
      }
    }
  }

  setTouchStart(0);
  setTouchEnd(0);
};

export default VerticalFeed;
