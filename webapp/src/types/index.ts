export interface ApiKey {
  id: string
  name: string
  description?: string
  key_hash: string
  is_active: boolean
  created_at: string
  last_used_at?: string
}

export interface Deployment {
  id: string
  name: string
  image: string
  port: number
  domain?: string
  replicas: number
  status: string
  environment_variables?: Record<string, string>
  resource_limits?: {
    cpu?: string
    memory?: string
  }
  created_at: string
  updated_at: string
}

export interface DeploymentHistory {
  id: string
  deployment_id: string
  action: 'create' | 'update' | 'scale' | 'rollback' | 'delete'
  previous_image?: string
  previous_replicas?: number
  changes?: Record<string, any>
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface CreateApiKeyRequest {
  name: string
  description?: string
}

export interface CreateApiKeyResponse {
  id: string
  name: string
  description?: string
  api_key: string  // Only returned once on creation
  created_at: string
}

export interface CreateDeploymentRequest {
  name: string
  image: string
  port: number
  domain?: string
  replicas?: number
  environment_variables?: Record<string, string>
  resource_limits?: {
    cpu?: string
    memory?: string
  }
}

export interface UpdateDeploymentRequest {
  image?: string
  replicas?: number
  domain?: string
  environment_variables?: Record<string, string>
}

export interface ApiError {
  detail: string
}
