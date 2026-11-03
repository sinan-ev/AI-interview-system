import React from 'react';

export interface ProgressBarProps {
  value: number; // 0 to 100
  max?: number;
  label?: string;
  showPercentage?: boolean;
  color?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'gradient';
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'gradient';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  showPercentage = true,
  color,
  variant,
  size = 'md',
  className = '',
}) => {
  const activeColor = variant || color || 'primary';
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const colorStyles = {
    primary: 'bg-primary',
    secondary: 'bg-secondary',
    accent: 'bg-accent',
    success: 'bg-success',
    warning: 'bg-warning',
    error: 'bg-error',
    gradient: 'bg-gradient-to-r from-primary via-secondary to-accent',
  };

  const sizeStyles = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={`w-full ${className}`}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-1.5 text-xs font-medium">
          {label && <span className="text-text-secondary">{label}</span>}
          {showPercentage && (
            <span className="text-text-primary ml-auto font-semibold">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <div
        className={`w-full bg-slate-800 rounded-full overflow-hidden ${sizeStyles[size]}`}
      >
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${colorStyles[activeColor]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
