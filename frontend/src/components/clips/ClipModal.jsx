import { useCallback, useEffect, useRef, useState } from "react";
import { Calendar, Clock, Download, ImageIcon, User, X } from "lucide-react";
import api from "../../services/api";
import AwardSection from "./AwardSection";
import CommentSection from "../comments/CommentSection";
import { getDownloadUrl, getStreamUrl } from "../../utils/urlHelper";
import { Button, Badge } from "../ui/StyledComponents";

function ClipModal({ clip, onClose, onClipUpdate }) {
  const [clipDetails, setClipDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const videoRef = useRef(null);

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

    const handleEsc = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [fetchClipDetails, onClose]);

  const handleDownload = () => {
    const downloadUrl = getDownloadUrl(clip.id);
    console.log("Downloading from:", downloadUrl);
    window.open(downloadUrl, "_blank");
  };

  const handleAwardsChange = (newAwards) => {
    if (clipDetails) {
      setClipDetails({
        ...clipDetails,
        awards: newAwards,
      });
    }

    if (onClipUpdate) {
      onClipUpdate(clip.id);
    }
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

  const mediaUrl =
    clip.clip_type === "video"
      ? getStreamUrl(clip.id)
      : getDownloadUrl(clip.id);

  return (
    <div
      className="modal-backdrop animate-fade-in"
      onClick={onClose}
    >
      <div
        className="modal-container max-w-6xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-700">
          <h2 className="text-xl font-bold truncate flex-1">{clip.filename}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-dark-700 rounded-button transition-colors"
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
                  ref={videoRef}
                  controls
                  autoPlay
                  className="w-full rounded-card bg-black"
                  src={mediaUrl}
                  onError={(e) => {
                    console.error("Video load error:", e);
                    console.error("Attempted URL:", mediaUrl);
                  }}
                >
                  Twoja przeglądarka nie obsługuje video.
                </video>
              ) : (
                <img
                  src={mediaUrl}
                  alt={clip.filename}
                  className="w-full rounded-card"
                  onError={(e) => {
                    console.error("Image load error:", e);
                    console.error("Attempted URL:", mediaUrl);
                  }}
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
              <Button
                onClick={handleDownload}
                variant="primary"
                className="mt-4 w-full"
              >
                <Download size={20} />
                Pobierz ({clip.file_size_mb.toFixed(1)} MB)
              </Button>

              {/* Comments Section */}
              <div className="mt-8 border-t border-dark-700 pt-6">
                {!loading && (
                  <CommentSection
                    clipId={clip.id}
                    videoRef={clip.clip_type === "video" ? videoRef : null}
                  />
                )}
              </div>
            </div>

            {/* Right: Awards Section */}
            <div className="lg:col-span-1">
              {loading ? (
                <div className="text-gray-400">Ładowanie nagród...</div>
              ) : clipDetails ? (
                <AwardSection
                  clipId={clip.id}
                  initialAwards={clipDetails.awards}
                  onAwardsChange={handleAwardsChange}
                />
              ) : (
                <div className="text-danger">
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
