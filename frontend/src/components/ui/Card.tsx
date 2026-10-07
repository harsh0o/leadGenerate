"use client";

import { motion, HTMLMotionProps } from 'framer-motion';
import { twMerge } from 'tailwind-merge';
import React from 'react';

interface CardProps extends HTMLMotionProps<"div"> {
  header?: React.ReactNode;
  footer?: React.ReactNode;
  hoverEffect?: boolean;
}

export default function Card({ className, header, footer, children, hoverEffect = false, ...props }: CardProps) {
  const noPad = className?.includes('p-0');
  return (
    <motion.div
      whileHover={hoverEffect ? { y: -2, transition: { duration: 0.2 } } : {}}
      className={twMerge("bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-sm", className)}
      {...props}
    >
      {header && <div className="px-6 py-4 border-b border-gray-800">{header as React.ReactNode}</div>}
      <div className={noPad ? "" : "p-6"}>{children as React.ReactNode}</div>
      {footer && <div className="px-6 py-4 border-t border-gray-800 bg-gray-900/50">{footer as React.ReactNode}</div>}
    </motion.div>
  );
}
