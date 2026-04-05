const router   = require('express').Router();
const { verifyPost, verifyPostReal, runAgentsSse } = require('../services/verifyService');

// POST /api/verify/:postId
// Body: { post: { id, image_url, caption, post_date, likes_count, comments_count, ... } }
router.post('/:postId', async (req, res) => {
  try {
    const { post } = req.body;
    if (!post) return res.status(400).json({ error: 'post object required in body' });

    const result = await verifyPostReal(post);
    res.json(result);
  } catch (err) {
    console.error('[verify] error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// POST /api/verify/:postId/stream  (NDJSON streaming)
// Each line is a complete JSON object: { type: 'agent'|'verdict'|'error', ...data }
router.post('/:postId/stream', async (req, res) => {
  const { post } = req.body;
  if (!post) return res.status(400).json({ error: 'post object required in body' });

  // Disable Nagle algorithm so each write() is flushed immediately
  if (req.socket) req.socket.setNoDelay(true);

  res.writeHead(200, {
    'Content-Type': 'application/x-ndjson',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no',
  });

  let clientClosed = false;
  req.on('close', () => { clientClosed = true; });

  function send(type, data) {
    if (clientClosed) return;
    try {
      // Strip very large base64 fields to keep lines small
      const clean = JSON.parse(JSON.stringify(data, (key, val) => {
        if (typeof val === 'string' && val.length > 50000) return '[truncated]';
        return val;
      }));
      const line = JSON.stringify({ type, ...clean }) + '\n';
      res.write(line);
    } catch (e) {
      console.error('[stream] write error:', e.message);
    }
  }

  try {
    await runAgentsSse(post, (eventType, data) => send(eventType, data));
  } catch (err) {
    send('error', { error: err.message });
  }

  if (!clientClosed) res.end();
});

module.exports = router;
