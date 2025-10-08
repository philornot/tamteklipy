import { useState, useEffect } from 'react'
import { TrendingUp, Users, Award, Film, AlertCircle, Loader } from 'lucide-react'
import api from '../services/api'
import { useAuth } from '../hooks/useAuth'
import usePageTitle from "../hooks/usePageTitle.js";

function StatsPage() {
  usePageTitle("Statystyki");
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await api.get('/awards/stats')
      setStats(response.data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
        <Loader className="animate-spin text-blue-500" size={48} />
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-8 text-red-400 flex items-center justify-center gap-2">
          <AlertCircle size={20} />
          Błąd ładowania statystyk
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Statystyki</h1>
        <p className="text-gray-400">
          Podsumowanie aktywności w TamteKlipy
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center gap-3">
            <Award className="text-yellow-500" size={32} />
            <div>
              <p className="text-gray-400 text-sm">Wszystkie nagrody</p>
              <p className="text-2xl font-bold">{stats.total_awards}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center gap-3">
            <Users className="text-blue-500" size={32} />
            <div>
              <p className="text-gray-400 text-sm">Aktywni użytkownicy</p>
              <p className="text-2xl font-bold">{stats.most_active_users?.length || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center gap-3">
            <Film className="text-green-500" size={32} />
            <div>
              <p className="text-gray-400 text-sm">Nagrodzonych klipów</p>
              <p className="text-2xl font-bold">{stats.top_clips_by_awards?.length || 0}</p>
            </div>
          </div>
        </div>

        {user && (
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-3">
              <TrendingUp className="text-purple-500" size={32} />
              <div>
                <p className="text-gray-400 text-sm">Moje nagrody</p>
                <p className="text-2xl font-bold">
                  {Object.values(stats.current_user_breakdown || {}).reduce((a, b) => a + b, 0)}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Most Popular Award */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
        <h3 className="text-lg font-semibold mb-4">Najpopularniejsza nagroda</h3>
        {stats.most_popular_award?.award_name ? (
          <div className="flex items-center gap-4">
            <span className="text-4xl">{stats.most_popular_award.icon}</span>
            <div>
              <p className="font-semibold">{stats.most_popular_award.display_name}</p>
              <p className="text-gray-400">{stats.most_popular_award.count} przyznań</p>
            </div>
          </div>
        ) : (
          <p className="text-gray-400">Brak danych - nie przyznano jeszcze żadnych nagród</p>
        )}
      </div>

      {/* Most Active Users */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
        <h3 className="text-lg font-semibold mb-4">Najbardziej aktywni użytkownicy</h3>
        {stats.most_active_users && stats.most_active_users.length > 0 ? (
          <div className="space-y-3">
            {stats.most_active_users.map((user, idx) => (
              <div key={user.user_id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-gray-500 w-6">#{idx + 1}</span>
                  <span className="font-medium">{user.username}</span>
                </div>
                <span className="text-gray-400">{user.awards_given} nagród</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-4">
            Brak aktywnych użytkowników
          </p>
        )}
      </div>

      {/* Top Clips */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">Top klipy według nagród</h3>
        {stats.top_clips_by_awards && stats.top_clips_by_awards.length > 0 ? (
          <div className="space-y-3">
            {stats.top_clips_by_awards.map((clip, idx) => (
              <div key={clip.clip_id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-gray-500 w-6">#{idx + 1}</span>
                  <div>
                    <p className="font-medium truncate max-w-md">{clip.filename}</p>
                    <p className="text-sm text-gray-400">by {clip.uploader_username}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Award size={16} className="text-yellow-500" />
                  <span>{clip.award_count}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-4">
            Brak nagrodzonych klipów
          </p>
        )}
      </div>
    </div>
  )
}

export default StatsPage;
