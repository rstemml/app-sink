#!/usr/bin/env node

/**
 * App-Sink MCP Server
 * Deploy to Kubernetes with natural language using Model Context Protocol
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { AppSinkClient } from './api-client.js';
import { z } from 'zod';

// Configuration from environment
const API_URL = process.env.APP_SINK_API_URL || 'http://localhost:8000';
const API_KEY = process.env.APP_SINK_API_KEY || '';

if (!API_KEY) {
  console.error('ERROR: APP_SINK_API_KEY environment variable is required');
  process.exit(1);
}

// Initialize API client
const apiClient = new AppSinkClient(API_URL, API_KEY);

// Tool Definitions
const TOOLS: Tool[] = [
  {
    name: 'app_sink_deploy',
    description: 'Deploy an application to Kubernetes. Can analyze a Git repository automatically or use provided configuration.',
    inputSchema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Name for the deployment (lowercase, alphanumeric, hyphens)',
        },
        git_url: {
          type: 'string',
          description: 'Git repository URL to deploy (will be analyzed automatically)',
        },
        image: {
          type: 'string',
          description: 'Docker image to deploy (e.g., nginx:latest). Use this OR git_url.',
        },
        port: {
          type: 'number',
          description: 'Port the application listens on (default: auto-detected)',
        },
        domain: {
          type: 'string',
          description: 'Custom domain for the deployment',
        },
        replicas: {
          type: 'number',
          description: 'Number of replicas (default: 1)',
        },
      },
      required: ['name'],
    },
  },
  {
    name: 'app_sink_list',
    description: 'List all deployments running on Kubernetes',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'app_sink_get_status',
    description: 'Get detailed status and information about a specific deployment',
    inputSchema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Name of the deployment',
        },
      },
      required: ['name'],
    },
  },
  {
    name: 'app_sink_logs',
    description: 'Get logs from a deployment',
    inputSchema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Name of the deployment',
        },
        lines: {
          type: 'number',
          description: 'Number of log lines to retrieve (default: 100)',
        },
      },
      required: ['name'],
    },
  },
  {
    name: 'app_sink_scale',
    description: 'Scale a deployment to a specific number of replicas',
    inputSchema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Name of the deployment',
        },
        replicas: {
          type: 'number',
          description: 'Number of replicas to scale to',
        },
      },
      required: ['name', 'replicas'],
    },
  },
  {
    name: 'app_sink_rollback',
    description: 'Rollback a deployment to the previous version',
    inputSchema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Name of the deployment',
        },
      },
      required: ['name'],
    },
  },
  {
    name: 'app_sink_delete',
    description: 'Delete a deployment from Kubernetes',
    inputSchema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Name of the deployment to delete',
        },
      },
      required: ['name'],
    },
  },
  {
    name: 'app_sink_analyze',
    description: 'Analyze a Git repository to detect language, framework, and deployment requirements',
    inputSchema: {
      type: 'object',
      properties: {
        git_url: {
          type: 'string',
          description: 'Git repository URL to analyze',
        },
        branch: {
          type: 'string',
          description: 'Git branch to analyze (default: main/master)',
        },
      },
      required: ['git_url'],
    },
  },
];

// Create MCP Server
const server = new Server(
  {
    name: 'app-sink',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Handle tool listing
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'app_sink_deploy': {
        const { name, git_url, image, port, domain, replicas } = args as any;

        // If git_url provided, use analyze-and-deploy
        if (git_url) {
          const result = await apiClient.analyzeAndDeploy({
            git_url,
            name,
            domain,
          });
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(result, null, 2),
              },
            ],
          };
        }

        // Otherwise, direct deployment
        if (!image) {
          throw new Error('Either git_url or image must be provided');
        }

        const deployment = await apiClient.createDeployment({
          name,
          image,
          port: port || 80,
          domain,
          replicas: replicas || 1,
        });

        return {
          content: [
            {
              type: 'text',
              text: `✅ Deployment created successfully!\n\n${JSON.stringify(deployment, null, 2)}`,
            },
          ],
        };
      }

      case 'app_sink_list': {
        const deployments = await apiClient.listDeployments();
        return {
          content: [
            {
              type: 'text',
              text: `Found ${deployments.length} deployment(s):\n\n${JSON.stringify(deployments, null, 2)}`,
            },
          ],
        };
      }

      case 'app_sink_get_status': {
        const { name } = args as any;
        const deployment = await apiClient.getDeployment(name);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(deployment, null, 2),
            },
          ],
        };
      }

      case 'app_sink_logs': {
        const { name, lines } = args as any;
        const logs = await apiClient.getDeploymentLogs(name, lines || 100);
        return {
          content: [
            {
              type: 'text',
              text: `Logs for ${name}:\n\n${logs}`,
            },
          ],
        };
      }

      case 'app_sink_scale': {
        const { name, replicas } = args as any;
        const deployment = await apiClient.scaleDeployment(name, replicas);
        return {
          content: [
            {
              type: 'text',
              text: `✅ Scaled ${name} to ${replicas} replicas\n\n${JSON.stringify(deployment, null, 2)}`,
            },
          ],
        };
      }

      case 'app_sink_rollback': {
        const { name } = args as any;
        const deployment = await apiClient.rollbackDeployment(name);
        return {
          content: [
            {
              type: 'text',
              text: `✅ Rolled back ${name} to previous version\n\n${JSON.stringify(deployment, null, 2)}`,
            },
          ],
        };
      }

      case 'app_sink_delete': {
        const { name } = args as any;
        await apiClient.deleteDeployment(name);
        return {
          content: [
            {
              type: 'text',
              text: `✅ Deployment ${name} deleted successfully`,
            },
          ],
        };
      }

      case 'app_sink_analyze': {
        const { git_url, branch } = args as any;
        const analysis = await apiClient.analyzeRepository({
          git_url,
          branch,
        });
        return {
          content: [
            {
              type: 'text',
              text: `Repository Analysis:\n\n${JSON.stringify(analysis, null, 2)}`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: 'text',
          text: `❌ Error: ${error.message}\n\n${error.response?.data ? JSON.stringify(error.response.data, null, 2) : ''}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('App-Sink MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
