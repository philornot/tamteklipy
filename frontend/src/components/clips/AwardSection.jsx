import { useEffect, useState } from "react";
import { Award, Loader, Trash2 } from "lucide-react";
import * as LucideIcons from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import api from "../../services/api";
import { getBaseUrl } from "../../utils/urlHelper";

function AwardSection({ clipId, initialAwards, onAwardsChange }) {
  const [awards, setAwards] = useState(initialAwards || []);
  const [myAwards, setMyAwards] = useState([]);
  const [awardTypesMap, setAwardTypesMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchMyAwards();
    fetchAwardTypes();
  }, []);

  const fetchMyAwards = async () => {
    try {
      const response = await api.get("/awards/my-awards");
      setMyAwards(response.data.available_awards);
    } catch (err) {
      console.error("Failed to fetch my awards:", err);
    }
  };

  const fetchAwardTypes = async () => {
    try {
      const response = await api.get("/admin/award-types/detailed");
      const typesMap = {};
      response.data.forEach(type => {
        typesMap[type.name] = type;
      });
      setAwardTypesMap(typesMap);
    } catch (err) {
      console.error("Failed to fetch award types:", err);
    }
  };

  const handleGiveAward = async (awardName) => {
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/awards/clips/${clipId}`, {
        award_name: awardName,
      });

      const newAwards = [...awards, response.data];
      setAwards(newAwards);
      
      // Notify parent about change
      if (onAwardsChange) {
        onAwardsChange(newAwards);
      }
    } catch (err) {
      console.error("Failed to give award:", err);
      setError(err.response?.data?.message || "Nie udało się przyznać nagrody");
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveAward = async (awardId) => {
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      await api.delete(`/awards/clips/${clipId}/awards/${awardId}`);

      const newAwards = awards.filter((a) => a.id !== awardId);
      setAwards(newAwards);
      
      // Notify parent about change
      if (onAwardsChange) {
        onAwardsChange(newAwards);
      }
    } catch (err) {
      console.error("Failed to remove award:", err);
      setError("Nie udało się usunąć nagrody");
    } finally {
      setLoading(false);
    }
  };

  const canRemoveAward = (award) => {
    return award.user_id === user?.id;
  };

  const hasGivenAward = (awardName) => {
    return awards.some((a) => a.award_name === awardName && a.user_id === user?.id);
  };

  const renderAwardIcon = (award, size = "8") => {
    const awardType = awardTypesMap[award.award_name];
    if (!awardType) return <span className={`text-${size === "8" ? "2xl" : "xl"}`}>🏆</span>;

    // Custom icon
    if (awardType.icon_type === "custom" && awardType.custom_icon_url) {
      return (
        <img
          src={`${getBaseUrl()}${awardType.custom_icon_url}`}
          alt={awardType.display_name}
          className={`w-${size} h-${size} rounded`}
          onError={(e) => {
            e.target.style.display = 'none';
            e.target.nextSibling.style.display = 'block';
          }}
        />
      );
    }
    
    // Lucide icon
    if (awardType.icon_type === "lucide" && awardType.lucide_icon) {
      const componentName = awardType.lucide_icon
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join("");
      const IconComponent = LucideIcons[componentName];
      
      if (IconComponent) {
        return <IconComponent size={size === "8" ? 32 : 24} />;
      }
    }
    
    // Emoji fallback
    return <span className={`text-${size === "8" ? "2xl" : "xl"}`}>{awardType.icon}</span>;
  };

  return (
    <div className="space-y-6">
      {/* My Available Awards */}
      <div>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Award size={20} className="text-yellow-500" />
          Przyznaj nagrodę
        </h3>

        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-200 px-3 py-2 rounded text-sm mb-3">
            {error}
          </div>
        )}

        <div className="space-y-2">
          {myAwards.length === 0 ? (
            <p className="text-gray-400 text-sm">Nie masz dostępnych nagród</p>
          ) : (
            myAwards.map((award) => {
              const alreadyGiven = hasGivenAward(award.award_name);
              const awardType = awardTypesMap[award.award_name];
              
              return (
                <button
                  key={award.award_name}
                  onClick={() => !alreadyGiven && handleGiveAward(award.award_name)}
                  disabled={loading || alreadyGiven}
                  className={`w-full p-3 rounded-lg border transition flex items-center gap-3 ${
                    alreadyGiven
                      ? "bg-gray-700/50 border-gray-600 cursor-not-allowed opacity-50"
                      : "bg-gray-700 border-gray-600 hover:bg-gray-600 hover:border-blue-500"
                  }`}
                >
                  {/* Icon with proper rendering */}
                  <div className="flex-shrink-0">
                    {awardType && renderAwardIcon({ award_name: award.award_name }, "8")}
                    {!awardType && <span className="text-2xl">{award.icon}</span>}
                  </div>

                  <div className="flex-1 text-left">
                    <div className="font-semibold">{award.display_name}</div>
                    <div className="text-xs text-gray-400">{award.description}</div>
                  </div>
                  
                  {loading && !alreadyGiven && <Loader className="animate-spin" size={16} />}
                  {alreadyGiven && <span className="text-green-500 text-sm">✓ Przyznano</span>}
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Awarded List */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Nagrody ({awards.length})</h3>

        {awards.length === 0 ? (
          <p className="text-gray-400 text-sm">Brak nagród</p>
        ) : (
          <div className="space-y-2">
            {awards.map((award) => (
              <div
                key={award.id}
                className="flex items-center justify-between p-3 bg-gray-700 rounded-lg border border-gray-600"
              >
                <div className="flex items-center gap-3 flex-1">
                  <div className="flex-shrink-0">
                    {renderAwardIcon(award, "6")}
                  </div>
                  <div>
                    <div className="text-sm font-medium">
                      {award.award_display_name || award.award_name}
                    </div>
                    <div className="text-xs text-gray-400">
                      od {award.username} • {new Date(award.awarded_at).toLocaleString("pl-PL")}
                    </div>
                  </div>
                </div>

                {canRemoveAward(award) && (
                  <button
                    onClick={() => handleRemoveAward(award.id)}
                    disabled={loading}
                    className="p-2 text-red-400 hover:text-red-300 hover:bg-gray-600 rounded transition"
                    title="Usuń nagrodę"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default AwardSection;
