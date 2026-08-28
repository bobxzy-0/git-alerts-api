import React from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/i18n/LanguageContext';
import { useBranding } from '@/hooks/useBranding';
import { LogOut, UserRound } from 'lucide-react';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { locale, setLocale } = useLanguage();
  const branding = useBranding();

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
                {branding.brand_name}
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
            <div className="ml-4 flex shrink-0 items-center rounded-xl border bg-muted/20 p-1 shadow-sm">
              <div role="group" aria-label="Language" className="flex rounded-lg bg-muted/70 p-0.5 text-[11px] font-semibold">
                <button type="button" aria-pressed={locale === 'zh-CN'} onClick={() => setLocale('zh-CN')} className={`rounded-md px-2.5 py-1.5 transition-all ${locale === 'zh-CN' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>CN</button>
                <button type="button" aria-pressed={locale === 'en'} onClick={() => setLocale('en')} className={`rounded-md px-2.5 py-1.5 transition-all ${locale === 'en' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>EN</button>
              </div>
              {user && (
                <>
                  <div className="mx-1.5 h-6 w-px bg-border" />
                  <div className="flex min-w-0 items-center gap-2 px-1.5" title={user.username}>
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary"><UserRound className="h-4 w-4" /></span>
                    <span className="hidden max-w-28 truncate text-sm font-medium lg:block">{user.username}</span>
                  </div>
                  <button
                    onClick={handleLogout}
                    title="Logout"
                    aria-label="Logout"
                    className="ml-1 inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                  >
                    <LogOut className="h-4 w-4" />
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
