import { useEffect, useRef, useState } from "react";
import { AlertCircle, Volume2, VolumeX } from "lucide-react";
import AwardButton from './AwardButton';

/**
 * Vertical Video Player - pojedynczy klip
 */
function VerticalVideoPlayer({ clip, isActive, onEnded }) {
  const videoRef = useRef(null);
  const [isMuted, setIsMuted] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState(null);

  // Autoplay gdy aktywny
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (isActive) {
      video.play().catch((err) => {
        console.error("Autoplay failed:", err);
        setError("Nie można odtworzyć video");
      });
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  }, [isActive]);

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const togglePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused) {
      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  };

  const streamUrl = `${import.meta.env.VITE_API_URL || ""}/api/files/stream/${
    clip.id
  }?token=${localStorage.getItem("access_token")}`;

  return (
    <div className="relative w-full h-full bg-black">
      {/* Video */}
      <video
        ref={videoRef}
        src={streamUrl}
        className="absolute inset-0 w-full h-full object-cover"
        playsInline
        loop
        muted={isMuted}
        onClick={togglePlayPause}
        onEnded={onEnded}
        onError={(e) => {
          console.error("Video error:", e);
          setError("Nie można załadować video");
        }}
      />

      {/* Gradient overlay na dole */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/80 to-transparent pointer-events-none" />

      {/* Metadata */}
      <div className="absolute bottom-20 left-0 right-0 px-4 pb-4 text-white z-10">
        <p className="font-semibold text-lg mb-1 drop-shadow-lg">
          {clip.filename}
        </p>
        <p className="text-sm text-gray-300 drop-shadow-lg">
          @{clip.uploader_username}
        </p>
      </div>

      {/* Mute/Unmute Button */}
      <button
        onClick={toggleMute}
        className="absolute top-4 right-4 p-3 bg-black/50 backdrop-blur-sm rounded-full z-20 transition-all hover:bg-black/70"
        aria-label={isMuted ? "Unmute" : "Mute"}
      >
        {isMuted ? (
          <VolumeX size={20} className="text-white" />
        ) : (
          <Volume2 size={20} className="text-white" />
        )}
      </button>

      {/* Play/Pause Indicator (center tap) */}
      {!isPlaying && !error && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-20 h-20 bg-black/50 backdrop-blur-sm rounded-full flex items-center justify-center">
            <div className="w-0 h-0 border-t-[12px] border-t-transparent border-l-[20px] border-l-white border-b-[12px] border-b-transparent ml-1" />
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80">
          <div className="text-center px-4">
            <AlertCircle size={48} className="mx-auto mb-3 text-red-400" />
            <p className="text-white">{error}</p>
          </div>
        </div>
      )}
        <AwardButton clipId={clip.id} />
    </div>
  );
}

export default VerticalVideoPlayer;
