import type { ActivityProfile } from '../api/advisory';

interface AdvisoryPageFooterProps {
  activities: ActivityProfile[];
}

export function AdvisoryPageFooter({ activities }: AdvisoryPageFooterProps) {
  return (
    <footer className="grid gap-4 lg:grid-cols-2">
      <section
        aria-label="Hoạt động được tư vấn"
        className="rounded-[20px] border border-border bg-card p-5 sm:p-6"
      >
        <h2 className="font-nunito text-[15.5px] font-bold">Tư vấn được cho</h2>
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
      </section>

      <section
        aria-label="Nguồn dữ liệu"
        className="rounded-[20px] border border-border bg-card p-5 sm:p-6"
      >
        <h2 className="font-nunito text-[15.5px] font-bold">Dựa trên dữ liệu nào</h2>
        <p className="mt-3 text-[13px] leading-relaxed text-ink2">
          Lượng mưa và nhiệt độ trung bình ngày trong 10 năm, từ{' '}
          <a
            href="https://open-meteo.com/en/docs/historical-weather-api"
            target="_blank"
            rel="noreferrer"
            className="focus-ring underline hover:text-acc"
          >
            Open-Meteo ERA5
          </a>
          .
        </p>
        <p className="mt-2 text-[13px] leading-relaxed text-m1">
          Là tham khảo từ lịch sử khí hậu, không phải dự báo cho một ngày cụ thể. Chưa xét gió,
          nắng, sóng biển hay độ ẩm.
        </p>
      </section>
    </footer>
  );
}
