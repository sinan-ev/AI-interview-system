import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Mic,
  FileText,
  BarChart2,
  User,
  LogOut,
  ChevronRight,
  Sparkles,
  BookOpen,
  Bell,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/interviews', icon: Mic, label: 'Interviews' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/analytics', icon: BarChart2, label: 'Analytics' },
  { to: '/learn', icon: BookOpen, label: 'Learn' },
  { to: '/profile', icon: User, label: 'Profile' },
];

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : '?';

  return (
    <aside className="hidden lg:flex flex-col w-60 min-h-screen bg-card border-r border-border px-3 py-5 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-3 mb-8">
        <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-accent" />
        </div>
        <span className="font-semibold text-text-primary tracking-tight">AI Interview</span>
      </div>

      {/* Nav items */}
      <nav className="flex flex-col gap-1 flex-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            id={`nav-${label.toLowerCase()}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-accent/10 text-accent'
                  : 'text-text-muted hover:text-text-primary hover:bg-slate-800/60'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-accent' : ''}`} />
                <span>{label}</span>
                {isActive && <ChevronRight className="w-3.5 h-3.5 ml-auto text-accent/50" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="border-t border-border pt-4 mt-4">
        <div className="flex items-center gap-3 px-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center shrink-0">
            <span className="text-xs font-semibold text-accent">{initials}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">{user?.name}</p>
            <p className="text-xs text-text-muted truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          id="sidebar-logout-btn"
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-text-muted hover:text-error hover:bg-error/10 transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
};

export const TopBar: React.FC = () => {
  const location = useLocation();
  const { user } = useAuthStore();

  const currentNav = navItems.find((n) => location.pathname.startsWith(n.to));
  const pageTitle = currentNav?.label ?? 'AI Interview';

  return (
    <header className="h-14 flex items-center justify-between px-4 md:px-6 border-b border-border bg-card/80 backdrop-blur-sm shrink-0 sticky top-0 z-30">
      <h1 className="text-base font-semibold text-text-primary">{pageTitle}</h1>
      <div className="flex items-center gap-2">
        <button
          id="topbar-notifications-btn"
          aria-label="Notifications"
          className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-slate-800 transition-all"
        >
          <Bell className="w-4 h-4" />
        </button>
        <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
          <span className="text-xs font-semibold text-accent">
            {user?.name?.charAt(0).toUpperCase() ?? '?'}
          </span>
        </div>
      </div>
    </header>
  );
};

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />
        <AnimatePresence mode="wait">
          <motion.main
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.18 }}
            className="flex-1 p-4 md:p-6 overflow-auto"
          >
            {children}
          </motion.main>
        </AnimatePresence>
      </div>
    </div>
  );
};
