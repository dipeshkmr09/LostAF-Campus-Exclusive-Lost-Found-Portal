#============================================================
#BACKEND — Python Flask API
#============================================================

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

load_dotenv()  # reads .env file into os.environ

# ── Firebase Admin SDK ──────────────────────────────────────
try:
    import firebase_admin
    from firebase_admin import credentials, auth as fb_auth
    _FIREBASE_AVAILABLE = True
except ImportError:
    _FIREBASE_AVAILABLE = False
    print('[AUTH] firebase-admin not installed. Run: pip install firebase-admin')

# ── CONFIGURE YOUR COLLEGE EMAIL DOMAIN HERE ───────────────
ALLOWED_DOMAIN = 'cgu-odisha.ac.in'

# Initialize Firebase Admin SDK.
# • Local dev  → set FIREBASE_SERVICE_ACCOUNT to the path of your service account JSON file.
# • Vercel/cloud → set FIREBASE_SERVICE_ACCOUNT_JSON to the entire JSON content as a string.
_firebase_initialized = False
if _FIREBASE_AVAILABLE:
    try:
        import json as _json
        sa_json_str = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
        sa_path     = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

        if sa_json_str:
            # Cloud: JSON content stored directly as an env var string
            cred = credentials.Certificate(_json.loads(sa_json_str))
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            print(f'[AUTH] Firebase Admin initialized via JSON string. Domain: @{ALLOWED_DOMAIN}')
        elif sa_path:
            # Local: path to the service account JSON file
            cred = credentials.Certificate(sa_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            print(f'[AUTH] Firebase Admin initialized via file path. Domain: @{ALLOWED_DOMAIN}')
        else:
            print('[AUTH] WARNING: Neither FIREBASE_SERVICE_ACCOUNT_JSON nor FIREBASE_SERVICE_ACCOUNT is set.')
            print('[AUTH] Token verification is DISABLED — set one before going to production.')
    except Exception as e:
        print(f'[AUTH] Firebase Admin init failed: {e}')


app = Flask(__name__, static_folder='.', static_url_path='')
# Set ALLOWED_ORIGINS env var to your production domain in production.
# e.g. ALLOWED_ORIGINS=https://lostaf.example.com
_origins = os.environ.get('ALLOWED_ORIGINS', '*')
CORS(app, origins=_origins)


# ──── SERVE FRONTEND ────

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# Database connection
def get_db():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        conn = psycopg2.connect(database_url, sslmode='require')
    else:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            database=os.environ.get('DB_NAME', 'lostaf'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASS')
        )
    conn.set_client_encoding('UTF8')
    return conn


# ──── DB MIGRATIONS ────

def ensure_item_images_table():
    """Create the item_images table if it doesn't exist (Step 3 migration)."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS item_images (
                id            SERIAL PRIMARY KEY,
                item_id       INT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                image_data    TEXT NOT NULL,
                display_order INT DEFAULT 0,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_item_images_item ON item_images(item_id)")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB Migration] item_images: {e}")

ensure_item_images_table()


# ──── AUTH MIDDLEWARE ────

def verify_firebase_token(token):
    """Verify a Firebase ID token. Returns decoded token dict or None in dev mode."""
    if not _firebase_initialized:
        return None  # dev mode: skip verification
    return fb_auth.verify_id_token(token)


def require_auth(f):
    """Decorator: require a valid Firebase Bearer token in the Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required. Please sign in.'}), 401
        token = auth_header.split(' ', 1)[1]
        try:
            decoded = verify_firebase_token(token)
            if decoded is not None:
                email = decoded.get('email', '')
                if not email.endswith('@' + ALLOWED_DOMAIN):
                    return jsonify({
                        'error': 'Only college email accounts are allowed to use this portal.'
                    }), 403
            request.firebase_user = decoded  # None in dev mode, dict in prod
        except Exception:
            return jsonify({'error': 'Invalid or expired token. Please sign in again.'}), 401
        return f(*args, **kwargs)
    return decorated


# ──── RANK SYSTEM ────

RANK_TIERS = [
    (10, 'Legend',         '👑'),
    (6,  'Campus Hero',    '🦸'),
    (3,  'Good Samaritan', '⭐'),
    (1,  'Helper',         '🤝'),
    (0,  'Newcomer',       '🌱'),
]

def get_rank_title(items_returned):
    """Return (rank_title, badge_emoji) for a given items_returned count."""
    for threshold, title, badge in RANK_TIERS:
        if items_returned >= threshold:
            return title, badge
    return 'Newcomer', '🌱'


# ──── ITEMS ENDPOINTS ────

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all items with optional filters"""
    item_type = request.args.get('type')
    category = request.args.get('category')
    location = request.args.get('location')
    search = request.args.get('search')
    status = request.args.get('status', 'active')

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT i.*, u.name as user_name, u.avatar_emoji, u.email as user_email
        FROM items i
        JOIN users u ON i.user_id = u.id
        WHERE i.status = %s
    """
    params = [status]

    if item_type:
        query += " AND i.type = %s"
        params.append(item_type)
    if category:
        query += " AND i.category = %s"
        params.append(category)
    if location:
        query += " AND i.location = %s"
        params.append(location)
    if search:
        query += " AND (i.title ILIKE %s OR i.description ILIKE %s)"
        params.extend(['%' + search + '%', '%' + search + '%'])

    query += " ORDER BY i.created_at DESC"

    cur.execute(query, params)
    columns = [desc[0] for desc in cur.description]
    items = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()
    return jsonify(items)


@app.route('/api/items', methods=['POST'])
@require_auth
def create_item():
    """Create a new lost/found item — requires authentication"""
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    # Resolve user — prefer the verified token email over submitted email
    firebase_user = getattr(request, 'firebase_user', None)
    email = (firebase_user.get('email') if firebase_user else None) or data.get('email')

    user_id = None
    if email:
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            user_id = row[0]
        else:
            # Fallback create (shouldn't normally happen; sync is called on login)
            cur.execute("""
                INSERT INTO users (name, email)
                VALUES (%s, %s)
                RETURNING id
            """, (data.get('name', 'Anonymous'), email))
            user_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO items (user_id, type, title, description, category, location, image_url, item_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        user_id, data['type'], data['title'],
        data.get('description', ''), data['category'],
        data['location'], data.get('image_url', ''), data['item_date']
    ))

    item_id = cur.fetchone()[0]

    # ── Store multiple images in item_images table ──
    images = data.get('images', [])
    if images:
        for idx, img_data in enumerate(images[:4]):  # max 4 images
            cur.execute("""
                INSERT INTO item_images (item_id, image_data, display_order)
                VALUES (%s, %s, %s)
            """, (item_id, img_data, idx))
        # Also set the first image as the thumbnail
        if not data.get('image_url'):
            cur.execute("UPDATE items SET image_url = %s WHERE id = %s", (images[0], item_id))
    elif data.get('image_url'):
        # Legacy single-image: also store in item_images for consistency
        cur.execute("""
            INSERT INTO item_images (item_id, image_data, display_order)
            VALUES (%s, %s, 0)
        """, (item_id, data['image_url']))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'id': item_id, 'message': 'Item created successfully'}), 201


