import {
  UserProfile, Project, Passage, Answer, AuditRunSummary,
  AuditRunResponse, ClaimAudit, ReviewQueueItem, AuditLog,
  LLMAdvisoryResponse, BenchmarkRunResponse
} from '../types';

let currentCsrfToken = '';
export const setCsrfToken = (t: string) => { currentCsrfToken = t; };

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set('Accept', 'application/json');

  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes((options.method || 'GET').toUpperCase())) {
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
    if (currentCsrfToken && !headers.has('x-csrf-token')) headers.set('x-csrf-token', currentCsrfToken);
  }

  const res = await fetch(path, { ...options, headers, credentials: 'include' });
  if (!res.ok) {
    let detail = `Request failed: ${res.status}`;
    try { const ej = await res.json(); if (ej.detail) detail = typeof ej.detail === 'string' ? ej.detail : JSON.stringify(ej.detail); } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  async getProfile(): Promise<UserProfile> {
    const d = await request<UserProfile>('/api/v1/auth/me');
    if (d.csrf_token) setCsrfToken(d.csrf_token);
    return d;
  },
  async demoLogin(role: string): Promise<UserProfile> {
    const d = await request<UserProfile>('/api/v1/auth/demo-login', { method: 'POST', body: JSON.stringify({ role }) });
    if (d.csrf_token) setCsrfToken(d.csrf_token);
    return d;
  },
  async logout(): Promise<void> {
    await request('/api/v1/auth/logout', { method: 'POST' });
    setCsrfToken('');
  },
  getProjects: () => request<Project[]>('/api/v1/audits/projects'),
  createProject: (name: string, description: string) => request<Project>('/api/v1/audits/projects', { method: 'POST', body: JSON.stringify({ name, description }) }),
  getPassages: (pid?: number) => request<Passage[]>(pid ? `/api/v1/audits/passages?project_id=${pid}` : '/api/v1/audits/passages'),
  ingestPassage: (p: any, pid?: number) => request<Passage>(pid ? `/api/v1/audits/passages?project_id=${pid}` : '/api/v1/audits/passages', { method: 'POST', body: JSON.stringify(p) }),
  getAnswers: (pid?: number) => request<Answer[]>(pid ? `/api/v1/audits/answers?project_id=${pid}` : '/api/v1/audits/answers'),
  ingestAnswer: (a: any, pid?: number) => request<Answer>(pid ? `/api/v1/audits/answers?project_id=${pid}` : '/api/v1/audits/answers', { method: 'POST', body: JSON.stringify(a) }),
  runAudit: (ansId: number) => request<AuditRunResponse>(`/api/v1/audits/run?answer_id=${ansId}`, { method: 'POST' }),
  getAuditRuns: (pid?: number) => request<AuditRunSummary[]>(pid ? `/api/v1/audits/runs?project_id=${pid}` : '/api/v1/audits/runs'),
  getAuditRun: (runId: number) => request<AuditRunResponse>(`/api/v1/audits/runs/${runId}`),
  getClaimAdvisory: (cid: number) => request<LLMAdvisoryResponse>(`/api/v1/audits/claims/${cid}/advisory`, { method: 'POST' }),
  async exportAudit(runId: number, fmt: 'json' | 'markdown' | 'csv'): Promise<string> {
    const r = await fetch(`/api/v1/audits/runs/${runId}/export?format=${fmt}`, { credentials: 'include' });
    if (!r.ok) throw new Error(`Export failed: ${r.statusText}`);
    return r.text();
  },
  getReviewQueue: (st?: string, pr?: string) => {
    const sp = new URLSearchParams();
    if (st) sp.append('status_filter', st);
    if (pr) sp.append('priority_filter', pr);
    return request<ReviewQueueItem[]>(`/api/v1/review/queue${sp.toString() ? `?${sp.toString()}` : ''}`);
  },
  submitReviewAction: (act: any) => request<ClaimAudit>('/api/v1/review/action', { method: 'POST', body: JSON.stringify(act) }),
  getAuditLogs: () => request<AuditLog[]>('/api/v1/review/audit-logs'),
  getBenchmark: () => request<BenchmarkRunResponse>('/api/v1/evaluation/benchmark'),
  getDataset: () => request<any[]>('/api/v1/evaluation/dataset')
};
