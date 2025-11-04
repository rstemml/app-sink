import axios, { type AxiosInstance } from 'axios'
import type {
  ApiKey,
  Deployment,
  LoginRequest,
  LoginResponse,
  CreateApiKeyRequest,
  CreateApiKeyResponse,
  CreateDeploymentRequest,
  UpdateDeploymentRequest,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor to include auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Auth
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/api/v1/auth/login', credentials)
    return response.data
  }

  // API Keys
  async getApiKeys(): Promise<ApiKey[]> {
    const response = await this.client.get<ApiKey[]>('/api/v1/keys')
    return response.data
  }

  async createApiKey(data: CreateApiKeyRequest): Promise<CreateApiKeyResponse> {
    const response = await this.client.post<CreateApiKeyResponse>('/api/v1/keys', data)
    return response.data
  }

  async toggleApiKey(keyId: string, isActive: boolean): Promise<ApiKey> {
    const response = await this.client.patch<ApiKey>(`/api/v1/keys/${keyId}`, { is_active: isActive })
    return response.data
  }

  async deleteApiKey(keyId: string): Promise<void> {
    await this.client.delete(`/api/v1/keys/${keyId}`)
  }

  // Deployments
  async getDeployments(skip = 0, limit = 100): Promise<Deployment[]> {
    const response = await this.client.get<Deployment[]>('/api/v1/apps', {
      params: { skip, limit },
    })
    return response.data
  }

  async getDeployment(name: string): Promise<Deployment> {
    const response = await this.client.get<Deployment>(`/api/v1/apps/${name}`)
    return response.data
  }

  async createDeployment(data: CreateDeploymentRequest): Promise<Deployment> {
    const response = await this.client.post<Deployment>('/api/v1/apps', data)
    return response.data
  }

  async updateDeployment(name: string, data: UpdateDeploymentRequest): Promise<Deployment> {
    const response = await this.client.put<Deployment>(`/api/v1/apps/${name}`, data)
    return response.data
  }

  async scaleDeployment(name: string, replicas: number): Promise<Deployment> {
    const response = await this.client.put<Deployment>(`/api/v1/apps/${name}/scale`, { replicas })
    return response.data
  }

  async deleteDeployment(name: string): Promise<void> {
    await this.client.delete(`/api/v1/apps/${name}`)
  }

  async getDeploymentLogs(name: string, tail = 100): Promise<string> {
    const response = await this.client.get<string>(`/api/v1/apps/${name}/logs`, {
      params: { tail },
    })
    return response.data
  }

  async rollbackDeployment(name: string): Promise<Deployment> {
    const response = await this.client.post<Deployment>(`/api/v1/apps/${name}/rollback`)
    return response.data
  }

  // Health
  async getHealth(): Promise<{ status: string; kubernetes: boolean; database: boolean }> {
    const response = await this.client.get('/api/v1/health')
    return response.data
  }
}

export const api = new ApiClient()
