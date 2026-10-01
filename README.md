# LostAF — Campus Lost & Found Portal

> The smartest way to find what you've lost on campus — or return what you've found. Powered by Trust.

A full-stack web application built for **C. V. Raman Global University (CGU), Odisha**. Students can report lost or found items, browse the live feed, and reunite belongings with their owners — all within a verified campus-only environment.

---

## Features

- **Browse without login** — anyone can view the item feed, filter by zone and category, and search
- **Google Sign-In** — restricted exclusively to `@cgu-odisha.ac.in` accounts, enforced both client-side and server-side
- **3-Step Report Wizard** — report a lost or found item with type, category, campus location, description, and optional image
- **Interactive Campus Map** — click any building on the SVG map to instantly filter the feed by that zone
- **Item Detail Modal** — click any card to see full details including a direct mailto contact link
- **Reunite Flow** — mark an item as reunited with a celebration
- **AI Smart Search** — real-time title and description filtering in the navbar
- **Responsive Design** — works on mobile with a collapsible hamburger menu

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla JS (SPA), HTML5, CSS3 (Glassmorphism) |
| Auth | Firebase Authentication v12 (Google Sign-In) |
| Backend | Python 3 · Flask 3 |
| Database | PostgreSQL |
| ORM / Driver | psycopg2 |
| Fonts & Icons | Inter · Space Grotesk · Font Awesome 6.5 |

---

## Project Structure

```
LostAF/
├── index.html          # Single-page application (all 4 pages)
├── style.css           # Full stylesheet (dark glassmorphism theme)
├── script.js           # Frontend logic (SPA router, feed, forms, modals)
├── auth.js             # Firebase Auth module (sign-in, state observer)
├── server.py           # Flask REST API backend
├── schema.sql          # PostgreSQL schema + migration notes
├── requirements.txt    # Python dependencies
├── resources/          # Static media assets (images, video, icons)
│   ├── favicon.svg
│   ├── cgu_logo.png
│   ├── cgu_poster.jpg
│   ├── cgu_vid.mp4
│   └── abhishek.webp
├── .gitignore
└── .env                # Local secrets (not committed)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- A Firebase project with Google Sign-In enabled
- A `@cgu-odisha.ac.in` Google account for testing

### 1. Clone the repository

```bash
git clone https://github.com/dipeshkmr09/LostAF-Campus-Exclusive-Lost-Found-Portal.git
cd LostAF
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Set up the database

Create the database and run the schema:

```bash
psql -U postgres -c "CREATE DATABASE lostaf;"
psql -U postgres -d lostaf -f schema.sql
```

If upgrading an existing database, run only the migration lines at the bottom of `schema.sql` instead.

### 4. Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com) → your project → **Authentication → Sign-in methods** → enable **Google**
2. Go to **Authentication → Settings → Authorized domains** → add `localhost`
3. Go to **Project Settings → Service accounts** → **Generate new private key** → save the downloaded `.json` file somewhere safe

### 5. Create a `.env` file

```env
# Database
DB_HOST=localhost
DB_NAME=lostaf
DB_USER=postgres
DB_PASS=your_postgres_password

# Firebase Admin SDK (path to the downloaded service account JSON)
FIREBASE_SERVICE_ACCOUNT=/path/to/serviceAccountKey.json

# CORS — set to your domain in production, leave as * for local dev
ALLOWED_ORIGINS=*
```

### 6. Run the server

```bash
python server.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DB_HOST` | Yes | PostgreSQL host (default: `localhost`) |
| `DB_NAME` | Yes | Database name (default: `lostaf`) |
| `DB_USER` | Yes | Database user (default: `postgres`) |
| `DB_PASS` | Yes | Database password |
| `FIREBASE_SERVICE_ACCOUNT` | Yes (prod) | Absolute path to Firebase service account JSON. Without this, token verification is disabled — **do not deploy without it** |
| `ALLOWED_ORIGINS` | Yes (prod) | CORS origin — set to your production domain, e.g. `https://lostaf.example.com` |
| `FLASK_DEBUG` | No | Set to `true` to enable Flask debug mode locally |

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/items` | No | List items. Query params: `type`, `category`, `location`, `search`, `status` |
| `POST` | `/api/items` | **Yes** | Create a new lost/found item report |
| `PUT` | `/api/items/:id/reunite` | **Yes** | Mark an item as reunited |
| `POST` | `/api/users/sync` | **Yes** | Upsert user record from Firebase session (called on every login) |
| `GET` | `/api/stats` | No | Returns total items, reunited count, and user count |

Protected endpoints require a valid Firebase ID token in the `Authorization: Bearer <token>` header. The backend also verifies the email domain server-side.

---

## Campus Zones

The campus map covers 15 filterable zones:
Pharmacy · BS Building · CS Building · EEE Block · ETC Block · CSE Lawn · Bosch COE · Mechanical · Mech Lawn · Civil Lawn · Temple Lawn · Library · Management · MBA Block · Main Gate

---

## Deployment Checklist

- [ ] `FIREBASE_SERVICE_ACCOUNT` is set to a valid service account JSON path on the server
- [ ] `ALLOWED_ORIGINS` is set to your production domain
- [ ] Production domain is added to Firebase Console → Authorized domains
- [ ] Database migration SQL has been run (if upgrading an existing DB)
- [ ] Server is running behind **HTTPS** (required by Firebase Auth)
- [ ] `FLASK_DEBUG` is not set (defaults to `false`)

---

## Built By

**Dipesh kumar** — B.Tech student, C. V. Raman Global University

Built because campus WhatsApp "Found in BS204" messages go ignored. Wanted something actually useful that doesn't look like a government website.

- GitHub: [@dipeshkmr09](https://github.com/dipeshkmr09)
- LinkedIn: [Dipesh Kumar](www.linkedin.com/in/dipesh-kumar-2b9a0a359)

---

## License

This project is intended for internal use at CGU. Not licensed for redistribution. But can be made for any campus exclusive.
