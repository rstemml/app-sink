/**
 * App-Sink API Client
 * Handles communication with the App-Sink Kubernetes API
 */

import axios, { type AxiosInstance } from 'axios';

export interface Deployment {
  id: string;
  name: string;
  image: string;
  port: number;
  domain?: string;
  replicas: number;
  status: string;
  environment_variables?: Record<string, string>;
  resource_limits?: {
    cpu?: string;
    memory?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface DeployRequest {
  name: string;
  image: string;
  port: number;
  domain?: string;
  replicas?: number;
  environment_variables?: Record<string, string>;
  resource_limits?: {
    cpu?: string;
    memory?: string;
  };
}

export interface AnalyzeRequest {
  git_url?: string;
  local_path?: string;
  branch?: string;
}

export interface AnalyzeResponse {
  language: string;
  framework?: string;
  entry_point?: string;
  port?: number;
  dependencies: string[];
  recommended_resources: {
    cpu: string;
    memory: string;
  };
}

export class AppSinkClient {
  private client: AxiosInstance;

  constructor(baseURL: string, apiKey: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
    });
  }

  // Deployments
  async listDeployments(): Promise<Deployment[]> {
    const response = await this.client.get<Deployment[]>('/api/v1/apps');
    return response.data;
  }

  async getDeployment(name: string): Promise<Deployment> {
    const response = await this.client.get<Deployment>(`/api/v1/apps/${name}`);
    return response.data;
  }

  async createDeployment(data: DeployRequest): Promise<Deployment> {
    const response = await this.client.post<Deployment>('/api/v1/apps', data);
    return response.data;
  }

  async scaleDeployment(name: string, replicas: number): Promise<Deployment> {
    const response = await this.client.put<Deployment>(
      `/api/v1/apps/${name}/scale`,
      { replicas }
    );
    return response.data;
  }

  async deleteDeployment(name: string): Promise<void> {
    await this.client.delete(`/api/v1/apps/${name}`);
  }

  async getDeploymentLogs(name: string, tail = 100): Promise<string> {
    const response = await this.client.get<string>(
      `/api/v1/apps/${name}/logs`,
      { params: { tail } }
    );
    return response.data;
  }

  async rollbackDeployment(name: string): Promise<Deployment> {
    const response = await this.client.post<Deployment>(
      `/api/v1/apps/${name}/rollback`
    );
    return response.data;
  }

  // AI Analysis
  async analyzeRepository(data: AnalyzeRequest): Promise<AnalyzeResponse> {
    const response = await this.client.post<AnalyzeResponse>(
      '/api/v1/analyze',
      data
    );
    return response.data;
  }

  async analyzeAndDeploy(data: AnalyzeRequest & { name: string; domain?: string }) {
    const response = await this.client.post(
      '/api/v1/analyze-and-deploy',
      data
    );
    return response.data;
  }
}
