import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import {
  ApiResponse,
  PaginatedResponse,
  Scenario,
  CallHistoryItem,
  CallMetrics,
  User,
} from '@/types';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - redirect to login
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Generic request methods
  private async request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.request<T>(config);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  private handleError<T>(error: unknown): ApiResponse<T> {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message || error.message;
      return {
        success: false,
        error: message,
        message: message,
      };
    }
    return {
      success: false,
      error: 'An unexpected error occurred',
      message: 'An unexpected error occurred',
    };
  }

  // Scenario endpoints
  async getScenarios(): Promise<ApiResponse<Scenario[]>> {
    return this.request<Scenario[]>({
      method: 'GET',
      url: '/scenarios',
    });
  }

  async getScenario(id: string): Promise<ApiResponse<Scenario>> {
    return this.request<Scenario>({
      method: 'GET',
      url: `/scenarios/${id}`,
    });
  }

  // Call endpoints
  async startCall(scenarioId?: string): Promise<ApiResponse<{ sessionId: string; callId: string }>> {
    return this.request({
      method: 'POST',
      url: '/calls/start',
      data: { scenarioId },
    });
  }

  async endCall(callId: string): Promise<ApiResponse<void>> {
    return this.request({
      method: 'POST',
      url: `/calls/${callId}/end`,
    });
  }

  async getCallHistory(
    page = 1,
    pageSize = 20
  ): Promise<ApiResponse<PaginatedResponse<CallHistoryItem>>> {
    return this.request<PaginatedResponse<CallHistoryItem>>({
      method: 'GET',
      url: '/calls/history',
      params: { page, pageSize },
    });
  }

  async getCallDetails(callId: string): Promise<ApiResponse<CallHistoryItem>> {
    return this.request<CallHistoryItem>({
      method: 'GET',
      url: `/calls/${callId}`,
    });
  }

  async getCallMetrics(callId: string): Promise<ApiResponse<CallMetrics>> {
    return this.request<CallMetrics>({
      method: 'GET',
      url: `/calls/${callId}/metrics`,
    });
  }

  async getCallTranscript(callId: string): Promise<ApiResponse<any>> {
    return this.request({
      method: 'GET',
      url: `/calls/${callId}/transcript`,
    });
  }

  // User endpoints
  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>({
      method: 'GET',
      url: '/users/me',
    });
  }

  async updateUser(userId: string, data: Partial<User>): Promise<ApiResponse<User>> {
    return this.request<User>({
      method: 'PATCH',
      url: `/users/${userId}`,
      data,
    });
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.request({
      method: 'GET',
      url: '/health',
    });
  }
}

// Singleton instance
export const apiService = new ApiService();
export default apiService;
