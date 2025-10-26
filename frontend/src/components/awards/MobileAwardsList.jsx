import { Edit2, Trash2 } from 'lucide-react';
import * as LucideIcons from 'lucide-react';
import { getBaseUrl } from '../../utils/urlHelper';

function MobileAwardsList({ awards, awardTypesMap, onEdit, onDelete }) {
  const renderIcon = (award) => {
    const awardType = awardTypesMap[award.id];

    if (awardType?.icon_type === 'custom' && awardType.icon_url) {
      return (
        <img
          src={`${getBaseUrl()}${awardType.icon_url}`}
          alt={awardType.display_name}
          className="w-16 h-16 rounded object-cover"
        />
      );
    }

    if (awardType?.icon_type === 'lucide' && awardType.lucide_icon) {
      const componentName = awardType.lucide_icon
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join('');
      const IconComponent = LucideIcons[componentName];

      return IconComponent ? (
        <IconComponent size={64} />
      ) : (
        <span className="text-5xl">{awardType.icon || '🏆'}</span>
      );
    }

    return <span className="text-5xl">{award.icon || '🏆'}</span>;
  };

  return (
    <div className="space-y-3 pb-20">
      {awards.map((award) => (
        <div
          key={award.id}
          className="bg-gray-800 rounded-xl p-4 border border-gray-700"
        >
          <div className="flex items-center gap-4 mb-3">
            {/* Icon */}
            <div className="flex-shrink-0">
              {renderIcon(award)}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg mb-1">{award.display_name}</h3>
              <p className="text-sm text-gray-400 line-clamp-2">
                {award.description || 'Brak opisu'}
              </p>

              {/* Color indicator */}
              <div className="flex items-center gap-2 mt-2">
                <div
                  className="w-6 h-6 rounded border border-gray-600"
                  style={{ backgroundColor: award.color }}
                />
                <span className="text-xs text-gray-500">{award.color}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={() => onEdit(award)}
              className="flex-1 py-2 px-4 bg-gray-700 hover:bg-gray-600 rounded-lg flex items-center justify-center gap-2 transition text-sm"
            >
              <Edit2 size={16} />
              Edytuj
            </button>

            {!award.is_personal && (
              <button
                onClick={() => onDelete(award.id, award.display_name)}
                className="flex-1 py-2 px-4 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-lg flex items-center justify-center gap-2 transition text-sm text-red-400"
              >
                <Trash2 size={16} />
                Usuń
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default MobileAwardsList;
