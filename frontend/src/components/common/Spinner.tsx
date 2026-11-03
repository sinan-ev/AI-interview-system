import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  fullScreen?: boolean;
}

const sizes = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-10 h-10',
};

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  label = 'Loading...',
  fullScreen = false,
}) => {
  const spinner = (
    <div className="flex flex-col items-center gap-3" role="status" aria-label={label}>
      <Loader2 className={`${sizes[size]} text-accent animate-spin`} />
      {label && size !== 'sm' && (
        <p className="text-sm text-text-muted">{label}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="fixed inset-0 bg-background z-50 flex items-center justify-center"
      >
        {spinner}
      </motion.div>
    );
  }

  return spinner;
};

interface PageLoadingProps {
  label?: string;
}

export const PageLoading: React.FC<PageLoadingProps> = ({ label }) => (
  <div className="min-h-[60vh] flex items-center justify-center">
    <Spinner size="lg" label={label} />
  </div>
);
