-- ============================================================
-- SQL SCHEMA — PostgreSQL
-- ============================================================

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL DEFAULT 'not-set',
    firebase_uid    TEXT UNIQUE,
    profile_picture TEXT,
    avatar_emoji    VARCHAR(50) DEFAULT '🧑‍🎓',
    items_returned  INT DEFAULT 0,
    rank_title      VARCHAR(50) DEFAULT 'Newcomer',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE items (
    id              SERIAL PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(10) NOT NULL CHECK (type IN ('lost', 'found')),
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    category        VARCHAR(50) NOT NULL,
    location        VARCHAR(100) NOT NULL,
    image_url       TEXT,
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'reunited', 'expired')),
    item_date       DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_items_type ON items(type);
CREATE INDEX idx_items_category ON items(category);
CREATE INDEX idx_items_location ON items(location);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_created ON items(created_at DESC);

CREATE TABLE matches (
    id              SERIAL PRIMARY KEY,
    lost_item_id    INT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    found_item_id   INT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    status          VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected')),
    matched_by      INT REFERENCES users(id),
    confirmed_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- MIGRATION — run these if upgrading an existing database
-- ============================================================
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS firebase_uid TEXT UNIQUE;
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture TEXT;
-- ALTER TABLE users ALTER COLUMN password_hash SET DEFAULT 'not-set';

-- STEP 3: Multiple images per item
CREATE TABLE IF NOT EXISTS item_images (
    id            SERIAL PRIMARY KEY,
    item_id       INT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    image_data    TEXT NOT NULL,
    display_order INT DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_item_images_item ON item_images(item_id);

-- MIGRATION for Step 3:
-- CREATE TABLE IF NOT EXISTS item_images (...);  -- run the block above
