import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Header } from '@/components/layout/header'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Rocket,
  Trash2,
  RotateCcw,
  ChevronRight,
  TrendingUp,
  TrendingDown,
} from 'lucide-react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'

export function DeploymentsPage() {
  const queryClient = useQueryClient()

  const { data: deployments = [], isLoading } = useQuery({
    queryKey: ['deployments'],
    queryFn: () => api.getDeployments(),
  })

  const scaleMutation = useMutation({
    mutationFn: ({ name, replicas }: { name: string; replicas: number }) =>
      api.scaleDeployment(name, replicas),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (name: string) => api.deleteDeployment(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
  })

  const rollbackMutation = useMutation({
    mutationFn: (name: string) => api.rollbackDeployment(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
  })

  const handleScale = (name: string, currentReplicas: number, increment: number) => {
    const newReplicas = Math.max(0, currentReplicas + increment)
    scaleMutation.mutate({ name, replicas: newReplicas })
  }

  return (
    <div className="flex-1 overflow-auto">
      <Header
        title="Deployments"
        description="Manage your Kubernetes deployments"
      />

      <div className="p-6">
        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">
            Loading deployments...
          </div>
        ) : deployments.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <div className="w-16 h-16 rounded-full bg-muted mx-auto mb-4 flex items-center justify-center">
                <Rocket className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">No deployments yet</h3>
              <p className="text-muted-foreground mb-4">
                Get started by deploying your first application
              </p>
              <Button>
                <Rocket className="mr-2 h-4 w-4" />
                Deploy Application
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {deployments.map((deployment, index) => (
              <motion.div
                key={deployment.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                          <Rocket className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{deployment.name}</CardTitle>
                          <CardDescription className="text-xs">
                            {deployment.domain || 'No domain'}
                          </CardDescription>
                        </div>
                      </div>
                      <Badge
                        variant={deployment.status === 'running' ? 'success' : 'warning'}
                      >
                        {deployment.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Image */}
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Image</p>
                      <p className="text-sm font-mono truncate">{deployment.image}</p>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Replicas</p>
                        <div className="flex items-center gap-2">
                          <Button
                            size="icon"
                            variant="outline"
                            className="h-6 w-6"
                            onClick={() => handleScale(deployment.name, deployment.replicas, -1)}
                            disabled={deployment.replicas === 0}
                          >
                            <TrendingDown className="h-3 w-3" />
                          </Button>
                          <span className="text-lg font-bold">{deployment.replicas}</span>
                          <Button
                            size="icon"
                            variant="outline"
                            className="h-6 w-6"
                            onClick={() => handleScale(deployment.name, deployment.replicas, 1)}
                          >
                            <TrendingUp className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Port</p>
                        <p className="text-lg font-bold">{deployment.port}</p>
                      </div>
                    </div>

                    {/* Resources */}
                    {deployment.resource_limits && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Resources</p>
                        <div className="flex gap-2">
                          {deployment.resource_limits.cpu && (
                            <Badge variant="outline">
                              CPU: {deployment.resource_limits.cpu}
                            </Badge>
                          )}
                          {deployment.resource_limits.memory && (
                            <Badge variant="outline">
                              RAM: {deployment.resource_limits.memory}
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2 pt-2 border-t">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1"
                        onClick={() => {
                          if (
                            confirm(
                              `Rollback ${deployment.name} to previous version?`
                            )
                          ) {
                            rollbackMutation.mutate(deployment.name)
                          }
                        }}
                      >
                        <RotateCcw className="mr-1 h-3 w-3" />
                        Rollback
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          if (
                            confirm(
                              `Are you sure you want to delete ${deployment.name}?`
                            )
                          ) {
                            deleteMutation.mutate(deployment.name)
                          }
                        }}
                      >
                        <Trash2 className="h-3 w-3 text-destructive" />
                      </Button>
                      <Link to={`/deployments/${deployment.name}`}>
                        <Button size="sm">
                          <ChevronRight className="h-3 w-3" />
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
