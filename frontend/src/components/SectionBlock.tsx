import { ReactNode } from 'react';

interface SectionBlockProps {
  title?: string;
  children: ReactNode;
  className?: string;
  subtitle?: string;
}

export default function SectionBlock({
  title,
  children,
  className = '',
  subtitle,
}: SectionBlockProps) {
  return (
    <div className={`section ${className}`}>
      {title || subtitle && (
        <div className="section-header">
          {title && <h2 className="section-title">{title}</h2>}
          {subtitle && <p className="section-subtitle">{subtitle}</p>}
        </div>
      )}
      <div className="card">{children}</div>
    </div>
  );
}
