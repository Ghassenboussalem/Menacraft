const router = require('express').Router();
const { getSupabase, createSupabaseFromCreds } = require('../lib/supabase');

// GET /api/posts — fetch posts from server-side Supabase config
router.get('/', async (req, res) => {
  try {
    const sb = getSupabase();
    if (!sb) return res.status(400).json({ error: 'Supabase not configured on server' });

    const table = process.env.SUPABASE_TABLE || 'instagram_posts';
    const { data, error } = await sb
      .from(table)
      .select('*')
      .order('post_date', { ascending: false })
      .limit(100);

    if (error) throw error;
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/posts/connect — connect with client-provided credentials
router.post('/connect', async (req, res) => {
  try {
    const { url, key, table } = req.body;
    if (!url || !key) return res.status(400).json({ error: 'url and key are required' });

    const sb = createSupabaseFromCreds(url, key);
    const tableName = table || 'instagram_posts';
    const { data, error } = await sb
      .from(tableName)
      .select('*')
      .order('post_date', { ascending: false })
      .limit(100);

    if (error) throw error;
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
