import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { Header } from '@/components/layout/header'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, RefreshCw } from 'lucide-react'

export function DeploymentDetailsPage() {
  const { name } = useParams<{ name: string }>()

  const { data: deployment, isLoading } = useQuery({
    queryKey: ['deployment', name],
    queryFn: () => api.getDeployment(name!),
    enabled: !!name,
  })

  const { data: logs, refetch: refetchLogs } = useQuery({
    queryKey: ['logs', name],
    queryFn: () => api.getDeploymentLogs(name!, 200),
    enabled: !!name,
    refetchInterval: 5000, // Auto-refresh logs every 5 seconds
  })

  if (isLoading || !deployment) {
    return (
      <div className="flex-1 overflow-auto">
        <Header title="Loading..." />
        <div className="p-6 text-center text-muted-foreground">
          Loading deployment details...
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-auto">
      <Header title={deployment.name} description={deployment.image} />

      <div className="p-6 space-y-6">
        <Link to="/deployments">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Deployments
          </Button>
        </Link>

        {/* Overview */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge variant={deployment.status === 'running' ? 'success' : 'warning'}>
                  {deployment.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Image</p>
                <p className="font-mono text-sm">{deployment.image}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Domain</p>
                <p className="text-sm">{deployment.domain || 'Not configured'}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Port</p>
                  <p className="text-lg font-bold">{deployment.port}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Replicas</p>
                  <p className="text-lg font-bold">{deployment.replicas}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resources</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {deployment.resource_limits ? (
                <>
                  <div>
                    <p className="text-sm text-muted-foreground">CPU Limit</p>
                    <p className="text-lg font-bold">
                      {deployment.resource_limits.cpu || 'Not set'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Memory Limit</p>
                    <p className="text-lg font-bold">
                      {deployment.resource_limits.memory || 'Not set'}
                    </p>
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">No resource limits configured</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Environment Variables */}
        {deployment.environment_variables &&
          Object.keys(deployment.environment_variables).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Environment Variables</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(deployment.environment_variables).map(([key, value]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between p-3 bg-muted rounded-lg"
                    >
                      <code className="text-sm font-mono">{key}</code>
                      <code className="text-sm font-mono text-muted-foreground">{value}</code>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

        {/* Logs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Logs</CardTitle>
                <CardDescription>Last 200 lines • Auto-refreshing</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={() => refetchLogs()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-xs overflow-auto max-h-96">
              {logs ? (
                <pre>{logs}</pre>
              ) : (
                <p className="text-muted-foreground">No logs available</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
