"use client";

import { motion, HTMLMotionProps } from 'framer-motion';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Loader2 } from 'lucide-react';
import React from 'react';

interface ButtonProps extends HTMLMotionProps<"button"> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({
  className, variant = 'primary', size = 'md', isLoading, children, asChild, ...props
}, ref) => {
  const baseClasses = "inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible:outline-none disabled:opacity-50 disabled:pointer-events-none";
  
  const variants = {
    primary: "bg-accent-green text-gray-950 hover:bg-emerald-400",
    secondary: "bg-gray-800 text-white hover:bg-gray-700 border border-gray-700",
    ghost: "hover:bg-gray-800 text-gray-300 hover:text-white",
    danger: "bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20",
  };

  const sizes = {
    sm: "h-9 px-3 text-sm",
    md: "h-10 px-4 py-2",
    lg: "h-11 px-8 text-lg",
  };

  if (asChild) {
    // Render child (expected <a>/<Link>) with button styling via cloneElement
    // so styles land on the interactive element (no span>a nesting).
    const child = React.Children.only(children) as React.ReactElement<{ className?: string }>;
    return React.cloneElement(child, {
      className: twMerge(baseClasses, variants[variant], sizes[size], className, (child.props as { className?: string }).className),
    });
  }

  return (
    <motion.button
      ref={ref as React.Ref<HTMLButtonElement>}
      type={(props as { type?: "button" | "submit" | "reset" }).type ?? "button"}
      whileTap={{ scale: 0.98 }}
      whileHover={{ scale: 1.02 }}
      className={twMerge(baseClasses, variants[variant], sizes[size], className)}
      disabled={isLoading || (props as any).disabled}
      {...props}
    >
      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {children as React.ReactNode}
    </motion.button>
  );
});

Button.displayName = "Button";

export default Button;
