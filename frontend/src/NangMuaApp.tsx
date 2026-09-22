import React, { useState, useEffect } from 'react';
import {
  useParams,
  useNavigate,
  useLocation,
  Link,
} from 'react-router-dom';
import { skipToken, useQuery } from '@tanstack/react-query';
import { Header, type PageTab } from './components/Header';
import { LocationBar } from './components/LocationBar';
import { OverviewPage } from './pages/OverviewPage';
import { ComparePage } from './pages/ComparePage';
import { HistoryPage } from './pages/HistoryPage';
import { AdvisoryPage } from './pages/AdvisoryPage';
import { DestinationPage } from './pages/DestinationPage';
import { WeatherSkeleton } from './components/WeatherSkeleton';
import { ErrorMessage } from './components/ErrorMessage';
import {
  DEFAULT_LOCATION_SLUG,
  findLocationBySlug,
} from './api/locations';
import { getForecast } from './api/forecast';
import { useLocations } from './hooks/useLocations';
import { useUserLocation } from './hooks/useUserLocation';
import type { LocationItem } from './types';

const FAVORITES_STORAGE_KEY = 'nang_mua_favorites';
const EMPTY_LOCATIONS: LocationItem[] = [];

export const NangMuaApp: React.FC = () => {
  const { locationSlug, page } = useParams<{ locationSlug?: string; page?: string }>();
  const navigate = useNavigate();
  const routerLocation = useLocation();
  const locationsQuery = useLocations();
  const locations = locationsQuery.data ?? EMPTY_LOCATIONS;

  // Selected location from URL or fallback
  const currentLocation = findLocationBySlug(
    locations,
    locationSlug || DEFAULT_LOCATION_SLUG,
  );
  const userLocationState = useUserLocation(locations, currentLocation);

  // Selected tab
  const validPages: PageTab[] = ['tong-quan', 'so-sanh', 'lich-su', 'tu-van', 'di-dau'];
  const currentPage: PageTab = validPages.includes(page as PageTab)
    ? (page as PageTab)
    : 'tong-quan';
  const usesClimateAdvice = currentPage === 'tu-van' || currentPage === 'di-dau';

  // Favorites from localStorage
  const [favorites, setFavorites] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(FAVORITES_STORAGE_KEY);
      const parsed: unknown = saved ? JSON.parse(saved) : [];
      return Array.isArray(parsed)
        ? [...new Set(parsed.filter((slug): slug is string => typeof slug === 'string'))]
        : [];
    } catch {
      return [];
    }
  });

  const toggleFavorite = (slug: string) => {
    setFavorites(prev => {
      const next = prev.includes(slug) ? prev.filter(s => s !== slug) : [slug, ...prev];
      try {
        localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(next));
      } catch (e) {
        console.error('Failed to save favorites to localStorage', e);
      }
      return next;
    });
  };

  // Đường dẫn gốc mở địa điểm người dùng sau khi đã đọc lưu trữ hoặc định vị.
  useEffect(() => {
    if (
      userLocationState.isInitialized &&
      userLocationState.userLocation &&
      (routerLocation.pathname === '/' || !locationSlug)
    ) {
      navigate(`/${userLocationState.userLocation.slug}/tong-quan`, { replace: true });
    }
  }, [
    locationSlug,
    navigate,
    routerLocation.pathname,
    userLocationState.isInitialized,
    userLocationState.userLocation,
  ]);

  // TanStack Query for weather data (cached 30 minutes)
  const {
    data: weatherData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['weather', currentLocation?.slug],
    queryFn: currentLocation
      ? () => getForecast(currentLocation.slug)
      : skipToken,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });

  const handleSelectLocation = (loc: LocationItem) => {
    navigate(`/${loc.slug}/${currentPage}`);
  };

  const handleSelectPage = (nextPage: PageTab) => {
    if (currentLocation) {
      navigate(`/${currentLocation.slug}/${nextPage}`);
    }
  };

  if (locationsQuery.isPending) {
    return (
      <div className="min-h-screen bg-bg text-ink px-[22px] pt-[26px] pb-[80px]">
        <div className="max-w-[1080px] mx-auto">
          <WeatherSkeleton />
        </div>
      </div>
    );
  }

  if (locationsQuery.isError || !currentLocation || !userLocationState.userLocation) {
    return (
      <div className="min-h-screen bg-bg text-ink px-[22px] pt-[26px] pb-[80px]">
        <div className="max-w-[1080px] mx-auto">
          <ErrorMessage
            title="Không tải được danh sách địa điểm"
            message="Vui lòng kiểm tra kết nối và thử lại."
            onRetry={() => void locationsQuery.refetch()}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg text-ink selection:bg-acc-soft selection:text-acc px-[22px] pt-[26px] pb-[80px]">
      <div className="max-w-[1080px] mx-auto">
        {/* Common Header */}
        <Header
          currentPage={currentPage}
          onSelectPage={handleSelectPage}
          userLocation={userLocationState.userLocation}
          isDetectingUserLocation={userLocationState.isDetecting}
          userLocationError={userLocationState.errorMessage}
          onSelectUserLocation={userLocationState.selectUserLocation}
          onDetectUserLocation={userLocationState.detectUserLocation}
        />

        {/* Trang So sánh, Tư vấn và Đi đâu? tự chọn địa điểm nên không dùng LocationBar. */}
        {currentPage !== 'so-sanh' && !usesClimateAdvice && (
          <LocationBar
            currentLocation={currentLocation}
            locations={locations}
            currentTemperature={weatherData?.tempNow}
            onSelectLocation={handleSelectLocation}
            favorites={favorites}
            onToggleFavorite={toggleFavorite}
          />
        )}

        {/* Page Content */}
        {currentPage === 'tu-van' ? (
          <main>
            <AdvisoryPage
              locations={locations}
              userLocationSlug={userLocationState.userLocation.slug}
            />
          </main>
        ) : currentPage === 'di-dau' ? (
          <main><DestinationPage /></main>
        ) : currentPage === 'so-sanh' ? (
          <main>
            <ComparePage
              currentLocation={currentLocation}
              locations={locations}
            />
          </main>
        ) : currentPage === 'lich-su' ? (
          <main><HistoryPage currentLocation={currentLocation} /></main>
        ) : isLoading && !weatherData ? (
          <WeatherSkeleton />
        ) : isError && !weatherData ? (
          <ErrorMessage
            title="Không tải được dữ liệu thời tiết"
            message={
              <>
                Không tải được dữ liệu thời tiết cho{' '}
                <strong>{currentLocation.name}</strong>. Vui lòng kiểm tra kết
                nối mạng và thử lại.
              </>
            }
            onRetry={() => refetch()}
          />
        ) : (
          weatherData && (
            <main><OverviewPage data={weatherData} /></main>
          )
        )}

        <footer className="mt-[36px] text-center">
          <Link
            className="focus-ring rounded-md px-[6px] py-[3px] text-[12px] text-m3 transition-colors hover:text-acc"
            to="/admin"
          >
            Quản trị
          </Link>
        </footer>
      </div>
    </div>
  );
};
