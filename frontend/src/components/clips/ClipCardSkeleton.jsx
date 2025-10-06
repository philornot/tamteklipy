/**
 * Skeleton loader pokazywany podczas ładowania klipów
 * Używa animate-pulse z Tailwind do animacji "pulsowania"
 */
function ClipCardSkeleton() {
  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 animate-pulse">
      {/* Thumbnail skeleton */}
      <div className="aspect-video bg-gray-700" />

      {/* Info skeleton */}
      <div className="p-4 space-y-3">
        {/* Filename */}
        <div className="h-5 bg-gray-700 rounded w-3/4" />

        {/* Metadata row */}
        <div className="flex items-center gap-4">
          <div className="h-4 bg-gray-700 rounded w-20" />
          <div className="h-4 bg-gray-700 rounded w-24" />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="h-4 bg-gray-700 rounded w-12" />
          <div className="h-4 bg-gray-700 rounded w-16" />
        </div>
      </div>
    </div>
  );
}

export default ClipCardSkeleton;