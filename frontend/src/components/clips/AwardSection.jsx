import {useEffect, useState} from "react";
import {Award, Loader, Trash2} from "lucide-react";
import {useAuth} from "../../hooks/useAuth";
import api, {getBaseURL} from "../../services/api";

function AwardSection({clipId, initialAwards}) {
    const [awards, setAwards] = useState(initialAwards || []);
    const [myAwards, setMyAwards] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const {user} = useAuth();

    useEffect(() => {
        fetchMyAwards();
    }, []);

    const fetchMyAwards = async () => {
        try {
            const response = await api.get("/awards/my-awards");
            setMyAwards(response.data.available_awards);
        } catch (err) {
            console.error("Failed to fetch my awards:", err);
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

            // Optimistic UI update
            setAwards([...awards, response.data]);
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

            // Optimistic UI update
            setAwards(awards.filter((a) => a.id !== awardId));
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

    // Group awards by type
    //   const awardCounts = awards.reduce((acc, award) => {
    //     acc[award.award_name] = (acc[award.award_name] || 0) + 1;
    //     return acc;
    //   }, {});

    // Był error: awardCounts' is assigned a value but never used. Allowed unused vars must match

    return (<div className="space-y-6">
        {/* My Available Awards */}
        <div>
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Award size={20} className="text-yellow-500"/>
                Przyznaj nagrodę
            </h3>

            {error && (<div className="bg-red-900/50 border border-red-700 text-red-200 px-3 py-2 rounded text-sm mb-3">
                {error}
            </div>)}

            <div className="space-y-2">
                {myAwards.length === 0 ? (<p className="text-gray-400 text-sm">Nie masz dostępnych
                    nagród</p>) : (myAwards.map((award) => {
                    const alreadyGiven = hasGivenAward(award.award_name)
                    return (<button
                        key={award.award_name}
                        onClick={() => !alreadyGiven && handleGiveAward(award.award_name)}
                        disabled={loading || alreadyGiven}
                        className={`w-full p-3 rounded-lg border transition flex items-center gap-3 ${alreadyGiven ? 'bg-gray-700/50 border-gray-600 cursor-not-allowed opacity-50' : 'bg-gray-700 border-gray-600 hover:bg-gray-600 hover:border-blue-500'}`}
                    >
                        {/* Icon: image or emoji fallback */}
                        {award.icon_url ? (<img
                            src={`${getBaseURL()}${award.icon_url}`}
                            alt={award.display_name}
                            className="w-8 h-8 rounded"
                            onError={(e) => {
                                // Fallback to emoji on error
                                e.target.style.display = 'none'
                                e.target.nextSibling.style.display = 'block'
                            }}
                        />) : null}
                        <span className={`text-2xl ${award.icon_url ? 'hidden' : ''}`}>
                            {award.icon}
                        </span>

                        <div className="flex-1 text-left">
                            <div className="font-semibold">{award.display_name}</div>
                            <div className="text-xs text-gray-400">{award.description}</div>
                        </div>
                        {loading && !alreadyGiven && <Loader className="animate-spin" size={16}/>}
                        {alreadyGiven && <span className="text-green-500 text-sm">✓ Przyznano</span>}
                    </button>)
                }))}
            </div>
        </div>

        {/* Awarded List */}
        <div>
            <h3 className="text-lg font-semibold mb-3">
                Nagrody ({awards.length})
            </h3>

            {awards.length === 0 ? (<p className="text-gray-400 text-sm">Brak nagród</p>) : (<div className="space-y-2">
                {awards.map((award) => (<div
                    key={award.id}
                    className="flex items-center justify-between p-3 bg-gray-700 rounded-lg border border-gray-600"
                >
                    <div className="flex items-center gap-3 flex-1">
                  <span className="text-2xl">
                    {myAwards.find((a) => a.award_name === award.award_name)?.icon || "🏆"}
                  </span>
                        <div>
                            <div className="text-sm font-medium">{award.username}</div>
                            <div className="text-xs text-gray-400">
                                {new Date(award.awarded_at).toLocaleString("pl-PL")}
                            </div>
                        </div>
                    </div>

                    {canRemoveAward(award) && (<button
                        onClick={() => handleRemoveAward(award.id)}
                        disabled={loading}
                        className="p-2 text-red-400 hover:text-red-300 hover:bg-gray-600 rounded transition"
                        title="Usuń nagrodę"
                    >
                        <Trash2 size={16}/>
                    </button>)}
                </div>))}
            </div>)}
        </div>
    </div>);
}

export default AwardSection;
