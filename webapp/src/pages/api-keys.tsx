import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Header } from '@/components/layout/header'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Plus, Copy, Trash2, Power, Key as KeyIcon, Check } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export function ApiKeysPage() {
  const queryClient = useQueryClient()
  const [isCreating, setIsCreating] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyDescription, setNewKeyDescription] = useState('')
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const { data: apiKeys = [], isLoading } = useQuery({
    queryKey: ['apiKeys'],
    queryFn: () => api.getApiKeys(),
  })

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      api.createApiKey(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] })
      setCreatedKey(data.api_key)
      setNewKeyName('')
      setNewKeyDescription('')
      setTimeout(() => setIsCreating(false), 5000)
    },
  })

  const toggleMutation = useMutation({
    mutationFn: ({ keyId, isActive }: { keyId: string; isActive: boolean }) =>
      api.toggleApiKey(keyId, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (keyId: string) => api.deleteApiKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] })
    },
  })

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      name: newKeyName,
      description: newKeyDescription || undefined,
    })
  }

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="flex-1 overflow-auto">
      <Header
        title="API Keys"
        description="Manage your API keys for programmatic access"
      />

      <div className="p-6 space-y-6">
        {/* Create New Key */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Create New API Key</CardTitle>
                <CardDescription>
                  Generate a new API key for accessing the App-Sink API
                </CardDescription>
              </div>
              <Button
                onClick={() => setIsCreating(!isCreating)}
                variant={isCreating ? 'secondary' : 'default'}
              >
                <Plus className="mr-2 h-4 w-4" />
                {isCreating ? 'Cancel' : 'New Key'}
              </Button>
            </div>
          </CardHeader>

          <AnimatePresence>
            {isCreating && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
              >
                <CardContent>
                  <form onSubmit={handleCreate} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="keyName">Key Name *</Label>
                      <Input
                        id="keyName"
                        placeholder="e.g., Production API Key"
                        value={newKeyName}
                        onChange={(e) => setNewKeyName(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="keyDescription">Description</Label>
                      <Input
                        id="keyDescription"
                        placeholder="Optional description"
                        value={newKeyDescription}
                        onChange={(e) => setNewKeyDescription(e.target.value)}
                      />
                    </div>

                    {createdKey && (
                      <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                        <p className="text-sm font-medium text-green-600 dark:text-green-400 mb-2">
                          API Key Created Successfully!
                        </p>
                        <p className="text-xs text-muted-foreground mb-3">
                          Copy this key now. You won't be able to see it again!
                        </p>
                        <div className="flex gap-2">
                          <Input
                            value={createdKey}
                            readOnly
                            className="font-mono text-sm"
                          />
                          <Button
                            type="button"
                            size="icon"
                            onClick={() => copyToClipboard(createdKey, 'new-key')}
                          >
                            {copiedId === 'new-key' ? (
                              <Check className="h-4 w-4" />
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </div>
                    )}

                    <Button
                      type="submit"
                      disabled={createMutation.isPending || !newKeyName}
                    >
                      Generate API Key
                    </Button>
                  </form>
                </CardContent>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>

        {/* API Keys List */}
        <Card>
          <CardHeader>
            <CardTitle>Your API Keys</CardTitle>
            <CardDescription>
              {apiKeys.length} API key{apiKeys.length !== 1 ? 's' : ''} total
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading...
              </div>
            ) : apiKeys.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No API keys yet. Create one to get started!
              </div>
            ) : (
              <div className="space-y-3">
                {apiKeys.map((key) => (
                  <motion.div
                    key={key.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <KeyIcon className="w-5 h-5 text-primary" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{key.name}</p>
                        {key.description && (
                          <p className="text-sm text-muted-foreground">
                            {key.description}
                          </p>
                        )}
                        <div className="flex gap-2 mt-1">
                          <p className="text-xs text-muted-foreground">
                            Created: {new Date(key.created_at).toLocaleDateString()}
                          </p>
                          {key.last_used_at && (
                            <p className="text-xs text-muted-foreground">
                              Last used: {new Date(key.last_used_at).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={key.is_active ? 'success' : 'secondary'}>
                        {key.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() =>
                          toggleMutation.mutate({
                            keyId: key.id,
                            isActive: !key.is_active,
                          })
                        }
                      >
                        <Power className={`h-4 w-4 ${key.is_active ? 'text-green-500' : ''}`} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          if (confirm('Are you sure you want to delete this API key?')) {
                            deleteMutation.mutate(key.id)
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
