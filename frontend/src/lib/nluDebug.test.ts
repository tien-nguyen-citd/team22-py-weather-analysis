import { describe, expect, it } from 'vitest';
import { isNluDebugShortcut, type ShortcutKeys } from './nluDebug';

const keys = (overrides: Partial<ShortcutKeys>): ShortcutKeys => ({
  ctrlKey: false,
  altKey: false,
  shiftKey: false,
  metaKey: false,
  key: 'Backspace',
  ...overrides,
});

describe('phím tắt chi tiết phân tích NLU', () => {
  it('nhận Ctrl + Alt + Backspace', () => {
    expect(isNluDebugShortcut(keys({ ctrlKey: true, altKey: true }))).toBe(true);
  });

  it.each([
    ['chỉ Backspace', keys({})],
    ['thiếu Alt', keys({ ctrlKey: true })],
    ['thiếu Ctrl', keys({ altKey: true })],
    ['thêm Shift', keys({ ctrlKey: true, altKey: true, shiftKey: true })],
    ['phím khác', keys({ ctrlKey: true, altKey: true, key: 'Delete' })],
  ])('bỏ qua %s', (_, event) => {
    expect(isNluDebugShortcut(event)).toBe(false);
  });
});
