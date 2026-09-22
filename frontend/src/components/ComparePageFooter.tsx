import { ERA5_URL, FooterCard, SourceLink } from './FooterCard';

export function ComparePageFooter() {
  return (
    <footer className="grid gap-4 lg:grid-cols-2">
      <FooterCard title="Điểm du lịch tính thế nào">
        <p className="mt-3 text-[13px] leading-relaxed text-ink2">
          Mỗi tháng bắt đầu từ 100 điểm, bị trừ khi nhiệt độ trung bình dưới 20°C hoặc trên 28°C, và
          trừ thêm theo số ngày có mưa.
        </p>
        <p className="mt-2 text-[13px] leading-relaxed text-m1">
          Từ 80 điểm là rất thích hợp để đi, từ 60 điểm là đi được nhưng nên mang áo mưa.
        </p>
      </FooterCard>

      <FooterCard title="Dựa trên dữ liệu nào">
        <p className="mt-3 text-[13px] leading-relaxed text-ink2">
          Nhiệt độ, lượng mưa và số ngày có mưa trung bình của từng tháng trong 10 năm, từ{' '}
          <SourceLink href={ERA5_URL} label="Open-Meteo ERA5" />.
        </p>
        <p className="mt-2 text-[13px] leading-relaxed text-m1">
          Là tham khảo từ lịch sử khí hậu, không phải dự báo cho chuyến đi. Chưa xét gió, nắng hay
          độ ẩm.
        </p>
      </FooterCard>
    </footer>
  );
}
