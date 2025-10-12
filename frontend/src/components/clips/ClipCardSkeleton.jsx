/**
 * Skeleton loader pokazywany podczas ładowania klipów
 * Używa animate-pulse z Tailwind do animacji "pulsowania"
 */
function ClipCardSkeleton() {
  return (
    <div className="bg-dark-800 rounded-card overflow-hidden border border-dark-700 animate-pulse">
      {/* Thumbnail skeleton */}
      <div className="aspect-video bg-dark-700" />

      {/* Info skeleton */}
      <div className="p-4 space-y-3">
        {/* Filename */}
        <div className="h-5 bg-dark-700 rounded w-3/4" />

        {/* Metadata row */}
        <div className="flex items-center gap-4">
          <div className="h-4 bg-dark-700 rounded w-20" />
          <div className="h-4 bg-dark-700 rounded w-24" />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="h-4 bg-dark-700 rounded w-12" />
          <div className="h-4 bg-dark-700 rounded w-16" />
        </div>
      </div>
    </div>
  );
}

export default ClipCardSkeleton;
