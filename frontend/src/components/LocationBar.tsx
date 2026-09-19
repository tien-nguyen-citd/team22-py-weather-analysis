import React, { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Star } from "lucide-react";
import { fetchCurrentTemperatures } from "../api/weatherApi";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useLocations, usePinnedLocations } from "../hooks/useLocations";
import { buildLocationChips } from "../lib/locationChips";
import type { LocationItem } from "../types";

interface LocationBarProps {
  currentLocation: LocationItem;
  locations: LocationItem[];
  currentTemperature?: number;
  onSelectLocation: (location: LocationItem) => void;
  favorites: string[]; // array of slugs
  onToggleFavorite: (slug: string) => void;
}

export const LocationBar: React.FC<LocationBarProps> = ({
  currentLocation,
  locations,
  currentTemperature,
  onSelectLocation,
  favorites,
  onToggleFavorite,
}) => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const scrollContentRef = useRef<HTMLDivElement>(null);
  const chipRefs = useRef(new Map<string, HTMLButtonElement>());
  const pendingSavedSlugRef = useRef<string | null>(null);
  const previousCurrentSlugRef = useRef<string | null>(null);
  const [scrollEdges, setScrollEdges] = useState({ left: false, right: false });

  const debouncedQuery = useDebouncedValue(query, 250);
  const { data: filteredLocations = [], isFetching } = useLocations(
    debouncedQuery.trim(),
  );
  const { data: pinnedLocations = [] } = usePinnedLocations();

  const { data: temperatures } = useQuery({
    queryKey: ["location-temperatures", locations],
    queryFn: ({ signal }) => fetchCurrentTemperatures(signal),
    enabled: isOpen,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const { locations: chips, suggestedStart } = useMemo(
    () => buildLocationChips(currentLocation, favorites, locations, pinnedLocations),
    [currentLocation, favorites, locations, pinnedLocations],
  );

  const updateScrollEdges = useCallback(() => {
    const rail = scrollRef.current;
    if (!rail) return;
    const next = {
      left: rail.scrollLeft > 1,
      right: rail.scrollLeft + rail.clientWidth < rail.scrollWidth - 1,
    };
    setScrollEdges(previous =>
      previous.left === next.left && previous.right === next.right ? previous : next,
    );
  }, []);

  const scrollChipIntoView = useCallback((slug: string) => {
    const rail = scrollRef.current;
    const chip = chipRefs.current.get(slug);
    if (!rail || !chip) return;

    const railBounds = rail.getBoundingClientRect();
    const chipBounds = chip.getBoundingClientRect();
    const edgePadding = 24;
    if (chipBounds.left < railBounds.left + edgePadding) {
      rail.scrollBy({ left: chipBounds.left - railBounds.left - edgePadding, behavior: 'smooth' });
    } else if (chipBounds.right > railBounds.right - edgePadding) {
      rail.scrollBy({ left: chipBounds.right - railBounds.right + edgePadding, behavior: 'smooth' });
    }
  }, []);

  useEffect(() => {
    updateScrollEdges();
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(updateScrollEdges);
    if (scrollRef.current) observer?.observe(scrollRef.current);
    if (scrollContentRef.current) observer?.observe(scrollContentRef.current);
    window.addEventListener('resize', updateScrollEdges);
    return () => {
      observer?.disconnect();
      window.removeEventListener('resize', updateScrollEdges);
    };
  }, [chips, updateScrollEdges]);

  useEffect(() => {
    const savedSlug = pendingSavedSlugRef.current;
    const target = savedSlug && favorites.includes(savedSlug)
      ? savedSlug
      : previousCurrentSlugRef.current !== currentLocation.slug
        ? currentLocation.slug
        : null;
    if (target) scrollChipIntoView(target);
    pendingSavedSlugRef.current = null;
    previousCurrentSlugRef.current = currentLocation.slug;
    updateScrollEdges();
  }, [chips, currentLocation.slug, favorites, scrollChipIntoView, updateScrollEdges]);

  const scrollChips = (direction: -1 | 1) => {
    const rail = scrollRef.current;
    if (!rail) return;
    rail.scrollBy({ left: direction * Math.max(180, rail.clientWidth * 0.7), behavior: 'smooth' });
  };

  const handleFavoriteToggle = (loc: LocationItem) => {
    if (!favorites.includes(loc.slug)) pendingSavedSlugRef.current = loc.slug;
    onToggleFavorite(loc.slug);
  };

  const handleSelect = (loc: LocationItem) => {
    onSelectLocation(loc);
    setIsOpen(false);
    setQuery("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      setIsOpen(false);
      setQuery("");
      inputRef.current?.blur();
    }
  };

  const handleBlur = (event: React.FocusEvent<HTMLDivElement>) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      setIsOpen(false);
      setQuery("");
    }
  };

  return (
    <div className="mt-[20px] flex gap-[10px] flex-wrap items-center relative z-30">
      {/* Search Input Box */}
      <div ref={containerRef} onBlur={handleBlur} className="relative">
        <div className="bg-card border border-border rounded-full py-[8px] pr-[16px] pl-[14px] shadow-sh1 flex items-center gap-[9px] transition-colors focus-within:border-acc">
          {/* Location icon - 13x13px ring */}
          <span className="w-[13px] h-[13px] rounded-full border-[1.5px] border-acc inline-block flex-shrink-0" />

          {/* Input field */}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            aria-label="Tìm địa điểm"
            placeholder="Tìm tỉnh, thành phố…"
            className="w-[186px] max-w-[calc(100vw-200px)] min-w-0 text-[13.5px] text-ink placeholder:text-m4 bg-transparent border-none outline-none"
          />

        </div>

        {/* Dropdown Results */}
        {isOpen && (
          <div
            role="listbox"
            aria-label="Kết quả tìm địa điểm"
            className="absolute top-[46px] left-0 w-[330px] max-w-[calc(100vw-44px)] max-h-[330px] overflow-y-auto bg-card border border-border rounded-[18px] shadow-sh3 p-[8px] z-50"
          >
            {isFetching && filteredLocations.length === 0 ? (
              <div className="py-[16px] px-[14px] text-[13px] text-m2 text-center">
                Đang tìm địa điểm…
              </div>
            ) : filteredLocations.length === 0 ? (
              <div className="py-[16px] px-[14px] text-[13px] text-m2 text-center">
                Không tìm thấy địa điểm nào khớp.
              </div>
            ) : (
              filteredLocations.map((loc) => {
                const isCurrent = loc.slug === currentLocation.slug;
                const isSaved = favorites.includes(loc.slug);
                const temperature = isCurrent && currentTemperature !== undefined
                  ? currentTemperature
                  : temperatures?.[loc.slug];
                return (
                  <div
                    key={loc.slug}
                    role="option"
                    aria-selected={isCurrent}
                    className={`flex items-center rounded-[10px] transition-colors ${
                      isCurrent
                        ? "bg-acc-soft text-acc font-semibold"
                        : "hover:bg-tint text-ink"
                    }`}
                  >
                    <button
                      type="button"
                      onPointerDown={event => {
                        if (event.button === 0) handleSelect(loc);
                      }}
                      onClick={() => handleSelect(loc)}
                      className="min-w-0 flex-1 flex items-center justify-between text-left px-[14px] py-[9px] rounded-[10px] cursor-pointer focus-ring"
                    >
                      <span className="min-w-0">
                        <span className="text-[13.5px] block truncate">{loc.name}</span>
                        <span className="text-[11px] text-m3 block truncate">{loc.regionLabel}</span>
                      </span>
                      <span className="font-nunito font-semibold text-[15px] text-m1 ml-[8px] shrink-0">
                        {temperature !== undefined ? `${Math.round(temperature)}°` : "—"}
                      </span>
                    </button>
                    <button
                      type="button"
                      onPointerDown={event => event.preventDefault()}
                      onClick={() => handleFavoriteToggle(loc)}
                      title={isSaved ? `Bỏ lưu ${loc.name}` : `Lưu ${loc.name}`}
                      aria-label={isSaved ? `Bỏ lưu ${loc.name}` : `Lưu ${loc.name}`}
                      aria-pressed={isSaved}
                      className={`mr-[8px] p-[6px] rounded-full shrink-0 focus-ring transition-colors ${
                        isSaved ? "text-acc" : "text-m3 hover:text-acc"
                      }`}
                    >
                      <Star className="w-[16px] h-[16px]" fill={isSaved ? "var(--acc)" : "none"} strokeWidth={1.5} />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* Scrollable saved locations and default suggestions */}
      <div className="relative w-full min-w-0 min-[900px]:w-auto min-[900px]:flex-1">
        {scrollEdges.left && (
          <button
            type="button"
            onClick={() => scrollChips(-1)}
            aria-label="Cuộn địa điểm sang trái"
            className="absolute inset-y-0 left-0 z-10 flex items-center pl-[2px] pr-[16px] text-acc focus-ring"
            style={{ background: 'linear-gradient(to right, var(--bg) 55%, transparent)' }}
          >
            <ChevronLeft className="w-[16px] h-[16px]" strokeWidth={1.75} />
          </button>
        )}
        {scrollEdges.right && (
          <button
            type="button"
            onClick={() => scrollChips(1)}
            aria-label="Cuộn địa điểm sang phải"
            className="absolute inset-y-0 right-0 z-10 flex items-center pl-[16px] pr-[2px] text-acc focus-ring"
            style={{ background: 'linear-gradient(to left, var(--bg) 55%, transparent)' }}
          >
            <ChevronRight className="w-[16px] h-[16px]" strokeWidth={1.75} />
          </button>
        )}
        <div
          ref={scrollRef}
          onScroll={updateScrollEdges}
          role="group"
          aria-label="Địa điểm yêu thích và gợi ý"
          className="location-chip-scroll w-full overflow-x-auto scroll-smooth"
        >
          <div ref={scrollContentRef} className="flex w-max items-center gap-[8px] py-[2px]">
            {chips.map((loc, index) => {
              const isActive = loc.slug === currentLocation.slug;
              const isSaved = favorites.includes(loc.slug);
              return (
                <React.Fragment key={loc.slug}>
                  {index === suggestedStart && suggestedStart > 0 && (
                    <span role="separator" className="h-[20px] w-px bg-border mx-[3px] shrink-0" />
                  )}
                  <button
                    ref={node => {
                      if (node) chipRefs.current.set(loc.slug, node);
                      else chipRefs.current.delete(loc.slug);
                    }}
                    type="button"
                    onClick={() => onSelectLocation(loc)}
                    aria-pressed={isActive}
                    aria-label={isSaved ? `${loc.name}, đã lưu` : loc.name}
                    className={`shrink-0 whitespace-nowrap inline-flex items-center gap-[6px] px-[14px] py-[7px] rounded-full border text-[13px] transition-colors duration-150 focus-ring ${
                      isActive
                        ? "bg-acc text-acc-ink font-semibold border-acc shadow-xs"
                        : "bg-card border-border text-m1 hover:text-ink"
                    }`}
                  >
                    {isSaved && (
                      <Star
                        className={`w-[12px] h-[12px] ${isActive ? "text-acc-ink" : "text-acc"}`}
                        fill="currentColor"
                        strokeWidth={1.5}
                        aria-hidden="true"
                      />
                    )}
                    {loc.name}
                  </button>
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
