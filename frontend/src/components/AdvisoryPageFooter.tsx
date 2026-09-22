import type { ActivityProfile } from '../api/advisory';
import { ERA5_URL, FooterCard, SourceLink } from './FooterCard';

interface AdvisoryPageFooterProps {
  activities: ActivityProfile[];
}

export function AdvisoryPageFooter({ activities }: AdvisoryPageFooterProps) {
  return (
    <footer className="grid gap-4 lg:grid-cols-2">
      <FooterCard title="Tư vấn được cho">
        <div className="mt-3.5 flex flex-wrap gap-1.5">
          {activities.map(activity => (
            <span
              key={activity.id}
              className="rounded-full bg-tint px-3 py-1.5 text-[12.5px] text-ink2"
            >
              {activity.name}
            </span>
          ))}
        </div>
      </FooterCard>

      <FooterCard title="Dựa trên dữ liệu nào">
        <p className="mt-3 text-[13px] leading-relaxed text-ink2">
          Lượng mưa và nhiệt độ trung bình ngày trong 10 năm, từ{' '}
          <SourceLink href={ERA5_URL} label="Open-Meteo ERA5" />.
        </p>
        <p className="mt-2 text-[13px] leading-relaxed text-m1">
          Là tham khảo từ lịch sử khí hậu, không phải dự báo cho một ngày cụ thể. Chưa xét gió,
          nắng, sóng biển hay độ ẩm.
        </p>
      </FooterCard>
    </footer>
  );
}
