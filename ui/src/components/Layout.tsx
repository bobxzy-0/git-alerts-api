import React from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/i18n/LanguageContext';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { locale, setLocale } = useLanguage();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6 min-w-0">
              <Link to="/" className="text-2xl font-bold text-primary">
                GitAlerts
              </Link>
              <nav className="flex flex-wrap items-center gap-x-4 gap-y-2">
                <Link
                  to="/dashboard"
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  to="/scans"
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  Scans
                </Link>
                <Link
                  to="/findings"
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  Findings
                </Link>
                <Link
                  to="/notifications"
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  Notifications
                </Link>
                <Link
                  to="/integrations"
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  Integrations
                </Link>
                <Link
                  to="/settings"
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  Settings
                </Link>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <select
                aria-label="Language"
                value={locale}
                onChange={(event) => setLocale(event.target.value === 'zh-CN' ? 'zh-CN' : 'en')}
                className="rounded-md border border-input bg-background px-2 py-1 text-sm text-foreground"
              >
                <option value="zh-CN">简体中文</option>
                <option value="en">English</option>
              </select>
              {user && (
                <>
                  <span className="text-sm text-muted-foreground">{user.username}</span>
                  <button
                    onClick={handleLogout}
                    className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                  >
                    Logout
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
};
