import { FooterCard, SourceLink } from './FooterCard';

export function OverviewPageFooter() {
  return (
    <footer className="grid gap-4 lg:grid-cols-2">
      <FooterCard title="Điểm được tính thế nào">
        <p className="mt-3 text-[13px] leading-relaxed text-ink2">
          Mỗi giờ bắt đầu từ 100 điểm, bị trừ khi nhiệt độ lệch xa 25°C, khi khả năng mưa cao và
          khi chỉ số UV vượt 5.
        </p>
        <p className="mt-2 text-[13px] leading-relaxed text-m1">
          Điểm trong ngày là trung bình các giờ từ 06:00 đến 17:59. Giờ ban đêm luôn ở mức thấp
          nên không được gợi ý là khung giờ tốt.
        </p>
      </FooterCard>

      <FooterCard title="Dựa trên dữ liệu nào">
        <p className="mt-3 text-[13px] leading-relaxed text-ink2">
          Dự báo theo giờ cho 7 ngày tới từ{' '}
          <SourceLink href="https://open-meteo.com/en/docs" label="Open-Meteo Forecast" />, chất
          lượng không khí từ{' '}
          <SourceLink
            href="https://open-meteo.com/en/docs/air-quality-api"
            label="Open-Meteo Air Quality"
          />
          .
        </p>
        <p className="mt-2 text-[13px] leading-relaxed text-m1">
          Dự báo càng xa càng kém chính xác. Nên xem lại trước khi ra ngoài.
        </p>
      </FooterCard>
    </footer>
  );
}
