import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'neutral' | 'default';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}) => {
  const variantStyles = {
    primary: 'bg-primary/10 text-primary-light border-primary/20',
    secondary: 'bg-secondary/10 text-secondary-light border-secondary/20',
    accent: 'bg-accent/10 text-accent-light border-accent/20',
    success: 'bg-success/10 text-success-light border-success/20',
    warning: 'bg-warning/10 text-warning-light border-warning/20',
    error: 'bg-error/10 text-error-light border-error/20',
    neutral: 'bg-slate-800 text-text-secondary border-slate-700',
    default: 'bg-slate-800 text-text-secondary border-slate-700',
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5 rounded',
    md: 'text-xs font-medium px-2.5 py-1 rounded-full',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 border font-medium ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};
