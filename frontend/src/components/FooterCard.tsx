import type { ReactNode } from 'react';

interface FooterCardProps {
  title: string;
  children: ReactNode;
}

export function FooterCard({ title, children }: FooterCardProps) {
  return (
    <section aria-label={title} className="rounded-[20px] border border-border bg-card p-5 sm:p-6">
      <h2 className="font-nunito text-[15.5px] font-bold">{title}</h2>
      {children}
    </section>
  );
}

export function SourceLink({ href, label }: { href: string; label: string }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="focus-ring underline hover:text-acc">
      {label}
    </a>
  );
}

export const ERA5_URL = 'https://open-meteo.com/en/docs/historical-weather-api';
