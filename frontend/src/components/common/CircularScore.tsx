import React from 'react';

export interface CircularScoreProps {
  score: number; // 0 to 100
  size?: number; // diameter in px
  strokeWidth?: number;
  label?: string;
  className?: string;
}

export const CircularScore: React.FC<CircularScoreProps> = ({
  score,
  size = 120,
  strokeWidth = 10,
  label,
  className = '',
}) => {
  const normalizedScore = Math.min(Math.max(score, 0), 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  let strokeColor = '#EF4444'; // Red
  if (normalizedScore >= 75) {
    strokeColor = '#22C55E'; // Green
  } else if (normalizedScore >= 60) {
    strokeColor = '#F59E0B'; // Amber
  }

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div className="relative inline-flex items-center justify-center">
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#1E293B"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-2xl font-bold tracking-tight text-text-primary">
            {Math.round(normalizedScore)}
          </span>
          <span className="text-[10px] font-medium text-text-muted uppercase tracking-wider">
            / 100
          </span>
        </div>
      </div>
      {label && (
        <span className="mt-2 text-xs font-medium text-text-secondary">{label}</span>
      )}
    </div>
  );
};
