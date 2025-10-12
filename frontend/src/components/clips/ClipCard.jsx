import { useState } from "react";
import * as LucideIcons from "lucide-react";
import { Award, Calendar, Image, Play, User, Check } from "lucide-react";
import ClipModal from "./ClipModal";
import { getBaseUrl, getThumbnailUrl, addTokenToUrl } from "../../utils/urlHelper";

function ClipCard({
  clip,
  index,
  selectionMode = false,
  isSelected = false,
  onSelectionToggle,
  onClipUpdate,
}) {
  const [showModal, setShowModal] = useState(false);

  // ✅ Thumbnail URL z tokenem
  const thumbnailUrl = clip.has_thumbnail ? getThumbnailUrl(clip.id) : null;

  // ❌ PROBLEM: WebP URL jest taki sam jak JPEG, ale powinien mieć własny token
  // Musimy go wygenerować osobno
  const thumbnailWebPUrl = thumbnailUrl; // To będzie OK bo getThumbnailUrl() już dodaje token

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
    if (awardIcon.icon_url) {
      // ✅ Dodaj token do custom icon URL
      const iconUrl = addTokenToUrl(`${getBaseUrl()}${awardIcon.icon_url}`);

      return (
        <img
          src={iconUrl}
          alt={awardIcon.award_name}
          className="w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-800 object-cover"
          loading="lazy"
          onError={(e) => {
            console.error("Award icon load error:", awardIcon.icon_url);
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

    return (
      <div
        className="w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-800 flex items-center justify-center text-sm"
        title={`${awardIcon.award_name} (${awardIcon.count}x)`}
      >
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

  const getSelectionCheckboxClasses = (isChecked = false) => {
    const base = "w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200";
    const unchecked = "bg-gray-900/80 border-gray-600 hover:border-purple-400 backdrop-blur-sm";
    const checked = "bg-purple-500 border-purple-500 glow";

    return `${base} ${isChecked ? checked : unchecked}`;
  };

  return (
    <>
      <div
        onClick={handleClick}
        className={`bg-gradient-card rounded-card overflow-hidden border transition-all duration-500 cursor-pointer group relative ${
          isSelected
            ? "border-purple-500 glow scale-[1.02]"
            : "border-gray-700 hover:border-purple-500/50 hover:shadow-card-hover"
        }`}
      >
        {isSelected && <div className="selection-overlay" />}

        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent to-transparent ${isSelected ? "via-purple-500" : "via-purple-500"}`} />
          <div className={`absolute inset-0 bg-gradient-to-br from-transparent to-transparent ${isSelected ? "via-purple-500/10" : "via-purple-500/5"}`} />
        </div>

        <div className={`absolute top-2 left-2 z-20 transition-all duration-300 ${selectionMode || isSelected ? "opacity-100 scale-100" : "opacity-0 scale-90 group-hover:opacity-100 group-hover:scale-100"}`}>
          <button onClick={handleCheckboxClick} className={getSelectionCheckboxClasses(isSelected)}>
            {isSelected && <Check size={16} className="text-white animate-scale-in" />}
          </button>
        </div>

        <div className="relative aspect-video bg-gray-900 flex items-center justify-center overflow-hidden">
          {thumbnailUrl ? (
            // ✅ Uproszczone - jeden <img> tag zamiast <picture>
            // Picture tag może powodować podwójne requesty
            <img
              src={thumbnailUrl}
              alt={clip.filename}
              className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
              loading="lazy"
              onError={(e) => {
                console.error("Thumbnail load error for clip", clip.id);
                console.error("Attempted URL:", thumbnailUrl);
                e.target.style.display = "none";
                // Pokaż placeholder
                e.target.parentElement.innerHTML = `
                  <div class="text-gray-600 flex items-center justify-center">
                    ${clip.clip_type === "video" ? '<svg>...</svg>' : '<svg>...</svg>'}
                  </div>
                `;
              }}
            />
          ) : (
            <div className="text-gray-600">
              {clip.clip_type === "video" ? <Play size={48} /> : <Image size={48} />}
            </div>
          )}

          <div className="absolute bottom-2 left-2 badge badge-default z-10">
            {clip.clip_type === "video" ? "Video" : "Screenshot"}
          </div>

          {clip.award_icons && clip.award_icons.length > 0 && (
            <div className="absolute top-2 right-2 flex items-center -space-x-2 z-10">
              {clip.award_icons.slice(0, 5).map((awardIcon, idx) => (
                <div key={`${awardIcon.award_name}-${idx}`} className="relative group/award" style={{ zIndex: 10 - idx }}>
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

          {clip.duration && (
            <div className="absolute bottom-2 right-2 badge badge-default">
              {Math.floor(clip.duration / 60)}:{String(clip.duration % 60).padStart(2, "0")}
            </div>
          )}

          {!selectionMode && (
            <div className={`absolute inset-0 bg-gradient-to-b from-purple-600/10 via-purple-900/30 to-black/70 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500 ${isSelected && "hidden"}`}>
              <div className="relative transform group-hover:scale-110 transition-transform duration-500">
                <Play size={56} className="text-white drop-shadow-2xl relative z-10" fill="rgba(255,255,255,0.9)" />
                <div className="absolute inset-0 blur-2xl bg-purple-500/60 animate-pulse" />
                <div className="absolute inset-0 blur-3xl bg-fuchsia-500/40" />
              </div>
            </div>
          )}
        </div>

        <div className="p-4 relative">
          <h3 className={`font-semibold truncate mb-2 transition-all duration-300 ${isSelected ? "text-purple-300" : "text-white group-hover:gradient-text-primary"}`} title={clip.filename}>
            {clip.filename}
          </h3>

          <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
            <div className={`flex items-center gap-1 transition-colors ${isSelected ? "text-purple-300" : "group-hover:text-purple-300"}`}>
              <User size={14} />
              <span>{clip.uploader_username}</span>
            </div>

            <div className={`flex items-center gap-1 transition-colors ${isSelected ? "text-purple-300" : "group-hover:text-purple-300"}`}>
              <Calendar size={14} />
              <span>{formatDate(clip.created_at)}</span>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <div className={`flex items-center gap-1 transition-colors ${isSelected ? "text-purple-400" : "text-yellow-500 group-hover:text-purple-400"}`}>
              <Award size={16} className="group-hover:drop-shadow-lg group-hover:animate-pulse" />
              <span className="font-medium">{clip.award_count}</span>
            </div>

            <span className={`transition-colors ${isSelected ? "text-purple-400" : "text-gray-500 group-hover:text-purple-400"}`}>
              {formatFileSize(clip.file_size_mb)}
            </span>
          </div>
        </div>
      </div>

      {!selectionMode && showModal && (
        <ClipModal clip={clip} onClose={() => setShowModal(false)} onClipUpdate={onClipUpdate} />
      )}
    </>
  );
}

export default ClipCard;
