import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Header } from '@/components/layout/header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Activity, Rocket, Key, TrendingUp } from 'lucide-react'

export function DashboardPage() {
  const { data: deployments = [] } = useQuery({
    queryKey: ['deployments'],
    queryFn: () => api.getDeployments(),
  })

  const { data: apiKeys = [] } = useQuery({
    queryKey: ['apiKeys'],
    queryFn: () => api.getApiKeys(),
  })

  const stats = [
    {
      title: 'Total Deployments',
      value: deployments.length,
      icon: Rocket,
      change: '+12%',
      changeType: 'positive' as const,
    },
    {
      title: 'Active API Keys',
      value: apiKeys.filter(k => k.is_active).length,
      icon: Key,
      change: '+3',
      changeType: 'positive' as const,
    },
    {
      title: 'Total Replicas',
      value: deployments.reduce((sum, d) => sum + d.replicas, 0),
      icon: Activity,
      change: '+8%',
      changeType: 'positive' as const,
    },
    {
      title: 'Health Score',
      value: '98%',
      icon: TrendingUp,
      change: '+2%',
      changeType: 'positive' as const,
    },
  ]

  const recentDeployments = deployments.slice(0, 5)

  return (
    <div className="flex-1 overflow-auto">
      <Header
        title="Dashboard"
        description="Overview of your Kubernetes deployments"
      />

      <div className="p-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {stat.title}
                  </CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground">
                    <span className="text-green-500">{stat.change}</span> from last month
                  </p>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Recent Deployments */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Deployments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentDeployments.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No deployments yet
                </div>
              ) : (
                recentDeployments.map((deployment) => (
                  <div
                    key={deployment.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Rocket className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">{deployment.name}</p>
                        <p className="text-sm text-muted-foreground">{deployment.image}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge variant="success">
                        {deployment.replicas} replicas
                      </Badge>
                      <Badge variant={deployment.status === 'running' ? 'success' : 'warning'}>
                        {deployment.status}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
