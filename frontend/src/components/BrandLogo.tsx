import React from "react";
import { Link } from "react-router-dom";

export const BrandLogo: React.FC = () => {
  return (
    <Link
      to="/"
      aria-label="Nắng Mưa - về trang chủ"
      className="bg-card rounded-full py-2.25 pr-[18px] pl-[14px] shadow-sh1 flex items-center gap-[8px] select-none focus-ring transition-opacity hover:opacity-80"
    >
      <span className="w-[9px] h-[9px] rounded-full bg-acc inline-block" />
      <span className="font-nunito font-bold text-[15.5px] text-ink tracking-tight">
        Nắng Mưa
      </span>
    </Link>
  );
};
