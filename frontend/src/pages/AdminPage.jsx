import { useState, useEffect } from 'react'
import { Users, Award, BarChart3 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { Navigate } from 'react-router-dom'
import api from '../services/api'

function AdminPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('users')

  // Check admin permission
  if (!user?.award_scopes?.includes('admin')) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Admin Panel</h1>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-gray-700">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 flex items-center gap-2 ${
            activeTab === 'users' ? 'border-b-2 border-blue-500 text-white' : 'text-gray-400'
          }`}
        >
          <Users size={20} />
          Users
        </button>
        <button
          onClick={() => setActiveTab('award-types')}
          className={`px-4 py-2 flex items-center gap-2 ${
            activeTab === 'award-types' ? 'border-b-2 border-blue-500 text-white' : 'text-gray-400'
          }`}
        >
          <Award size={20} />
          Award Types
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          className={`px-4 py-2 flex items-center gap-2 ${
            activeTab === 'stats' ? 'border-b-2 border-blue-500 text-white' : 'text-gray-400'
          }`}
        >
          <BarChart3 size={20} />
          Stats
        </button>
      </div>

      {/* Content */}
      <div>
        {activeTab === 'users' && <p className="text-gray-400">User management - TODO</p>}
        {activeTab === 'award-types' && <p className="text-gray-400">Award types management - TODO</p>}
        {activeTab === 'stats' && <p className="text-gray-400">Statistics - TODO</p>}
      </div>
    </div>
  )
}

export default AdminPage
