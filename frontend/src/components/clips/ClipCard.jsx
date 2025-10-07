import { useState } from "react";
import * as LucideIcons from "lucide-react";
import { Award, Calendar, Image, Play, User } from "lucide-react";
import ClipModal from "./ClipModal";
import { getBaseUrl, getThumbnailUrl } from "../../utils/urlHelper";

function ClipCard({ clip }) {
  const [showModal, setShowModal] = useState(false);

  const thumbnailUrl = clip.has_thumbnail ? getThumbnailUrl(clip.id) : null;
  // URL dla WebP - backend automatycznie zwróci WebP jeśli klient obsługuje
  const thumbnailWebPUrl = thumbnailUrl; // Ten sam endpoint, backend decyduje

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("pl-PL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  const formatFileSize = (mb) => {
    return mb < 1 ? `${(mb * 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`;
  };

  const renderAwardIcon = (awardIcon) => {
    // Custom icon (uploaded)
    if (awardIcon.icon_url) {
      return (
        <img
          src={`${getBaseUrl()}${awardIcon.icon_url}`}
          alt={awardIcon.award_name}
          className="w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-800 object-cover"
          onError={(e) => {
            // Fallback to emoji on error
            e.target.style.display = "none";
            const fallback = document.createElement("div");
            fallback.className =
              "w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-800 flex items-center justify-center text-sm";
            fallback.textContent = awardIcon.icon || "🏆";
            e.target.parentElement.appendChild(fallback);
          }}
        />
      );
    }

    // Lucide icon
    if (awardIcon.lucide_icon) {
      const componentName = awardIcon.lucide_icon
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join("");
      const IconComponent = LucideIcons[componentName];

      if (IconComponent) {
        return (
          <div className="w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-800 flex items-center justify-center">
            <IconComponent size={16} />
          </div>
        );
      }
    }

    // Emoji fallback
    return (
      <div
        className="w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-800 flex items-center justify-center text-sm"
        title={`${awardIcon.award_name} (${awardIcon.count}x)`}
      >
        {awardIcon.icon || "🏆"}
      </div>
    );
  };

  return (
    <>
      <div
        onClick={() => setShowModal(true)}
        className="bg-gradient-to-br from-gray-800 to-gray-800/80 rounded-xl overflow-hidden border border-gray-700 hover:border-purple-500/50 hover:shadow-2xl hover:shadow-purple-500/10 transition-all duration-500 cursor-pointer group relative"
      >
        {/* Świecący akcent na hover */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-purple-500 to-transparent"/>
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-fuchsia-500/5"/>
        </div>
        {/* Thumbnail */}
        <div className="relative aspect-video bg-gray-900 flex items-center justify-center overflow-hidden">
          {thumbnailUrl ? (
            <picture>
              {/* WebP source – przeglądarka automatycznie użyje, jeśli obsługuje */}
              <source srcSet={thumbnailWebPUrl} type="image/webp" />
              {/* JPEG fallback */}
              <img
                src={thumbnailUrl}
                alt={clip.filename}
                className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                onError={(e) => {
                  console.error("Thumbnail load error for clip", clip.id);
                  e.target.style.display = "none";
                }}
              />
            </picture>
          ) : (
            <div className="text-gray-600">
              {clip.clip_type === "video" ? (
                <Play size={48} />
              ) : (
                <Image size={48} />
              )}
            </div>
          )}

          {/* Type badge */}
          <div className="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
            {clip.clip_type === "video" ? "Video" : "Screenshot"}
          </div>

          {/* Award Icons Overlay - TOP RIGHT */}
          {clip.award_icons && clip.award_icons.length > 0 && (
            <div className="absolute top-2 right-2 flex items-center -space-x-2">
              {clip.award_icons.slice(0, 5).map((awardIcon, idx) => (
                <div
                  key={`${awardIcon.award_name}-${idx}`}
                  className="relative group/award"
                  style={{ zIndex: 10 - idx }}
                >
                  {renderAwardIcon(awardIcon)}

                  {/* Tooltip on hover */}
                  <div className="absolute bottom-full right-0 mb-2 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover/award:opacity-100 transition whitespace-nowrap pointer-events-none">
                    {awardIcon.count}x
                  </div>
                </div>
              ))}

              {/* +X indicator for more awards */}
              {clip.award_icons.length > 5 && (
                <div className="w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-700 flex items-center justify-center text-xs font-semibold">
                  +{clip.award_icons.length - 5}
                </div>
              )}
            </div>
          )}

          {/* Duration for videos */}
          {clip.duration && (
            <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
              {Math.floor(clip.duration / 60)}:
              {String(clip.duration % 60).padStart(2, "0")}
            </div>
          )}

          {/* Play overlay z fioletowym akcentem */}
          <div className="absolute inset-0 bg-gradient-to-b from-purple-600/10 via-purple-900/30 to-black/70 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500">
            <div className="relative transform group-hover:scale-110 transition-transform duration-500">
              <Play size={56} className="text-white drop-shadow-2xl relative z-10" fill="rgba(255,255,255,0.9)" />
              <div className="absolute inset-0 blur-2xl bg-purple-500/60 animate-pulse"/>
              <div className="absolute inset-0 blur-3xl bg-fuchsia-500/40"/>
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="p-4 relative">
          <h3
            className="font-semibold text-white truncate mb-2 group-hover:bg-gradient-to-r group-hover:from-purple-300 group-hover:to-fuchsia-300 group-hover:bg-clip-text group-hover:text-transparent transition-all duration-300"
            title={clip.filename}
          >
            {clip.filename}
          </h3>

          <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
            <div className="flex items-center gap-1 group-hover:text-purple-300 transition-colors">
              <User size={14} />
              <span>{clip.uploader_username}</span>
            </div>

            <div className="flex items-center gap-1 group-hover:text-purple-300 transition-colors">
              <Calendar size={14} />
              <span>{formatDate(clip.created_at)}</span>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-1 text-yellow-500 group-hover:text-purple-400 transition-colors">
              <Award size={16} className="group-hover:drop-shadow-lg group-hover:animate-pulse" />
              <span className="font-medium">{clip.award_count}</span>
            </div>

            <span className="text-gray-500 group-hover:text-purple-400 transition-colors">
              {formatFileSize(clip.file_size_mb)}
            </span>
          </div>
        </div>
      </div>

      {showModal && (
        <ClipModal clip={clip} onClose={() => setShowModal(false)} />
      )}
    </>
  );
}

export default ClipCard;
