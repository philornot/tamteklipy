import { useState } from "react";
import * as LucideIcons from "lucide-react";
import { Award, Calendar, Image, Play, User, Check } from "lucide-react";
import ClipModal from "./ClipModal";
import { getBaseUrl, getThumbnailUrl } from "../../utils/urlHelper";

function ClipCard({
  clip,
  index,
  selectionMode = false,
  isSelected = false,
  onSelectionToggle
}) {
  const [showModal, setShowModal] = useState(false);

  const thumbnailUrl = clip.has_thumbnail ? getThumbnailUrl(clip.id) : null;
  const thumbnailWebPUrl = thumbnailUrl; // backend decyduje o WebP

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
        title={`${awardIcon.award_name} (${awardIcon.count}x)`}>
        {awardIcon.icon || "🏆"}
      </div>
    );
  };

  const handleClick = (e) => {
    if (selectionMode) {
      e.stopPropagation();
      onSelectionToggle?.(clip.id, index, e.shiftKey);
    } else {
      setShowModal(true);
    }
  };

  const handleCheckboxClick = (e) => {
    e.stopPropagation();
    onSelectionToggle?.(clip.id, index, e.shiftKey);
  };

  return (
    <>
      <div
        onClick={handleClick}
        className={`bg-gradient-to-br from-gray-800 to-gray-800/80 rounded-xl overflow-hidden border transition-all duration-500 cursor-pointer group relative ${
          isSelected
            ? 'border-blue-500 shadow-xl shadow-blue-500/30 scale-[1.02]'
            : 'border-gray-700 hover:border-purple-500/50 hover:shadow-2xl hover:shadow-purple-500/10'
        }`}
      >
        {/* Selection highlight */}
        {isSelected && (
          <div className="absolute inset-0 bg-blue-500/10 pointer-events-none z-10 animate-fadeIn" />
        )}

        {/* Hover glow accent */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent to-transparent ${
            isSelected ? 'via-blue-500' : 'via-purple-500'
          }`}/>
          <div className={`absolute inset-0 bg-gradient-to-br from-transparent to-transparent ${
            isSelected ? 'via-blue-500/10' : 'via-purple-500/5'
          }`}/>
        </div>

        {/* Checkbox */}
        <div
          className={`absolute top-3 left-3 z-20 transition-all duration-300 ${
            selectionMode || isSelected ? 'opacity-100 scale-100' : 'opacity-0 scale-90 group-hover:opacity-100 group-hover:scale-100'
          }`}
        >
          <button
            onClick={handleCheckboxClick}
            className={`w-6 h-6 rounded-md border-2 flex items-center justify-center transition-all duration-200 ${
              isSelected
                ? 'bg-blue-500 border-blue-500 shadow-lg shadow-blue-500/50'
                : 'bg-gray-900/80 border-gray-600 hover:border-blue-400 backdrop-blur-sm'
            }`}
          >
            {isSelected && (
              <Check size={16} className="text-white animate-scaleIn" />
            )}
          </button>
        </div>

        {/* Thumbnail */}
        <div className="relative aspect-video bg-gray-900 flex items-center justify-center overflow-hidden">
          {thumbnailUrl ? (
            <picture>
              <source srcSet={thumbnailWebPUrl} type="image/webp" />
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
              {clip.clip_type === "video" ? <Play size={48} /> : <Image size={48} />}
            </div>
          )}

          {/* Type badge */}
          <div className="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
            {clip.clip_type === "video" ? "Video" : "Screenshot"}
          </div>

          {/* Awards */}
          {clip.award_icons && clip.award_icons.length > 0 && (
            <div className="absolute top-2 right-2 flex items-center -space-x-2">
              {clip.award_icons.slice(0, 5).map((awardIcon, idx) => (
                <div
                  key={`${awardIcon.award_name}-${idx}`}
                  className="relative group/award"
                  style={{ zIndex: 10 - idx }}
                >
                  {renderAwardIcon(awardIcon)}
                  <div className="absolute bottom-full right-0 mb-2 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover/award:opacity-100 transition whitespace-nowrap pointer-events-none">
                    {awardIcon.count}x
                  </div>
                </div>
              ))}
              {clip.award_icons.length > 5 && (
                <div className="w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-700 flex items-center justify-center text-xs font-semibold">
                  +{clip.award_icons.length - 5}
                </div>
              )}
            </div>
          )}

          {/* Duration */}
          {clip.duration && (
            <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
              {Math.floor(clip.duration / 60)}:
              {String(clip.duration % 60).padStart(2, "0")}
            </div>
          )}

          {/* Play overlay (disabled in selection mode) */}
          {!selectionMode && (
            <div className={`absolute inset-0 bg-gradient-to-b from-purple-600/10 via-purple-900/30 to-black/70 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500 ${
              isSelected ? 'hidden' : ''
            }`}>
              <div className="relative transform group-hover:scale-110 transition-transform duration-500">
                <Play size={56} className="text-white drop-shadow-2xl relative z-10" fill="rgba(255,255,255,0.9)" />
                <div className="absolute inset-0 blur-2xl bg-purple-500/60 animate-pulse"/>
                <div className="absolute inset-0 blur-3xl bg-fuchsia-500/40"/>
              </div>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="p-4 relative">
          <h3
            className={`font-semibold truncate mb-2 transition-all duration-300 ${
              isSelected 
                ? 'text-blue-300'
                : 'text-white group-hover:bg-gradient-to-r group-hover:from-purple-300 group-hover:to-fuchsia-300 group-hover:bg-clip-text group-hover:text-transparent'
            }`}
            title={clip.filename}
          >
            {clip.filename}
          </h3>

          <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
            <div className={`flex items-center gap-1 transition-colors ${
              isSelected ? 'text-blue-300' : 'group-hover:text-purple-300'
            }`}>
              <User size={14} />
              <span>{clip.uploader_username}</span>
            </div>

            <div className={`flex items-center gap-1 transition-colors ${
              isSelected ? 'text-blue-300' : 'group-hover:text-purple-300'
            }`}>
              <Calendar size={14} />
              <span>{formatDate(clip.created_at)}</span>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <div className={`flex items-center gap-1 transition-colors ${
              isSelected 
                ? 'text-blue-400' 
                : 'text-yellow-500 group-hover:text-purple-400'
            }`}>
              <Award size={16} className="group-hover:drop-shadow-lg group-hover:animate-pulse" />
              <span className="font-medium">{clip.award_count}</span>
            </div>

            <span className={`transition-colors ${
              isSelected ? 'text-blue-400' : 'text-gray-500 group-hover:text-purple-400'
            }`}>
              {formatFileSize(clip.file_size_mb)}
            </span>
          </div>
        </div>
      </div>

      {!selectionMode && showModal && (
        <ClipModal clip={clip} onClose={() => setShowModal(false)} />
      )}
    </>
  );
}

export default ClipCard;
