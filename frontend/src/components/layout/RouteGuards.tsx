import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Spinner } from '../common/Spinner';

/**
 * Wraps protected routes. Redirects to login if not authenticated.
 */
export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Spinner size="lg" label="Loading session..." />
      </div>
    );
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/auth/login" replace />;
};

/**
 * Redirects already-authenticated users away from auth pages.
 */
export const GuestRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Spinner size="lg" />
      </div>
    );
  }

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Outlet />;
};
