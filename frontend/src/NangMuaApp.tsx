import React, { useState, useEffect } from 'react';
import {
  useParams,
  useNavigate,
  useLocation,
  Link,
} from 'react-router-dom';
import { skipToken, useIsFetching, useQuery, useQueryClient } from '@tanstack/react-query';
import { Header, type PageTab } from './components/Header';
import { LocationBar } from './components/LocationBar';
import { OverviewPage } from './pages/OverviewPage';
import { PlannerPage } from './pages/PlannerPage';
import { ComparePage } from './pages/ComparePage';
import { HistoryPage } from './pages/HistoryPage';
import { AdvisoryPage } from './pages/AdvisoryPage';
import { AdvisoryPageV2 } from './pages/AdvisoryPageV2';
import { WeatherSkeleton } from './components/WeatherSkeleton';
import { ErrorMessage } from './components/ErrorMessage';
import {
  DEFAULT_LOCATION_SLUG,
  findLocationBySlug,
  findNearestLocation,
} from './api/locations';
import { getForecast } from './api/forecast';
import { useLocations } from './hooks/useLocations';
import type { LocationItem } from './types';

const FAVORITES_STORAGE_KEY = 'nang_mua_favorites';
const EMPTY_LOCATIONS: LocationItem[] = [];

function formatUpdatedAt(updatedAt: string | undefined): string {
  if (!updatedAt) return 'Đang cập nhật...';

  const date = new Date(updatedAt);
  if (Number.isNaN(date.getTime())) return 'Đang cập nhật...';

  const formatter = new Intl.DateTimeFormat('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    weekday: 'long',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  });
  const parts = Object.fromEntries(
    formatter.formatToParts(date).map(part => [part.type, part.value]),
  );
  return `${parts.weekday} · ${parts.day}/${parts.month}/${parts.year} · ${parts.hour}:${parts.minute}`;
}

export const NangMuaApp: React.FC = () => {
  const { locationSlug, page } = useParams<{ locationSlug?: string; page?: string }>();
  const navigate = useNavigate();
  const routerLocation = useLocation();
  const queryClient = useQueryClient();
  const climateIsFetching = useIsFetching({ queryKey: ['climate'] });
  const advisoryIsFetching = useIsFetching({ queryKey: ['advisory'] });
  const locationsQuery = useLocations();
  const locations = locationsQuery.data ?? EMPTY_LOCATIONS;

  // Selected location from URL or fallback
  const currentLocation = findLocationBySlug(
    locations,
    locationSlug || DEFAULT_LOCATION_SLUG,
  );

  // Selected tab
  const validPages: PageTab[] = ['tong-quan', 'khung-gio', 'so-sanh', 'lich-su', 'tu-van', 'tu-van-v2'];
  const currentPage: PageTab = validPages.includes(page as PageTab)
    ? (page as PageTab)
    : 'tong-quan';

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

  // Check geolocation on very first visit if on root '/'
  useEffect(() => {
    if (locations.length > 0 && (routerLocation.pathname === '/' || !locationSlug)) {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
          pos => {
            const nearest = findNearestLocation(
              locations,
              pos.coords.latitude,
              pos.coords.longitude,
            );
            navigate(`/${nearest?.slug ?? DEFAULT_LOCATION_SLUG}/tong-quan`, {
              replace: true,
            });
          },
          () => {
            // Default fallback
            navigate(`/${DEFAULT_LOCATION_SLUG}/tong-quan`, { replace: true });
          },
          { timeout: 5000 }
        );
      } else {
        navigate(`/${DEFAULT_LOCATION_SLUG}/tong-quan`, { replace: true });
      }
    }
  }, [locationSlug, locations, routerLocation.pathname, navigate]);

  // TanStack Query for weather data (cached 30 minutes)
  const {
    data: weatherData,
    isLoading,
    isError,
    isFetching,
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

  if (locationsQuery.isError || !currentLocation) {
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
          updatedAt={currentPage === 'tu-van' || currentPage === 'tu-van-v2' ? 'Tư vấn từ lịch sử khí hậu' : formatUpdatedAt(weatherData?.updatedAt)}
          isFetching={isFetching || climateIsFetching > 0 || advisoryIsFetching > 0}
          onRefresh={() => {
            void refetch();
            void queryClient.invalidateQueries({ queryKey: ['climate'] });
            void queryClient.invalidateQueries({ queryKey: ['advisory'] });
          }}
        />

        {/* Common Location Bar — trang Tư vấn V2 tự chọn địa điểm nên không dùng */}
        {currentPage !== 'tu-van-v2' && (
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
        {currentPage === 'tu-van-v2' ? (
          <main><AdvisoryPageV2 locations={locations} /></main>
        ) : currentPage === 'tu-van' ? (
          <main><AdvisoryPage key={`${currentLocation.slug}:${routerLocation.search}`} currentLocation={currentLocation} locations={locations} /></main>
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
            <main>
              {currentPage === 'tong-quan' && <OverviewPage data={weatherData} />}
              {currentPage === 'khung-gio' && <PlannerPage data={weatherData} />}
            </main>
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
