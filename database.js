const { Pool } = require('pg');
require('dotenv').config();

// Create PostgreSQL connection pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Database initialization function
async function initializeDatabase() {
  try {
    // Create users table for XP system
    await pool.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(20) UNIQUE NOT NULL,
        guild_id VARCHAR(20) NOT NULL,
        username VARCHAR(100) NOT NULL,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        total_messages INTEGER DEFAULT 0,
        last_message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create guild settings table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS guild_settings (
        id SERIAL PRIMARY KEY,
        guild_id VARCHAR(20) UNIQUE NOT NULL,
        xp_enabled BOOLEAN DEFAULT true,
        xp_rate INTEGER DEFAULT 15,
        level_up_channel VARCHAR(20),
        admin_role VARCHAR(20),
        mod_role VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create moderation logs table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS mod_logs (
        id SERIAL PRIMARY KEY,
        guild_id VARCHAR(20) NOT NULL,
        user_id VARCHAR(20) NOT NULL,
        moderator_id VARCHAR(20) NOT NULL,
        action VARCHAR(50) NOT NULL,
        reason TEXT,
        duration INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    console.log('✅ Database tables initialized successfully');
  } catch (error) {
    console.error('❌ Error initializing database:', error);
    throw error;
  }
}

// XP calculation functions
function calculateXPForLevel(level) {
  return Math.floor(100 * Math.pow(level, 1.5));
}

function calculateLevelFromXP(xp) {
  let level = 1;
  while (calculateXPForLevel(level + 1) <= xp) {
    level++;
  }
  return level;
}

// Database helper functions
async function getUser(userId, guildId) {
  try {
    const result = await pool.query(
      'SELECT * FROM users WHERE user_id = $1 AND guild_id = $2',
      [userId, guildId]
    );
    return result.rows[0];
  } catch (error) {
    console.error('Error getting user:', error);
    return null;
  }
}

async function createUser(userId, guildId, username) {
  try {
    const result = await pool.query(
      'INSERT INTO users (user_id, guild_id, username) VALUES ($1, $2, $3) RETURNING *',
      [userId, guildId, username]
    );
    return result.rows[0];
  } catch (error) {
    console.error('Error creating user:', error);
    return null;
  }
}

async function updateUserXP(userId, guildId, xpGain) {
  try {
    const user = await getUser(userId, guildId);
    if (!user) return null;

    const newXP = user.xp + xpGain;
    const newLevel = calculateLevelFromXP(newXP);
    const leveledUp = newLevel > user.level;

    await pool.query(
      'UPDATE users SET xp = $1, level = $2, total_messages = total_messages + 1, last_message_time = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE user_id = $3 AND guild_id = $4',
      [newXP, newLevel, userId, guildId]
    );

    return { newXP, newLevel, leveledUp, oldLevel: user.level };
  } catch (error) {
    console.error('Error updating user XP:', error);
    return null;
  }
}

async function getLeaderboard(guildId, limit = 10) {
  try {
    const result = await pool.query(
      'SELECT username, xp, level FROM users WHERE guild_id = $1 ORDER BY xp DESC LIMIT $2',
      [guildId, limit]
    );
    return result.rows;
  } catch (error) {
    console.error('Error getting leaderboard:', error);
    return [];
  }
}

async function getGuildSettings(guildId) {
  try {
    const result = await pool.query(
      'SELECT * FROM guild_settings WHERE guild_id = $1',
      [guildId]
    );
    return result.rows[0];
  } catch (error) {
    console.error('Error getting guild settings:', error);
    return null;
  }
}

async function createGuildSettings(guildId) {
  try {
    const result = await pool.query(
      'INSERT INTO guild_settings (guild_id) VALUES ($1) RETURNING *',
      [guildId]
    );
    return result.rows[0];
  } catch (error) {
    console.error('Error creating guild settings:', error);
    return null;
  }
}

module.exports = {
  pool,
  initializeDatabase,
  calculateXPForLevel,
  calculateLevelFromXP,
  getUser,
  createUser,
  updateUserXP,
  getLeaderboard,
  getGuildSettings,
  createGuildSettings
};
