const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
app.use(cors());
app.use(express.json({ limit: '2mb' }));

// PostgreSQL connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

// Initialize tables
async function initDB() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS workbuddy_data (
        id SERIAL PRIMARY KEY,
        family_id VARCHAR(64) NOT NULL,
        app_name VARCHAR(32) NOT NULL,
        data JSONB NOT NULL DEFAULT '{}',
        updated_at TIMESTAMPTZ DEFAULT NOW()
      );
      CREATE UNIQUE INDEX IF NOT EXISTS idx_family_app ON workbuddy_data(family_id, app_name);
    `);
    console.log('DB initialized');
  } finally { client.release(); }
}

// Health check
app.get('/health', (req, res) => {
  res.json({ ok: true, time: new Date().toISOString() });
});

// GET data for a family + app
app.get('/api/data/:familyId/:appName', async (req, res) => {
  try {
    const { familyId, appName } = req.params;
    const result = await pool.query(
      'SELECT data, updated_at FROM workbuddy_data WHERE family_id=$1 AND app_name=$2',
      [familyId, appName]
    );
    res.json(result.rows[0] || { data: {}, updated_at: null });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// PUT save data
app.put('/api/data/:familyId/:appName', async (req, res) => {
  try {
    const { familyId, appName } = req.params;
    const { data } = req.body;
    await pool.query(
      `INSERT INTO workbuddy_data (family_id, app_name, data, updated_at)
       VALUES ($1, $2, $3, NOW())
       ON CONFLICT (family_id, app_name) DO UPDATE SET data=$3, updated_at=NOW()`,
      [familyId, appName, JSON.stringify(data)]
    );
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// DELETE data
app.delete('/api/data/:familyId/:appName', async (req, res) => {
  try {
    const { familyId, appName } = req.params;
    await pool.query('DELETE FROM workbuddy_data WHERE family_id=$1 AND app_name=$2', [familyId, appName]);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

const PORT = process.env.PORT || 3000;
initDB().then(() => {
  app.listen(PORT, () => console.log(`API server on port ${PORT}`));
});
