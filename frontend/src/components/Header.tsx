import React, { useEffect, useRef } from "react";
import { BrandLogo } from "./BrandLogo";
import { UserLocationPicker } from "./UserLocationPicker";
import type { LocationItem } from "../types";

export type PageTab =
  | "tong-quan"
  | "so-sanh"
  | "lich-su"
  | "tu-van";

interface HeaderProps {
  currentPage: PageTab;
  onSelectPage: (page: PageTab) => void;
  userLocation: LocationItem;
  isDetectingUserLocation: boolean;
  userLocationError: string | null;
  onSelectUserLocation: (location: LocationItem) => void;
  onDetectUserLocation: () => Promise<void>;
}

const TABS: { key: PageTab; label: string }[] = [
  { key: "tong-quan", label: "Tổng quan" },
  { key: "so-sanh", label: "So sánh" },
  { key: "lich-su", label: "Lịch sử" },
  { key: "tu-van", label: "Tư vấn" },
];

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  onSelectPage,
  userLocation,
  isDetectingUserLocation,
  userLocationError,
  onSelectUserLocation,
  onDetectUserLocation,
}) => {
  const activeTabRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    activeTabRef.current?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [currentPage]);

  return (
    <header className="flex items-center gap-[18px] flex-wrap justify-between">
      <div className="flex items-center gap-[14px] flex-wrap min-w-0 max-w-full">
        {/* Pill Logo */}
        <BrandLogo />

        {/* Pill Tabs */}
        <nav className="bg-card rounded-full p-[5px] shadow-sh1 flex items-center gap-[3px] max-w-full overflow-x-auto">
          {TABS.map((tab) => {
            const isActive = currentPage === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                ref={isActive ? activeTabRef : null}
                aria-current={isActive ? "page" : undefined}
                onClick={() => onSelectPage(tab.key)}
                className={`shrink-0 whitespace-nowrap px-[17px] py-[8px] !text-[13.5px] rounded-full transition-all duration-150 select-none cursor-pointer focus-ring ${
                  isActive
                    ? "bg-acc-soft text-acc font-semibold"
                    : "text-m1 hover:text-ink"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="ml-auto flex flex-wrap items-center justify-end gap-[10px]">
        <UserLocationPicker
          userLocation={userLocation}
          isDetecting={isDetectingUserLocation}
          errorMessage={userLocationError}
          onSelect={onSelectUserLocation}
          onDetect={onDetectUserLocation}
        />
      </div>
    </header>
  );
};
