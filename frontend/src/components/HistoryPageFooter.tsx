import { ERA5_URL, FooterCard, SourceLink } from './FooterCard';

export function HistoryPageFooter() {
  return (
    <footer className="grid gap-4 lg:grid-cols-2">
      <FooterCard title="Cách đọc biểu đồ">
        <p className="mt-3 text-[13px] leading-relaxed text-ink2">
          Cột đậm là lượng mưa từng tháng trong 12 tháng trọn vẹn gần nhất. Cột nhạt là trung bình
          của cùng tháng đó trong 10 năm trước.
        </p>
        <p className="mt-2 text-[13px] leading-relaxed text-m1">
          Cột đậm cao hơn cột nhạt nghĩa là tháng đó mưa nhiều hơn bình thường. Một ngày được tính
          là có mưa khi lượng mưa từ 1 mm trở lên.
        </p>
      </FooterCard>

      <FooterCard title="Dựa trên dữ liệu nào">
        <p className="mt-3 text-[13px] leading-relaxed text-ink2">
          Lượng mưa và nhiệt độ trung bình ngày từ dữ liệu tái phân tích{' '}
          <SourceLink href={ERA5_URL} label="Open-Meteo ERA5" />.
        </p>
        <p className="mt-2 text-[13px] leading-relaxed text-m1">
          Dữ liệu tái phân tích được dựng lại từ quan trắc và mô hình, có thể lệch so với trạm đo
          tại chỗ.
        </p>
      </FooterCard>
    </footer>
  );
}
