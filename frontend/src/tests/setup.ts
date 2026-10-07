import '@testing-library/jest-dom';

const originalFetch = globalThis.fetch;
globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
  const urlStr = String(input);
  if (urlStr.includes('/api/v1/auth/me')) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        user_id: 'test-analyst',
        email: 'analyst@demo.local',
        roles: ['analyst'],
        is_authenticated: true,
        is_demo: true,
        csrf_token: 'test-csrf-token'
      })
    } as any;
  }
  if (urlStr.includes('/api/v1/review/queue')) {
    return {
      ok: true,
      status: 200,
      json: async () => []
    } as any;
  }
  if (originalFetch) {
    try {
      return await originalFetch(input, init);
    } catch {
      return { ok: true, status: 200, json: async () => ({}) } as any;
    }
  }
  return { ok: true, status: 200, json: async () => ({}) } as any;
};
