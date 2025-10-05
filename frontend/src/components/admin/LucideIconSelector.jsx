import { useState, useEffect } from "react";
import { Search, X } from "lucide-react";
import * as LucideIcons from "lucide-react";

function LucideIconSelector({ selectedIcon, onSelect, onClose }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [availableIcons, setAvailableIcons] = useState([]);
  const [filteredIcons, setFilteredIcons] = useState([]);

  useEffect(() => {
    // Pobierz listę z API (opcjonalnie) lub użyj hardcoded
    const icons = [
      "trophy",
      "award",
      "star",
      "flame",
      "zap",
      "heart",
      "thumbs-up",
      "smile",
      "laugh",
      "sparkles",
      "crown",
      "target",
      "crosshair",
      "medal",
      "gem",
      "skull",
      "swords",
      "shield",
      "rocket",
      "bomb",
      "circle-check",
      "circle-x",
      "alert-circle",
      "info",
      "bookmark",
      "flag",
      "gift",
      "lightbulb",
      "music",
    ];
    setAvailableIcons(icons);
    setFilteredIcons(icons);
  }, []);

  useEffect(() => {
    if (searchTerm) {
      setFilteredIcons(
        availableIcons.filter((icon) =>
          icon.toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    } else {
      setFilteredIcons(availableIcons);
    }
  }, [searchTerm, availableIcons]);

  const renderIcon = (iconName) => {
    // Konwertuj kebab-case na PascalCase
    const componentName = iconName
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join("");

    const IconComponent = LucideIcons[componentName];

    if (!IconComponent) {
      return <div className="w-6 h-6 bg-gray-600 rounded" />;
    }

    return <IconComponent size={24} />;
  };

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[80vh] flex flex-col border border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold">Wybierz ikonę Lucide</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded">
            <X size={20} />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-700">
          <div className="relative">
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              size={20}
            />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Szukaj ikony..."
              className="w-full bg-gray-700 border border-gray-600 text-white pl-10 px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Icons Grid */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-6 gap-3">
            {filteredIcons.map((iconName) => (
              <button
                key={iconName}
                onClick={() => onSelect(iconName)}
                className={`p-4 rounded-lg border-2 transition flex flex-col items-center gap-2 hover:border-blue-500 ${
                  selectedIcon === iconName
                    ? "border-blue-500 bg-blue-500/20"
                    : "border-gray-700 hover:bg-gray-700"
                }`}
                title={iconName}
              >
                {renderIcon(iconName)}
                <span className="text-xs text-gray-400 truncate w-full text-center">
                  {iconName}
                </span>
              </button>
            ))}
          </div>

          {filteredIcons.length === 0 && (
            <div className="text-center py-8 text-gray-400">
              Nie znaleziono ikon
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700 text-sm text-gray-400">
          <p>
            Wybrano:{" "}
            <strong className="text-white">{selectedIcon || "brak"}</strong>
          </p>
        </div>
      </div>
    </div>
  );
}

export default LucideIconSelector;
