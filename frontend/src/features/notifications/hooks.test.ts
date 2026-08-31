import { describe, expect, it } from 'vitest';
import { shouldUseNotificationsSocket } from './hooks';

describe('notification transport selection', () => {
  it('uses polling instead of an implicit socket on production hosts', () => {
    expect(shouldUseNotificationsSocket(undefined, 'devflow-frontend-delta.vercel.app')).toBe(false);
  });

  it('keeps sockets available locally or when explicitly configured', () => {
    expect(shouldUseNotificationsSocket(undefined, 'localhost')).toBe(true);
    expect(shouldUseNotificationsSocket('wss://notifications.example.test', 'app.example.test')).toBe(true);
  });
});
