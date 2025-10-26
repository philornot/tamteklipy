import { Award, Home, User, Shield } from 'lucide-react';

/**
 * Mobile Bottom Navigation Bar
 *
 * Wyświetlany tylko na mobile (<768px)
 * 3 ikony dla zwykłych userów: Awards, Home, Profile
 * 4 ikony dla adminów: +Admin (Shield)
 *
 * Props:
 * - currentPath: string - aktualny pathname
 * - onNavigate: (path: string) => void - callback do nawigacji
 * - user: object - obiekt użytkownika
 */
function MobileNavBar({ currentPath = '/', onNavigate = () => {}, user = null }) {
  const isActive = (path) => currentPath === path;

  const navItems = [
    {
      path: '/awards',
      icon: Award,
      label: 'Awards',
      show: true
    },
    {
      path: '/',
      icon: Home,
      label: 'Home',
      show: true
    },
    {
      path: '/profile',
      icon: User,
      label: 'Profile',
      show: true
    },
    {
      path: '/admin',
      icon: Shield,
      label: 'Admin',
      show: user?.is_admin
    }
  ].filter(item => item.show);

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 md:hidden">
      {/* Safe area spacer dla iOS notch */}
      <div
        className="bg-gray-900/95 backdrop-blur-xl border-t border-gray-800"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      >
        <div className="flex items-center justify-around px-4 py-3">
          {navItems.map(({ path, icon: Icon, label }) => {
            const active = isActive(path);

            return (
              <button
                key={path}
                onClick={() => onNavigate(path)}
                className={`flex flex-col items-center justify-center transition-all duration-300 min-w-[60px] ${
                  active ? 'scale-110' : 'scale-100'
                }`}
                aria-label={label}
              >
                {/* Icon Container */}
                <div className={`relative p-3 rounded-2xl transition-all duration-300 ${
                  active 
                    ? 'bg-gradient-to-br from-purple-500 to-fuchsia-500 shadow-glow'
                    : 'bg-transparent'
                }`}>
                  <Icon
                    size={24}
                    className={`transition-colors duration-300 ${
                      active ? 'text-white' : 'text-gray-400'
                    }`}
                    strokeWidth={active ? 2.5 : 2}
                  />

                  {/* Active indicator dot */}
                  {active && (
                    <div className="absolute -top-1 -right-1 w-2 h-2 bg-white rounded-full animate-pulse" />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

export default MobileNavBar;