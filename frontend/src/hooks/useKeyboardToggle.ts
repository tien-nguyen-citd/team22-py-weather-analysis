import { useEffect, useState } from 'react';

/** Đảo trạng thái bật/tắt mỗi khi người dùng nhấn tổ hợp phím khớp với `matches`. */
export function useKeyboardToggle(matches: (event: KeyboardEvent) => boolean): boolean {
  const [isOn, setIsOn] = useState(false);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (!matches(event)) return;
      event.preventDefault();
      setIsOn(value => !value);
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [matches]);

  return isOn;
}
