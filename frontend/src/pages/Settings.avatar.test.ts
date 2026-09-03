import { describe, expect, it } from 'vitest';
import { avatarValidationError, MAX_AVATAR_SIZE } from './Settings';

const file = (size: number, type: string, name = 'avatar.png') =>
  new File([new Uint8Array(size)], name, { type });

describe('profile avatar validation', () => {
  it.each([
    ['JPG', 'image/jpeg'],
    ['PNG', 'image/png'],
    ['WebP', 'image/webp'],
  ])('accepts a valid %s image', (_label, type) => {
    expect(avatarValidationError(file(1024, type))).toBe('');
  });

  it('accepts the exact 10 MB boundary', () => {
    expect(avatarValidationError(file(MAX_AVATAR_SIZE, 'image/png'))).toBe('');
  });

  it('rejects one byte above 10 MB', () => {
    expect(avatarValidationError(file(MAX_AVATAR_SIZE + 1, 'image/png'))).toContain('10 MB');
  });

  it('rejects unsupported MIME types even with an image extension', () => {
    expect(avatarValidationError(file(128, 'text/plain'))).toContain('JPG');
  });
});
