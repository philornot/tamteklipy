import ClipCard from "./ClipCard";
import ClipCardSkeleton from "./ClipCardSkeleton";

function ClipGrid({
  clips,
  loading,
  selectionMode = false,
  selectedIds = [],
  onSelectionToggle,
  onClipUpdate,
}) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
        {Array.from({ length: 8 }).map((_, i) => (
          <ClipCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!clips || clips.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400 text-lg">Brak klipów do wyświetlenia</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
      {clips.map((clip, index) => (
        <ClipCard
          key={clip.id}
          clip={clip}
          index={index}
          selectionMode={selectionMode}
          isSelected={selectedIds.includes(clip.id)}
          onSelectionToggle={onSelectionToggle}
          onClipUpdate={onClipUpdate} // PRZEKAŻ DALEJ
        />
      ))}
    </div>
  );
}

export default ClipGrid;
