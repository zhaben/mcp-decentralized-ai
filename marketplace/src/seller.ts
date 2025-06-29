import express from "express";
import type { Request, Response } from "express";

import Database from "better-sqlite3";
import path from "path";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";

const mcpServer = new McpServer({
  name: "seller",
  version: "1.0.0",
});

mcpServer.tool(
  "sell_offer",
  "Give the list of item I'm selling.",
  {},
  async () => {
    return {
      content: [
        {
          type: "text",
          text: "I'm selling one apple at the price of 100$",
        },
      ],
    };
  }
);

mcpServer.tool(
  "negociate_price",
  "Negociate the price, if the price is below the minimum price, refuse to sell, else accept to sell.",
  {
    // item_name: z.string(),
    proposed_price: z.number(),
    // ai_agent_address: z.string(),
    // owner_name: z.string(),
  },
  async ({ proposed_price }) => {
    if(proposed_price > 50) {
      return {
        content: [{ type: "text", text: "I accept the price." }],
      };
    } else {
      return {
        content: [{ type: "text", text: "I refuse the price." }],
      };
    }
  }
);


const app = express();
app.use(express.json());

app.post("/mcp", async (req, res) => {
  try {
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("Erreur MCP:", error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: {
          code: -32603,
          message: "Erreur serveur",
        },
        id: null,
      });
    }
  }
});

const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined, // set to undefined for stateless servers
});

// Setup routes for the server
const setupServer = async () => {
  await mcpServer.connect(transport);
};

app.post('/mcp', async (req: Request, res: Response) => {
  console.log('Received MCP request:', req.body);
  try {
      await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error('Error handling MCP request:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Internal server error',
        },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (req: Request, res: Response) => {
  console.log('Received GET MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
  console.log('Received DELETE MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});


// Start the server
const PORT = process.env.PORT || 3000;
setupServer().then(() => {
  app.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
  });
}).catch(error => {
  console.error('Failed to set up the server:', error);
  process.exit(1);
});
