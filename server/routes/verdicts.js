/**
 * Verdict persistence — reads/writes to Supabase `post_verdicts` table.
 *
 * Required Supabase table (run once in SQL editor):
 *
 *   CREATE TABLE IF NOT EXISTS post_verdicts (
 *     post_id     TEXT PRIMARY KEY,
 *     verdict     TEXT,
 *     confidence  INTEGER,
 *     synthesis   TEXT,
 *     agents      JSONB,
 *     created_at  TIMESTAMPTZ DEFAULT NOW(),
 *     updated_at  TIMESTAMPTZ DEFAULT NOW()
 *   );
 */

const router = require('express').Router();
const { getSupabase } = require('../lib/supabase');

const TABLE = 'post_verdicts';

// GET /api/verdicts/:postId
router.get('/:postId', async (req, res) => {
  try {
    const sb = getSupabase();
    if (!sb) return res.status(503).json({ error: 'Supabase not configured' });

    const { data, error } = await sb
      .from(TABLE)
      .select('*')
      .eq('post_id', req.params.postId)
      .maybeSingle();

    if (error) throw error;
    if (!data) return res.status(404).json({ error: 'Not found' });

    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/verdicts/:postId  — upsert
router.post('/:postId', async (req, res) => {
  try {
    const sb = getSupabase();
    if (!sb) return res.status(503).json({ error: 'Supabase not configured' });

    const { verdict, confidence, synthesis, agents } = req.body;
    if (!verdict) return res.status(400).json({ error: 'verdict required' });

    // Strip annotated_image_b64 from agents before persisting — it's large binary
    // data that belongs in memory only, not in Postgres.
    const agentsForDb = Array.isArray(agents)
      ? agents.map((a) => {
          if (!a.raw?.annotated_image_b64) return a;
          const { annotated_image_b64: _dropped, ...rawWithout } = a.raw;
          return { ...a, raw: rawWithout };
        })
      : agents;

    const { data, error } = await sb
      .from(TABLE)
      .upsert({
        post_id: req.params.postId,
        verdict,
        confidence,
        synthesis,
        agents: agentsForDb,
        updated_at: new Date().toISOString(),
      }, { onConflict: 'post_id' })
      .select()
      .single();

    if (error) throw error;
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/verdicts/:postId
router.delete('/:postId', async (req, res) => {
  try {
    const sb = getSupabase();
    if (!sb) return res.status(503).json({ error: 'Supabase not configured' });

    const { error } = await sb
      .from(TABLE)
      .delete()
      .eq('post_id', req.params.postId);

    if (error) throw error;
    res.json({ ok: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
