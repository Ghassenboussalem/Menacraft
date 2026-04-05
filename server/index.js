require('dotenv').config();
const express = require('express');
const http    = require('http');
const cors    = require('cors');

const postsRoutes    = require('./routes/posts');
const verifyRoutes   = require('./routes/verify');
const verdictsRoutes = require('./routes/verdicts');

const PORT       = process.env.PORT || 3001;
const CLIENT_URL = process.env.CLIENT_URL || 'http://localhost:5173';
const IS_PROD    = process.env.NODE_ENV === 'production';

const app = express();

const corsOptions = {
  origin: IS_PROD ? CLIENT_URL : '*',
  methods: ['GET', 'POST', 'PATCH', 'DELETE'],
};

app.use(cors(corsOptions));
app.use(express.json({ limit: '50mb' }));

// ── REST Routes ──
app.use('/api/posts',    postsRoutes);
app.use('/api/verify',  verifyRoutes);
app.use('/api/verdicts', verdictsRoutes);

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', ts: Date.now(), env: process.env.NODE_ENV || 'development' });
});

// ── HTTP Server ──
const server = http.createServer(app);

// AI pipeline can take up to 5 minutes (Ollama fallback + 8 feature inspections)
server.timeout = 360000;
server.keepAliveTimeout = 360000;

server.listen(PORT, () => {
  console.log(`[sara7a-server] listening on :${PORT}`);
});
