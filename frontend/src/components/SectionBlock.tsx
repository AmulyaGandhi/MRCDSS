import { ReactNode } from 'react';

interface SectionBlockProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export default function SectionBlock({ title, children, className = '' }: SectionBlockProps) {
  return (
    <div className={`section-block ${className}`}>
      {title && <h3 className="section-block-title">{title}</h3>}
      {children}
    </div>
  );
}