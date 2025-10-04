import ClipCard from "./ClipCard";

function ClipGrid({ clips }) {
  if (!clips || clips.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400 text-lg">Brak klipów do wyświetlenia</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
      {clips.map((clip) => (
        <ClipCard key={clip.id} clip={clip} />
      ))}
    </div>
  );
}

export default ClipGrid;
