/**
 * API Client — Centralized HTTP client for the .NET backend API.
 * All frontend components should use this client instead of raw fetch().
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: any;
  headers?: Record<string, string>;
  token?: string;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  clearToken() {
    this.token = null;
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {}, token } = options;
    const authToken = token || this.token;

    const config: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...headers,
      },
    };

    if (body && method !== 'GET') {
      config.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config);

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new Error(`API ${method} ${endpoint} failed (${response.status}): ${errorText}`);
    }

    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    }
    return response.text() as unknown as T;
  }

  // ── Auth ──
  async login(username: string, password: string): Promise<{ token: string }> {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: { username, password },
    });
  }

  // ── Projects ──
  async getProjects(): Promise<any[]> {
    return this.request('/api/project');
  }

  async getProject(id: string): Promise<any> {
    return this.request(`/api/project/${id}`);
  }

  async updateProjectStatus(id: string, status: string): Promise<any> {
    return this.request(`/api/project/${id}/status`, {
      method: 'PUT',
      body: { status },
    });
  }

  // ── RFP Upload ──
  async uploadRfp(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/RfpUpload/upload`, {
      method: 'POST',
      headers: this.token ? { Authorization: `Bearer ${this.token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }
    return response.json();
  }

  // ── AI Engine Proxy Endpoints ──
  async getCompliance(): Promise<any> {
    return this.request('/api/compliance/matrix');
  }

  async evaluateGoNoGo(features: Record<string, number>): Promise<any> {
    return this.request('/api/compliance/go-nogo', {
      method: 'POST',
      body: features,
    });
  }

  async generateProposal(projectId: string, rfpText: string): Promise<any> {
    return this.request('/api/proposal/generate', {
      method: 'POST',
      body: { project_id: projectId, rfp_text: rfpText },
    });
  }

  // ── Health ──
  async healthCheck(): Promise<{ service: string; status: string }> {
    return this.request('/');
  }
}

export const apiClient = new ApiClient(API_BASE);
export default ApiClient;
