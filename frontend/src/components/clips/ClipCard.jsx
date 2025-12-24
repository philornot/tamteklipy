import { useState, useMemo, memo } from "react";
import * as LucideIcons from "lucide-react";
import { Award, Calendar, Image, Play, User, Check } from "lucide-react";
import ClipModal from "./ClipModal";
import {
  getThumbnailUrl,
  addTokenToUrl,
  getBaseUrl,
} from "../../utils/urlHelper";
import { logger } from "../../utils/logger";

/**
 * ClipCard component with React.memo and useMemo.
 *
 * Performance optimizations:
 * - Memoized with React.memo to prevent unnecessary re-renders
 * - Custom comparison function for deep props
 * - useMemo for expensive computations
 * - Callback memoization
 *
 * @param {Object} clip - Clip data object
 * @param {number} index - Index in list (for shift-click selection)
 * @param {boolean} selectionMode - Whether selection mode is active
 * @param {boolean} isSelected - Whether this clip is selected
 * @param {Function} onSelectionToggle - Selection toggle callback
 * @param {Function} onClipUpdate - Clip update callback
 */
function ClipCard({
  clip,
  index,
  selectionMode = false,
  isSelected = false,
  onSelectionToggle,
  onClipUpdate,
}) {
  const [showModal, setShowModal] = useState(false);
  const [thumbnailError, setThumbnailError] = useState(false);

  // Memoize expensive URL generation
  const thumbnailUrl = useMemo(
    () => (clip.has_thumbnail ? getThumbnailUrl(clip.id) : null),
    [clip.has_thumbnail, clip.id]
  );

  // Memoize formatted values
  const formattedDate = useMemo(
    () =>
      new Date(clip.created_at).toLocaleDateString("pl-PL", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      }),
    [clip.created_at]
  );

  const formattedSize = useMemo(() => {
    const mb = clip.file_size_mb;
    return mb < 1 ? `${(mb * 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`;
  }, [clip.file_size_mb]);

  const formattedDuration = useMemo(() => {
    if (!clip.duration) return null;
    const mins = Math.floor(clip.duration / 60);
    const secs = clip.duration % 60;
    return `${mins}:${String(secs).padStart(2, "0")}`;
  }, [clip.duration]);

  // Memoize award icons rendering
  const awardIconsElements = useMemo(() => {
    if (!clip.award_icons || clip.award_icons.length === 0) return null;

    return clip.award_icons
      .slice(0, 5)
      .map((awardIcon, idx) => (
        <AwardIconBadge
          key={`${awardIcon.award_name}-${idx}`}
          awardIcon={awardIcon}
          index={idx}
        />
      ));
  }, [clip.award_icons]);

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
        className={`bg-gradient-card rounded-card overflow-hidden border transition-all duration-500 cursor-pointer group relative ${
          isSelected
            ? "border-purple-500 glow scale-[1.02]"
            : "border-gray-700 hover:border-purple-500/50 hover:shadow-card-hover"
        }`}
      >
        {isSelected && <div className="selection-overlay" />}

        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div
            className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent to-transparent ${
              isSelected ? "via-purple-500" : "via-purple-500"
            }`}
          />
          <div
            className={`absolute inset-0 bg-gradient-to-br from-transparent to-transparent ${
              isSelected ? "via-purple-500/10" : "via-purple-500/5"
            }`}
          />
        </div>

        {/* Selection Checkbox */}
        <div
          className={`absolute top-2 left-2 z-20 transition-all duration-300 ${
            selectionMode || isSelected
              ? "opacity-100 scale-100"
              : "opacity-0 scale-90 group-hover:opacity-100 group-hover:scale-100"
          }`}
        >
          <button
            onClick={handleCheckboxClick}
            className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200 ${
              isSelected
                ? "bg-purple-500 border-purple-500 glow"
                : "bg-gray-900/80 border-gray-600 hover:border-purple-400 backdrop-blur-sm"
            }`}
          >
            {isSelected && (
              <Check size={16} className="text-white animate-scale-in" />
            )}
          </button>
        </div>

        {/* Thumbnail */}
        <div className="relative aspect-video bg-gray-900 flex items-center justify-center overflow-hidden">
          {thumbnailUrl && !thumbnailError ? (
            <img
              src={thumbnailUrl}
              alt={clip.filename}
              className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
              loading="lazy"
              onError={() => {
                logger.warn(`Thumbnail not ready for clip ${clip.id}`);
                setThumbnailError(true);
              }}
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-gray-600">
              {clip.clip_type === "video" ? (
                <Play size={48} className="mb-2" />
              ) : (
                <Image size={48} className="mb-2" />
              )}
              <span className="text-xs text-gray-500">
                {thumbnailError ? "Generowanie..." : "Brak miniaturki"}
              </span>
            </div>
          )}

          {/* Badges */}
          <div className="absolute bottom-2 left-2 badge badge-default z-10">
            {clip.clip_type === "video" ? "Video" : "Screenshot"}
          </div>

          {/* Award Icons */}
          {awardIconsElements && (
            <div className="absolute top-2 right-2 flex items-center -space-x-2 z-10">
              {awardIconsElements}
              {clip.award_icons.length > 5 && (
                <div className="w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-700 flex items-center justify-center text-xs font-semibold">
                  +{clip.award_icons.length - 5}
                </div>
              )}
            </div>
          )}

          {/* Duration Badge */}
          {formattedDuration && (
            <div className="absolute bottom-2 right-2 badge badge-default">
              {formattedDuration}
            </div>
          )}

          {/* Play Overlay */}
          {!selectionMode && (
            <div
              className={`absolute inset-0 bg-gradient-to-b from-purple-600/10 via-purple-900/30 to-black/70 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500 ${
                isSelected && "hidden"
              }`}
            >
              <div className="relative transform group-hover:scale-110 transition-transform duration-500">
                <Play
                  size={56}
                  className="text-white drop-shadow-2xl relative z-10"
                  fill="rgba(255,255,255,0.9)"
                />
                <div className="absolute inset-0 blur-2xl bg-purple-500/60 animate-pulse" />
                <div className="absolute inset-0 blur-3xl bg-fuchsia-500/40" />
              </div>
            </div>
          )}
        </div>

        {/* Card Content */}
        <div className="p-4 relative">
          <h3
            className={`font-semibold truncate mb-2 transition-all duration-300 ${
              isSelected
                ? "text-purple-300"
                : "text-white group-hover:gradient-text-primary"
            }`}
            title={clip.filename}
          >
            {clip.filename}
          </h3>

          <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
            <div
              className={`flex items-center gap-1 transition-colors ${
                isSelected ? "text-purple-300" : "group-hover:text-purple-300"
              }`}
            >
              <User size={14} />
              <span>{clip.uploader_username}</span>
            </div>

            <div
              className={`flex items-center gap-1 transition-colors ${
                isSelected ? "text-purple-300" : "group-hover:text-purple-300"
              }`}
            >
              <Calendar size={14} />
              <span>{formattedDate}</span>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <div
              className={`flex items-center gap-1 transition-colors ${
                isSelected
                  ? "text-purple-400"
                  : "text-yellow-500 group-hover:text-purple-400"
              }`}
            >
              <Award
                size={16}
                className="group-hover:drop-shadow-lg group-hover:animate-pulse"
              />
              <span className="font-medium">{clip.award_count}</span>
            </div>

            <span
              className={`transition-colors ${
                isSelected
                  ? "text-purple-400"
                  : "text-gray-500 group-hover:text-purple-400"
              }`}
            >
              {formattedSize}
            </span>
          </div>
        </div>
      </div>

      {!selectionMode && showModal && (
        <ClipModal
          clip={clip}
          onClose={() => setShowModal(false)}
          onClipUpdate={onClipUpdate}
        />
      )}
    </>
  );
}

