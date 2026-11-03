import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, User, Sparkles, ArrowRight } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/auth.api';
import { useToast } from '../../components/common/Toast';
import { Button } from '../../components/common/Button';
import type { UserRole } from '../../types';

const roleOptions: { label: string; value: UserRole; description: string }[] = [
  { label: 'Candidate', value: 'candidate', description: 'Practice & prepare for interviews' },
  { label: 'Interviewer', value: 'interviewer', description: 'Conduct & review interviews' },
];

export const RegisterPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('candidate');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const { success, error } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) {
      error('Please fill in all required fields.');
      return;
    }
    if (password.length < 8) {
      error('Password must be at least 8 characters.');
      return;
    }
    setIsLoading(true);
    try {
      const tokenData = await authApi.register({ name, email, password, role });
      setAuth(tokenData);
      success(`Account created! Welcome, ${tokenData.user.name}!`);
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      const message =
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail ||
        'Registration failed. Please try again.';
      error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 -right-32 w-[600px] h-[600px] rounded-full bg-accent/5 blur-3xl" />
        <div className="absolute -bottom-32 -left-32 w-[500px] h-[500px] rounded-full bg-primary/5 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md relative"
      >
        <div className="flex items-center gap-2.5 justify-center mb-8">
          <div className="w-9 h-9 rounded-xl bg-accent/20 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-accent" />
          </div>
          <span className="text-xl font-bold text-text-primary">AI Interview</span>
        </div>

        <div className="bg-card border border-border rounded-2xl p-8 shadow-card">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-text-primary mb-1">Create account</h1>
            <p className="text-sm text-text-muted">Start your interview journey today</p>
          </div>

          <form onSubmit={handleSubmit} id="register-form" className="space-y-4">
            {/* Role Selector */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">I am a</label>
              <div className="grid grid-cols-2 gap-2">
                {roleOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    id={`role-${option.value}-btn`}
                    onClick={() => setRole(option.value)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      role === option.value
                        ? 'border-accent bg-accent/10 text-text-primary'
                        : 'border-border bg-background text-text-muted hover:border-slate-600'
                    }`}
                  >
                    <p className="text-sm font-medium">{option.label}</p>
                    <p className="text-xs mt-0.5 opacity-70">{option.description}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Name */}
            <div>
              <label htmlFor="register-name" className="block text-sm font-medium text-text-secondary mb-1.5">
                Full name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  id="register-name"
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Alex Johnson"
                  disabled={isLoading}
                  className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl pl-10 pr-4 py-2.5 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all disabled:opacity-50"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label htmlFor="register-email" className="block text-sm font-medium text-text-secondary mb-1.5">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  id="register-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  disabled={isLoading}
                  className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl pl-10 pr-4 py-2.5 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all disabled:opacity-50"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="register-password" className="block text-sm font-medium text-text-secondary mb-1.5">
                Password <span className="text-text-muted font-normal">(min 8 chars)</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  id="register-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={isLoading}
                  className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl pl-10 pr-10 py-2.5 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all disabled:opacity-50"
                />
                <button
                  type="button"
                  id="toggle-register-password-visibility"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              id="register-submit-btn"
              isLoading={isLoading}
              className="w-full mt-2"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Create account
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-text-muted">
            Already have an account?{' '}
            <Link to="/auth/login" className="text-accent hover:text-accent/80 font-medium transition-colors">
              Sign in
            </Link>
          </p>
        </div>

        <p className="text-center text-xs text-text-muted mt-4">
          Practice smarter. Interview better.
        </p>
      </motion.div>
    </div>
  );
};
