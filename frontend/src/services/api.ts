import type {
  AnalysisDetail, AnalysisHistoryResponse, ModelStatus, HealthStatus,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiClientError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, options);
  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    try {
      const body = await resp.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new ApiClientError(detail, resp.status);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthStatus>('/health'),
  modelStatus: () => request<ModelStatus>('/model/status'),

  uploadAnalysis: async (file: File): Promise<AnalysisDetail> => {
    const formData = new FormData();
    formData.append('file', file);
    return request<AnalysisDetail>('/analysis/upload', { method: 'POST', body: formData });
  },

  predictAnalysis: (id: string) => request<AnalysisDetail>(`/analysis/predict/${id}`, { method: 'POST' }),
  getAnalysis: (id: string) => request<AnalysisDetail>(`/analysis/${id}`),

  history: (params?: { page?: number; pageSize?: number; search?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set('page', String(params.page));
    if (params?.pageSize) q.set('page_size', String(params.pageSize));
    if (params?.search) q.set('search', params.search);
    if (params?.status) q.set('status', params.status);
    return request<AnalysisHistoryResponse>(`/analysis/history?${q.toString()}`);
  },

  deleteAnalysis: (id: string) => request<{ success: boolean; id: string }>(`/analysis/${id}`, { method: 'DELETE' }),

  originalUrl: (id: string) => `${API_BASE}/analysis/${id}/original`,
  maskUrl: (id: string) => `${API_BASE}/analysis/${id}/mask`,
  overlayUrl: (id: string) => `${API_BASE}/analysis/${id}/overlay`,
  exportUrl: (id: string, format: 'json' | 'pdf') => `${API_BASE}/analysis/${id}/export?format=${format}`,
};

export { ApiClientError };
