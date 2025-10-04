import { SlidersHorizontal, ArrowUpDown } from "lucide-react";

function SortFilter({
  sortBy,
  sortOrder,
  clipType,
  onSortChange,
  onFilterChange,
}) {
  return (
    <div className="flex flex-wrap items-center gap-4 mb-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
      {/* Sort */}
      <div className="flex items-center gap-2">
        <ArrowUpDown size={20} className="text-gray-400" />
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value, sortOrder)}
          className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="created_at">Data dodania</option>
          <option value="filename">Nazwa</option>
          <option value="file_size">Rozmiar</option>
          <option value="duration">Długość</option>
        </select>

        <button
          onClick={() =>
            onSortChange(sortBy, sortOrder === "asc" ? "desc" : "asc")
          }
          className="p-2 bg-gray-700 hover:bg-gray-600 rounded border border-gray-600"
          title={sortOrder === "asc" ? "Rosnąco" : "Malejąco"}
        >
          {sortOrder === "asc" ? "↑" : "↓"}
        </button>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <SlidersHorizontal size={20} className="text-gray-400" />
        <select
          value={clipType}
          onChange={(e) => onFilterChange(e.target.value)}
          className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Wszystkie</option>
          <option value="video">Video</option>
          <option value="screenshot">Screenshot</option>
        </select>
      </div>
    </div>
  );
}

export default SortFilter;
