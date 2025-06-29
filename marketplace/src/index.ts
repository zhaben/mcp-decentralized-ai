import express from "express";
import type { Request, Response } from "express";

import bodyParser from "body-parser";
import Database from "better-sqlite3";
import path from "path";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";

const db = new Database(path.resolve(__dirname, "../db.sqlite"));

db.exec(`
  CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    listed_price REAL NOT NULL,
    ai_agent_address TEXT NOT NULL,
    owner_name TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    offer_price REAL NOT NULL,
    buyer_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    FOREIGN KEY(listing_id) REFERENCES listings(id)
  );
`);

const app = express();
app.use(bodyParser.json());

const mcpServer = new McpServer({
  name: "marketplace-server",
  version: "1.0.0",
});

const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined, // stateless
});

mcpServer.tool(
  "list_listings",
  "List all the listings.",
  {},
  async () => {
    const listings = db.prepare("SELECT * FROM listings").all();
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(listings),
        },
      ],
    };
  }
);

mcpServer.tool(
  "create_listing",
  "Create a new listing (name, price, agent AI, owner).",
  {
    item_name: z.string(),
    listed_price: z.number(),
    ai_agent_address: z.string(),
    owner_name: z.string(),
  },
  async ({ item_name, listed_price, ai_agent_address, owner_name }) => {
    db.prepare("INSERT INTO listings (item_name, listed_price, ai_agent_address, owner_name) VALUES (?, ?, ?, ?)")
      .run(item_name, listed_price, ai_agent_address, owner_name);
    return {
      content: [{ type: "text", text: "Listing created with success." }],
    };
  }
);

mcpServer.tool(
  "list_offers",
  "List all the offers.",
  {},
  async () => {
    const rows = db.prepare(`
      SELECT offers.id, offers.listing_id, offers.offer_price, offers.buyer_name, offers.status,
             listings.item_name, listings.owner_name
      FROM offers
      JOIN listings ON offers.listing_id = listings.id
    `).all();

    const result = rows.map((row: any) => ({
      id: row.id,
      listing_id: row.listing_id,
      offer_price: row.offer_price,
      buyer_name: row.buyer_name,
      status: row.status,
      item_name: row.item_name,
      current_owner: row.owner_name,
    }));

    return {
      content: [{ type: "text", text: JSON.stringify(result)}],
    };
  }
);

mcpServer.tool(
  "make_offer",
  "Make a buy offer.",
  {
    listing_id: z.number(),
    offer_price: z.number(),
    buyer_name: z.string(),
  },
  async ({ listing_id, offer_price, buyer_name }) => {
    const listing = db.prepare("SELECT id FROM listings WHERE id = ?").get(listing_id);
    if (!listing) {
      return {
        content: [{ type: "text", text: "Listing not available." }],
      };
    }
    db.prepare("INSERT INTO offers (listing_id, offer_price, buyer_name) VALUES (?, ?, ?)")
      .run(listing_id, offer_price, buyer_name);
    return {
      content: [{ type: "text", text: "Offer submitted with success." }],
    };
  }
);

mcpServer.tool(
  "respond_to_offer",
  "Accept or reject a buy offer.",
  {
    offer_id: z.number(),
    action: z.enum(["accept", "reject"]),
  },
  async ({ offer_id, action }) => {
    type Offer = {
      id: number;
      listing_id: number;
      offer_price: number;
      buyer_name: string;
      status: string;
    };

    const offer = db.prepare("SELECT * FROM offers WHERE id = ?").get(offer_id) as Offer;

    if (!offer) {
      return {
        content: [{ type: "text", text: "Offer not available." }],
      };
    }

    if (offer.status !== "pending") {
      return {
        content: [{ type: "text", text: "Offer already processed." }],
      };
    }

    db.prepare("UPDATE offers SET status = ? WHERE id = ?").run(action, offer_id);

    if (action === "accept") {
      db.prepare("UPDATE listings SET owner_name = ? WHERE id = ?").run(
        offer.buyer_name,
        offer.listing_id
      );
    }

    return {
      content: [{ type: "text", text: `Offer ${action} with success.` }],
    };
  }
);

// mcpServer.connect(transport);

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

app.post("/listings", (req: Request, res: Response) => {
  const { item_name, listed_price, ai_agent_address, owner_name } = req.body;
  if (!item_name || !listed_price || !ai_agent_address || !owner_name) {
    res.status(400).json({ error: "Champs manquants" });
  }

  const stmt = db.prepare(
    "INSERT INTO listings (item_name, listed_price, ai_agent_address, owner_name) VALUES (?, ?, ?, ?)"
  );
  stmt.run(item_name, listed_price, ai_agent_address, owner_name);
  res.status(201).json({ message: "Listing créé" });
});

app.get("/listings", (_req: Request, res: Response) => {
  const rows = db.prepare("SELECT * FROM listings").all();
  res.json(rows);
});

app.post("/offers", (req: Request, res: Response) => {
  const { listing_id, offer_price, buyer_name } = req.body;
  if (!listing_id || !offer_price || !buyer_name) {
    res.status(400).json({ error: "Champs manquants" });
  }

  const listing = db
    .prepare("SELECT id FROM listings WHERE id = ?")
    .get(listing_id);
  if (!listing) {
    res.status(404).json({ error: "Listing introuvable" });
  }

  const stmt = db.prepare(
    "INSERT INTO offers (listing_id, offer_price, buyer_name) VALUES (?, ?, ?)"
  );
  stmt.run(listing_id, offer_price, buyer_name);
  res.status(201).json({ message: "Offre soumise" });
});

app.get("/offers", (_req: Request, res: Response) => {
  const rows = db
    .prepare(`
      SELECT offers.id, offers.listing_id, offers.offer_price, offers.buyer_name, offers.status,
             listings.item_name, listings.owner_name
      FROM offers
      JOIN listings ON offers.listing_id = listings.id
    `)
    .all();

  const result = rows.map((row: any) => ({
    id: row.id,
    listing_id: row.listing_id,
    offer_price: row.offer_price,
    buyer_name: row.buyer_name,
    status: row.status,
    item_name: row.item_name,
    current_owner: row.owner_name,
  }));

  res.json(result);
});

app.post("/offers/:id", (req: Request, res: Response) => {
  const offerId = parseInt(req.params.id);
  const { action } = req.body;

  if (!["accept", "reject"].includes(action)) {
    res.status(400).json({ error: "Action invalide" });
  }
  type Offer = {
    id: number;
    listing_id: number;
    offer_price: number;
    buyer_name: string;
    status: string;
  };

  const offer = db
    .prepare("SELECT * FROM offers WHERE id = ?")
    .get(offerId) as Offer;

  if (!offer) {
    res.status(404).json({ error: "Offre introuvable" });
  }

  if (offer.status !== "pending") {
    res.status(400).json({ error: "Offre déjà traitée" });
  }

  db.prepare("UPDATE offers SET status = ? WHERE id = ?").run(action, offerId);

  if (action === "accept") {
    db.prepare("UPDATE listings SET owner_name = ? WHERE id = ?").run(
      offer.buyer_name,
      offer.listing_id
    );
  }

  res.json({ message: `Offre ${action}ée` });
});

// const PORT = process.env.PORT || 3000;
// app.listen(PORT, () => {
//   console.log(`Server started on http://localhost:${PORT}`);
// });

const PORT = process.env.PORT || 3000;

async function start() {
  await mcpServer.connect(transport);
  app.listen(PORT, () => {
    console.log(`Server started on http://localhost:${PORT}`);
  });
}

start().catch((err) => {
  console.error("Erreur au démarrage :", err);
  process.exit(1);
});
