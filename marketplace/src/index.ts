import express from "express";
import type { Request, Response } from "express";

import bodyParser from "body-parser";
import Database from "better-sqlite3";
import path from "path";


const app = express();
app.use(bodyParser.json());

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

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server started on http://localhost:${PORT}`);
});
