import React from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
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
  const navClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-3 py-2 text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6 min-w-0">
              <Link to="/" className="text-2xl font-bold text-primary">
                代码哨兵
              </Link>
              <nav className="flex flex-wrap items-center gap-1">
                <NavLink
                  to="/dashboard"
                  className={navClass}
                >
                  Dashboard
                </NavLink>
                <NavLink
                  to="/scans"
                  className={navClass}
                >
                  Scans
                </NavLink>
                <NavLink
                  to="/findings"
                  className={navClass}
                >
                  Findings
                </NavLink>
                <NavLink
                  to="/notifications"
                  className={navClass}
                >
                  Notifications
                </NavLink>
                <NavLink
                  to="/integrations"
                  className={navClass}
                >
                  Integrations
                </NavLink>
                <NavLink
                  to="/settings"
                  className={navClass}
                >
                  Settings
                </NavLink>
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