@app.route('/api/items/<int:item_id>/reunite', methods=['PUT'])
@require_auth
def reunite_item(item_id):
    """Mark an item as reunited — requires authentication AND ownership."""
    conn = get_db()
    cur = conn.cursor()

    # ── 1. Fetch item + owner in one query ──
    cur.execute("""
        SELECT i.status, u.email AS owner_email
        FROM items i
        JOIN users u ON i.user_id = u.id
        WHERE i.id = %s
    """, (item_id,))
    row = cur.fetchone()

    if not row:
        cur.close(); conn.close()
        return jsonify({'error': 'Item not found.'}), 404

    status, owner_email = row

    # ── 2. Already reunited? ──
    if status == 'reunited':
        cur.close(); conn.close()
        return jsonify({'error': 'This item has already been reunited.'}), 400

    # ── 3. Ownership check ──
    firebase_user = getattr(request, 'firebase_user', None)
    requester_email = firebase_user.get('email') if firebase_user else None

    if requester_email and requester_email != owner_email:
        cur.close(); conn.close()
        return jsonify({'error': 'Only the item owner can mark it as reunited.'}), 403

    # ── 4. All checks passed — mark reunited ──
    cur.execute("""
        UPDATE items SET status = 'reunited', updated_at = %s WHERE id = %s
    """, (datetime.now(), item_id))

    # ── 5. Increment owner's items_returned + update rank ──
    cur.execute("""
        UPDATE users SET items_returned = items_returned + 1,
                         updated_at     = CURRENT_TIMESTAMP
        WHERE id = (SELECT user_id FROM items WHERE id = %s)
        RETURNING items_returned
    """, (item_id,))
    new_count = cur.fetchone()[0]
    new_rank, _ = get_rank_title(new_count)
    cur.execute("""
        UPDATE users SET rank_title = %s
        WHERE id = (SELECT user_id FROM items WHERE id = %s)
    """, (new_rank, item_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': 'Item marked as reunited!', 'new_rank': new_rank})

# ──── ITEM IMAGES ────

@app.route('/api/items/<int:item_id>/images', methods=['GET'])
def get_item_images(item_id):
    """Get all images for an item."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT image_data, display_order
        FROM item_images
        WHERE item_id = %s
        ORDER BY display_order ASC
    """, (item_id,))
    images = [{'image_data': row[0], 'display_order': row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(images)


# ──── USERS ENDPOINTS ────

@app.route('/api/users/sync', methods=['POST'])
@require_auth
def sync_user():
    """Upsert a user record from Firebase auth data. Called after every successful login."""
    data = request.json
    firebase_user = getattr(request, 'firebase_user', None)
    firebase_uid = firebase_user['uid'] if firebase_user else None

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (name, email, firebase_uid, profile_picture)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
            name            = EXCLUDED.name,
            profile_picture = EXCLUDED.profile_picture,
            firebase_uid    = COALESCE(EXCLUDED.firebase_uid, users.firebase_uid),
            updated_at      = CURRENT_TIMESTAMP
        RETURNING id, name, email, avatar_emoji
    """, (
        data.get('name', ''),
        data['email'],
        firebase_uid,
        data.get('profile_picture', '')
    ))

    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'id': row[0], 'name': row[1], 'email': row[2], 'avatar_emoji': row[3]})


@app.route('/api/users', methods=['POST'])
def create_user():
    """Register a new user (legacy endpoint)"""
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (name, email, password_hash)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (data['name'], data['email'], data.get('password_hash', 'not-set')))

    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'id': user_id}), 201


# ──── MATCHES ────

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """Get recent confirmed matches"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT m.*, li.title as lost_title, fi.title as found_title,
               u.name as matched_by_name
        FROM matches m
        JOIN items li ON m.lost_item_id = li.id
        JOIN items fi ON m.found_item_id = fi.id
        LEFT JOIN users u ON m.matched_by = u.id
        WHERE m.status = 'confirmed'
        ORDER BY m.confirmed_at DESC
        LIMIT 20
    """)

    columns = [desc[0] for desc in cur.description]
    matches = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()
    return jsonify(matches)


# ──── STATS ────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM items")
    total_items = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM items WHERE status = 'reunited'")
    reunited = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.close()
    conn.close()

    return jsonify({
        'total_items': total_items,
        'reunited': reunited,
        'users': users
    })


# ──── LEADERBOARD ────

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top users ranked by items returned."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, avatar_emoji, items_returned, rank_title, profile_picture
        FROM users
        WHERE items_returned > 0
        ORDER BY items_returned DESC, updated_at ASC
        LIMIT 20
    """)

    columns = [desc[0] for desc in cur.description]
    leaders = []
    for row in cur.fetchall():
        user = dict(zip(columns, row))
        _, badge = get_rank_title(user['items_returned'])
        user['badge'] = badge
        leaders.append(user)

    cur.close()
    conn.close()
    return jsonify(leaders)


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, port=5000)
