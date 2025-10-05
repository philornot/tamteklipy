import { useEffect, useState, useCallback } from "react";
import {
  X,
  Download,
  Award,
  User,
  Calendar,
  Clock,
  ImageIcon,
} from "lucide-react";
import api, {getBaseURL} from "../../services/api";
import AwardSection from "./AwardSection";

function ClipModal({ clip, onClose }) {
  const [clipDetails, setClipDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchClipDetails = useCallback(async () => {
    try {
      const response = await api.get(`/files/clips/${clip.id}`);
      setClipDetails(response.data);
    } catch (err) {
      console.error("Failed to fetch clip details:", err);
    } finally {
      setLoading(false);
    }
  }, [clip.id]);

  useEffect(() => {
    fetchClipDetails();

    // ESC key handler
    const handleEsc = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [fetchClipDetails, onClose]);

  const handleDownload = () => {
window.open(`${getBaseURL()}/api/files/download/${clip.id}`, "_blank");
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString("pl-PL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${String(secs).padStart(2, "0")}`;
  };

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto border border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold truncate flex-1">{clip.filename}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded transition"
            title="Zamknij (ESC)"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Media Player */}
            <div className="lg:col-span-2">
              {clip.clip_type === "video" ? (
                <video
                  controls
                  autoPlay
                  className="w-full rounded-lg bg-black"
                  src={`${getBaseURL()}/api/files/stream/${clip.id}`}
                >
                  Twoja przeglądarka nie obsługuje video. What a shame.
                </video>
              ) : (
                <img
                  src={`${getBaseURL()}/api/files/download/${clip.id}`}
                  alt={clip.filename}
                  className="w-full rounded-lg"
                />
              )}

              {/* Metadata */}
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2 text-gray-400">
                  <User size={16} />
                  <span>
                    Uploader:{" "}
                    <strong className="text-white">
                      {clip.uploader_username}
                    </strong>
                  </span>
                </div>

                <div className="flex items-center gap-2 text-gray-400">
                  <Calendar size={16} />
                  <span>{formatDate(clip.created_at)}</span>
                </div>

                {clip.duration && (
                  <div className="flex items-center gap-2 text-gray-400">
                    <Clock size={16} />
                    <span>Długość: {formatDuration(clip.duration)}</span>
                  </div>
                )}

                {clip.width && clip.height && (
                  <div className="flex items-center gap-2 text-gray-400">
                    <ImageIcon size={16} />
                    <span>
                      Rozdzielczość: {clip.width}x{clip.height}
                    </span>
                  </div>
                )}
              </div>

              {/* Download button */}
              <button
                onClick={handleDownload}
                className="mt-4 btn-primary w-full flex items-center justify-center gap-2"
              >
                <Download size={20} />
                Pobierz ({clip.file_size_mb.toFixed(1)} MB)
              </button>
            </div>

            {/* Right: Awards Section */}
            <div className="lg:col-span-1">
              {loading ? (
                <div className="text-gray-400">Ładowanie nagród...</div>
              ) : clipDetails ? (
                <AwardSection
                  clipId={clip.id}
                  initialAwards={clipDetails.awards}
                />
              ) : (
                <div className="text-red-400">
                  Nie udało się załadować nagród
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ClipModal;
