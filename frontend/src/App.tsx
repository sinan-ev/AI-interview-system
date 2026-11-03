import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from './components/common/Toast';
import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute, GuestRoute } from './components/layout/RouteGuards';
import { useAuthStore } from './store/authStore';

// Pages
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { NewInterviewPage } from './pages/interviews/NewInterviewPage';
import { InterviewRoomPage } from './pages/interviews/InterviewRoomPage';
import { InterviewDetailPage } from './pages/interviews/InterviewDetailPage';
import { InterviewListPage } from './pages/interviews/InterviewListPage';
import { DocumentsPage } from './pages/documents/DocumentsPage';
import { AnalyticsPage } from './pages/analytics/AnalyticsPage';
import { LearnPage } from './pages/learn/LearnPage';
import { ProfilePage } from './pages/profile/ProfilePage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  const { initializeAuth } = useAuthStore();

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* Guest / Public Auth Routes */}
            <Route element={<GuestRoute />}>
              <Route path="/auth/login" element={<LoginPage />} />
              <Route path="/auth/register" element={<RegisterPage />} />
            </Route>

            {/* Protected Routes */}
            <Route element={<ProtectedRoute />}>
              {/* Interview Room (Dedicated immersion experience) */}
              <Route
                path="/interviews/:id/room"
                element={
                  <div className="min-h-screen bg-background p-4 md:p-8">
                    <InterviewRoomPage />
                  </div>
                }
              />

              {/* Standard App Layout Pages */}
              <Route
                element={
                  <AppLayout>
                    <Routes>
                      <Route path="/dashboard" element={<DashboardPage />} />
                      <Route path="/interviews" element={<InterviewListPage />} />
                      <Route path="/interviews/new" element={<NewInterviewPage />} />
                      <Route path="/interviews/:id" element={<InterviewDetailPage />} />
                      <Route path="/documents" element={<DocumentsPage />} />
                      <Route path="/analytics" element={<AnalyticsPage />} />
                      <Route path="/learn" element={<LearnPage />} />
                      <Route path="/profile" element={<ProfilePage />} />
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                      <Route path="*" element={<Navigate to="/dashboard" replace />} />
                    </Routes>
                  </AppLayout>
                }
                path="/*"
              />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
};
