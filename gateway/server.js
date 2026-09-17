const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const cors = require('cors');
const { Pool } = require('pg');
const proxy = require('express-http-proxy');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const FASTAPI_URL = process.env.FASTAPI_BACKEND_URL || 'http://localhost:8000';
const JWT_SECRET = process.env.JWT_SECRET || 'finagent-jwt-secret-change-me';

// Configure Database Connection Pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

app.use(cors({
  origin: ['http://localhost:8501', 'http://127.0.0.1:8501'],
  credentials: true
}));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ─── Proactive Notification delivery webhook ──────────────────────────────────
app.post('/notifications/deliver', (req, res) => {
  const { user_id, title, message, content } = req.body;
  console.log('\n=========================================');
  console.log(`🚀 [NOTIFICATION DELIVERY SYSTEM]`);
  console.log(`To User ID: ${user_id}`);
  console.log(`Title:      ${title}`);
  console.log(`Message:    ${message}`);
  console.log(`Content:\n${content}`);
  console.log('=========================================\n');
  res.json({ success: true, delivered: true });
});

// Helper: Generate Token
function createToken(userId, email) {
  const expiryHours = parseInt(process.env.JWT_EXPIRY_HOURS || '24');
  return jwt.sign(
    { sub: userId.toString(), email: email },
    JWT_SECRET,
    { expiresIn: `${expiryHours}h` }
  );
}

// ─── User Authentication Operations (Express native) ─────────────────────────

// POST /api/auth/register
app.post('/api/auth/register', async (req, res) => {
  const { email, name, password, monthly_income, currency } = req.body;
  
  if (!email || !name || !password) {
    return res.status(400).json({ detail: 'Email, name, and password are required.' });
  }

  try {
    const existing = await pool.query('SELECT * FROM users WHERE email = $1', [email.toLowerCase()]);
    if (existing.rows.length > 0) {
      return res.status(400).json({ detail: 'Email already registered.' });
    }

    const hashedPassword = bcrypt.hashSync(password, 12);
    const result = await pool.query(
      'INSERT INTO users (email, name, hashed_password, monthly_income, currency, created_at, is_active) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id, name, email',
      [
        email.toLowerCase(),
        name,
        hashedPassword,
        monthly_income || 0.0,
        currency || 'INR',
        new Date(),
        true
      ]
    );

    const user = result.rows[0];
    const token = createToken(user.id, user.email);

    res.json({
      access_token: token,
      user_id: user.id,
      name: user.name,
      email: user.email
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ detail: 'Server registration error.' });
  }
});

// POST /api/auth/login
app.post('/api/auth/login', async (req, res) => {
  const { email, password } = req.body;
  
  if (!email || !password) {
    return res.status(400).json({ detail: 'Email and password are required.' });
  }

  try {
    const result = await pool.query('SELECT * FROM users WHERE email = $1', [email.toLowerCase()]);
    if (result.rows.length === 0) {
      return res.status(401).json({ detail: 'Invalid email or password.' });
    }

    const user = result.rows[0];
    if (!bcrypt.compareSync(password, user.hashed_password)) {
      return res.status(401).json({ detail: 'Invalid email or password.' });
    }

    const token = createToken(user.id, user.email);

    res.json({
      access_token: token,
      user_id: user.id,
      name: user.name,
      email: user.email
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ detail: 'Server login error.' });
  }
});

// ─── Reverse Proxy Gateway ────────────────────────────────────────────────────
app.use('/api', (req, res, next) => {
  // Allow preflight CORS requests and public endpoints through without mandatory token
  const publicPaths = ['/auth/login', '/auth/register', '/health', '/docs', '/openapi.json'];
  if (req.method === 'OPTIONS' || publicPaths.includes(req.path)) {
    return next();
  }

  // Validate Authorization header
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ detail: 'Missing or invalid authentication credentials.' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.userId = payload.sub;
    next();
  } catch (error) {
    return res.status(401).json({ detail: 'Invalid or expired authentication token.' });
  }
}, proxy(FASTAPI_URL, {
  proxyReqOptDecorator: function(proxyReqOpts, srcReq) {
    // Inject X-User-Id header to backend request if available
    if (srcReq.userId) {
      proxyReqOpts.headers['x-user-id'] = srcReq.userId;
    }
    return proxyReqOpts;
  },
  proxyReqPathResolver: function(req) {
    // Forward /api/xyz as /xyz in FastAPI
    return req.url;
  }
}));

app.listen(PORT, () => {
  console.log(`[Express Gateway] Running on http://localhost:${PORT}`);
  console.log(`[Express Gateway] Proxying backend requests to ${FASTAPI_URL}`);
});
