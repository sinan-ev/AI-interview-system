import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
  bordered?: boolean;
  glow?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  children,
  hoverEffect = false,
  bordered = true,
  glow = false,
  padding = 'md',
  className = '',
  ...props
}) => {
  const paddingStyles = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={`bg-card rounded-xl ${paddingStyles[padding]} transition-all duration-200 ${
        bordered ? 'border border-border' : ''
      } ${
        hoverEffect
          ? 'hover:bg-card-hover hover:border-slate-700/80 hover:shadow-card cursor-pointer'
          : ''
      } ${glow ? 'shadow-glow border-primary/30' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
