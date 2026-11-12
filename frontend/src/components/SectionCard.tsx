import { ReactNode } from 'react';

interface SectionCardProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export default function SectionCard({ title, children, className = '' }: SectionCardProps) {
  return (
    <div className={`section-card ${className}`}>
      {title && <h3 className="section-card-title">{title}</h3>}
      {children}
    </div>
  );
}
