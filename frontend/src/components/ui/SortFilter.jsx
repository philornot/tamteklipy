import { SlidersHorizontal, ArrowUpDown } from "lucide-react";
import { Card, Select } from "./StyledComponents";

function SortFilter({
  sortBy,
  sortOrder,
  clipType,
  onSortChange,
  onFilterChange,
}) {
  const sortOptions = [
    { value: "created_at", label: "Data dodania" },
    { value: "filename", label: "Nazwa" },
    { value: "file_size", label: "Rozmiar" },
    { value: "duration", label: "Długość" },
  ];

  const filterOptions = [
    { value: "", label: "Wszystkie" },
    { value: "video", label: "Video" },
    { value: "screenshot", label: "Screenshot" },
  ];

  return (
    <Card className="flex flex-wrap items-center gap-4 mb-6 p-4">
      {/* Sort */}
      <div className="flex items-center gap-2">
        <ArrowUpDown size={20} className="text-gray-400" />
        <Select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value, sortOrder)}
          options={sortOptions}
          className="min-w-[160px]"
        />

        <button
          onClick={() =>
            onSortChange(sortBy, sortOrder === "asc" ? "desc" : "asc")
          }
          className="p-2 bg-dark-700 hover:bg-dark-600 rounded-button border border-dark-600 transition-colors"
          title={sortOrder === "asc" ? "Rosnąco" : "Malejąco"}
        >
          {sortOrder === "asc" ? "↑" : "↓"}
        </button>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <SlidersHorizontal size={20} className="text-gray-400" />
        <Select
          value={clipType}
          onChange={(e) => onFilterChange(e.target.value)}
          options={filterOptions}
          className="min-w-[160px]"
        />
      </div>
    </Card>
  );
}

export default SortFilter;
