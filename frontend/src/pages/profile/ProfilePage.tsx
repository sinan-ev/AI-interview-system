import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  User,
  Mail,
  Shield,
  Calendar,
  Save,
  LogOut,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { PageLoading } from '../../components/common/Spinner';
import { useToast } from '../../components/common/Toast';
import { usersApi } from '../../api/users.api';
import { useAuthStore } from '../../store/authStore';
import { useNavigate } from 'react-router-dom';

export const ProfilePage: React.FC = () => {
  const { user: authUser, setUser, logout } = useAuthStore();
  const { success, error } = useToast();
  const navigate = useNavigate();

  const [name, setName] = useState(authUser?.name ?? '');
  const [email, setEmail] = useState(authUser?.email ?? '');

  const { data: profile, isLoading } = useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const res = await usersApi.getProfile();
      setName(res.name);
      setEmail(res.email);
      setUser(res);
      return res;
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => usersApi.updateProfile({ name, email }),
    onSuccess: (updated) => {
      setUser(updated);
      success('Profile updated successfully.');
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.error?.message || 'Failed to update profile.';
      error(msg);
    },
  });

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  if (isLoading && !authUser) {
    return <PageLoading label="Loading user profile..." />;
  }

  const currentUser = profile ?? authUser;

  return (
    <div className="max-w-2xl mx-auto space-y-6 pb-16">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Account Profile</h1>
        <p className="text-sm text-text-muted mt-0.5">
          Manage your personal details and authentication settings.
        </p>
      </div>

      <Card padding="lg" className="space-y-6">
        <div className="flex items-center gap-4 border-b border-border pb-6">
          <div className="w-14 h-14 rounded-2xl bg-accent/20 flex items-center justify-center text-accent text-xl font-bold">
            {currentUser?.name?.charAt(0).toUpperCase() ?? 'U'}
          </div>
          <div>
            <h2 className="text-lg font-bold text-text-primary">{currentUser?.name}</h2>
            <p className="text-xs text-text-muted">{currentUser?.email}</p>
            <div className="flex items-center gap-2 mt-1.5">
              <Badge variant="accent" size="sm">
                {currentUser?.role ?? 'candidate'}
              </Badge>
              <Badge variant="success" size="sm">
                Active Account
              </Badge>
            </div>
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            updateMutation.mutate();
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl pl-9 pr-4 py-2 text-sm outline-none focus:border-accent"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl pl-9 pr-4 py-2 text-sm outline-none focus:border-accent"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              onClick={handleLogout}
              className="text-error border-error/30 hover:bg-error/10"
              leftIcon={<LogOut className="w-4 h-4" />}
            >
              Sign Out
            </Button>

            <Button
              type="submit"
              isLoading={updateMutation.isPending}
              leftIcon={<Save className="w-4 h-4" />}
            >
              Save Changes
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
