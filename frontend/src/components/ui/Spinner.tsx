import { Loader2 } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export default function Spinner({ size = 'md', className }: SpinnerProps) {
  const sizes = {
    sm: 16,
    md: 24,
    lg: 32,
    xl: 48,
  };

  return (
    <Loader2 
      size={sizes[size]} 
      className={twMerge("animate-spin text-accent-green", className)} 
    />
  );
}