/**
 * Memoized award icon badge component.
 * Extracted to prevent re-rendering of all badges when one changes.
 */
const AwardIconBadge = memo(({ awardIcon, index }) => {
  const iconElement = useMemo(() => {
    if (awardIcon.icon_url) {
      const iconUrl = addTokenToUrl(`${getBaseUrl()}${awardIcon.icon_url}`);

      return (
        <img
          src={iconUrl}
          alt={awardIcon.award_name}
          className="w-8 h-8 rounded-full border-2 border-gray-900 bg-gray-800 object-cover"
          loading="lazy"
          onError={(e) => {
            logger.error("Award icon load error:", awardIcon.icon_url);
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
  }, [awardIcon]);

  return (
    <div className="relative group/award" style={{ zIndex: 10 - index }}>
      {iconElement}
      <div className="absolute bottom-full right-0 mb-2 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover/award:opacity-100 transition whitespace-nowrap pointer-events-none">
        {awardIcon.count}x
      </div>
    </div>
  );
});

AwardIconBadge.displayName = "AwardIconBadge";

/**
 * Custom comparison function for React.memo.
 * Only re-render if these props actually changed.
 */
function arePropsEqual(prevProps, nextProps) {
  return (
    prevProps.clip.id === nextProps.clip.id &&
    prevProps.clip.award_count === nextProps.clip.award_count &&
    prevProps.isSelected === nextProps.isSelected &&
    prevProps.selectionMode === nextProps.selectionMode &&
    prevProps.index === nextProps.index
  );
}

export default memo(ClipCard, arePropsEqual);
