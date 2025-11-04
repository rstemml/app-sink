import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/theme-provider'
import { LoginForm } from '@/components/auth/login-form'
import { Sidebar } from '@/components/layout/sidebar'
import { DashboardPage } from '@/pages/dashboard'
import { ApiKeysPage } from '@/pages/api-keys'
import { DeploymentsPage } from '@/pages/deployments'
import { DeploymentDetailsPage } from '@/pages/deployment-details'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    setIsAuthenticated(!!token)
  }, [])

  const handleLoginSuccess = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    setIsAuthenticated(false)
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark">
        <BrowserRouter>
          {!isAuthenticated ? (
            <LoginForm onSuccess={handleLoginSuccess} />
          ) : (
            <div className="flex h-screen overflow-hidden">
              <Sidebar onLogout={handleLogout} />
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/api-keys" element={<ApiKeysPage />} />
                <Route path="/deployments" element={<DeploymentsPage />} />
                <Route path="/deployments/:name" element={<DeploymentDetailsPage />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </div>
          )}
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
