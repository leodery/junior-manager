const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json({ limit: '2mb' }));

// PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

// Init DB
async function initDB() {
  const c = await pool.connect();
  try {
    await c.query(`CREATE TABLE IF NOT EXISTS wb_data (
      id SERIAL PRIMARY KEY, family_id VARCHAR(64) NOT NULL,
      app_name VARCHAR(32) NOT NULL, data JSONB NOT NULL DEFAULT '{}',
      updated_at TIMESTAMPTZ DEFAULT NOW()
    );`);
    await c.query(`CREATE UNIQUE INDEX IF NOT EXISTS idx_wb ON wb_data(family_id, app_name);`);
  } finally { c.release(); }
}

// API routes
app.get('/health', (_, res) => res.json({ ok: true }));

app.get('/api/data/:familyId/:appName', async (req, res) => {
  try {
    const r = await pool.query('SELECT data, updated_at FROM wb_data WHERE family_id=$1 AND app_name=$2', [req.params.familyId, req.params.appName]);
    res.json(r.rows[0] || { data: {}, updated_at: null });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.put('/api/data/:familyId/:appName', async (req, res) => {
  try {
    await pool.query(`INSERT INTO wb_data (family_id, app_name, data, updated_at) VALUES ($1,$2,$3,NOW()) ON CONFLICT (family_id, app_name) DO UPDATE SET data=$3, updated_at=NOW()`,
      [req.params.familyId, req.params.appName, JSON.stringify(req.body.data)]);
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Static files (junior-manager frontend)
app.use(express.static(path.join(__dirname, '..')));

const PORT = process.env.PORT || 3000;
initDB().then(() => app.listen(PORT, () => console.log(`WorkBuddy API + Static on ${PORT}`)));
