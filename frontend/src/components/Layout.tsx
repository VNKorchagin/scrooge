import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

export const Layout = () => {
  const { user, logout, isAuthenticated } = useAuthStore();
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/add', label: 'Add Transaction' },
    { path: '/history', label: 'History' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <span className="text-xl font-bold text-gray-900">Scrooge</span>
            </Link>

            {/* Navigation */}
            {isAuthenticated && (
              <nav className="hidden md:flex space-x-8">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`text-sm font-medium transition-colors ${
                      location.pathname === item.path
                        ? 'text-primary-600'
                        : 'text-gray-500 hover:text-gray-900'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            )}

            {/* User Menu */}
            {isAuthenticated && (
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600 hidden sm:block">
                  {user?.username}
                </span>
                <button
                  onClick={logout}
                  className="text-sm text-gray-500 hover:text-danger-600 transition-colors"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Mobile Navigation */}
        {isAuthenticated && (
          <div className="md:hidden border-t border-gray-200">
            <div className="flex justify-around py-3">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`text-xs font-medium ${
                    location.pathname === item.path
                      ? 'text-primary-600'
                      : 'text-gray-500'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
};
