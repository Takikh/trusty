# Telemedicine Backend — Project Documentation

> **Clinical Identity Verification API**
> A FastAPI backend providing JWT-based authentication, role-based access control (Doctor / Admin), email OTP verification, and integration with a Supabase-hosted verification pipeline.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Environment Variables](#environment-variables)
- [Setup & Installation](#setup--installation)
- [API Reference](#api-reference)
- [Authentication Flow](#authentication-flow)
- [Role-Based Access Control](#role-based-access-control)
- [Frontend Integration](#frontend-integration)
- [External Pipeline Integration](#external-pipeline-integration)

---

## Overview

This backend serves the **Telemedicine Client Portal** — a platform where doctors register, verify their identity through a multi-step pipeline, and receive admin approval before gaining full access. It acts as the authentication and authorization layer sitting between a React frontend and a shared Supabase PostgreSQL database.

### Key Features

- **2-Step Doctor Registration** — Email + OTP verification
- **3-Gate Login** — Password → Email verified → Admin approved
- **Admin Dashboard API** — View all doctors, approve/revoke access
- **Pipeline Integration** — Reads verification status from an external identity verification service
- **JWT Tokens** — Stateless authentication with HS256-signed tokens

---

## Architecture

```
┌──────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   React UI   │  HTTP   │  FastAPI Backend  │  REST   │    Supabase     │
│ (Vite :5173) │────────▶│   (Uvicorn :8000) │────────▶│   PostgreSQL    │
└──────────────┘         └──────────────────┘         └─────────────────┘
                                │                            ▲
                                │ JWT                        │
                                │                      ┌─────┴──────┐
                                └─────────────────────▶│  Identity   │
                                  reads verdict from   │  Verify     │
                                  doctors table        │  Pipeline   │
                                                       └────────────┘
```

- **Frontend** communicates with the backend via REST (JSON).
- **Backend** talks to Supabase via the PostgREST API (HTTP), not a direct PostgreSQL connection.
- An **external verification pipeline** independently writes to the `doctors` table. This backend only reads from it.

---

## Tech Stack

| Layer        | Technology                                   |
|-------------|----------------------------------------------|
| Framework   | **FastAPI** 0.136+                            |
| Server      | **Uvicorn** (ASGI)                            |
| Database    | **Supabase** (PostgreSQL) via PostgREST API   |
| DB Client   | **postgrest-py** (`SyncPostgrestClient`)      |
| Auth        | **python-jose** (JWT) + **bcrypt** (hashing)  |
| Validation  | **Pydantic** v2                               |
| Email       | **smtplib** (Gmail SMTP + TLS)                |
| HTTP Client | **httpx** (HTTP/1.1 forced)                   |
| Python      | 3.14+                                         |

---

## Project Structure

```
telemedicine-backend/
├── .env                        # Environment variables (git-ignored)
├── .gitignore
├── requirements.txt            # Python dependencies
├── auth_tables.sql             # SQL migration for users + verification_codes
├── postman_collection.json     # Postman collection for API testing
├── structure.sql               # Existing pipeline DB schema (reference)
│
├── app/
│   ├── __init__.py
│   ├── config.py               # Pydantic Settings — loads .env
│   ├── database.py             # Supabase PostgREST client singleton
│   ├── models.py               # (intentionally empty — Pydantic handles validation)
│   ├── auth.py                 # Password hashing, JWT, FastAPI dependencies
│   ├── email_service.py        # Gmail SMTP OTP sender
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── main.py                 # FastAPI app, CORS, router registration
│   ├── seed_admin.py           # CLI script to create admin user
│   └── routes/
│       ├── __init__.py
│       ├── auth_routes.py      # /api/auth/* — register, verify, login, me
│       └── admin_routes.py     # /api/admin/* — doctor list, approval toggle
│
└── telemedicine-client/        # React frontend (Vite)
    ├── design/                 # Shared CSS design system
    ├── src/
    │   ├── api.js              # Backend API utility (fetch wrapper)
    │   ├── App.jsx             # Router — all page routes
    │   ├── main.jsx            # Entry point
    │   ├── index.css           # Additional component styles
    │   └── pages/
    │       ├── RegisterPage.jsx
    │       ├── VerifyEmailPage.jsx
    │       ├── IdentityHandoffPage.jsx
    │       ├── LoginPage.jsx
    │       ├── DashboardPage.jsx
    │       └── AdminDashboardPage.jsx
    └── ...
```

---

## Database Schema

The backend owns **two tables** and reads from **one existing table**:

### `users` (owned by this backend)

| Column          | Type                     | Default        | Notes                     |
|----------------|--------------------------|----------------|---------------------------|
| `id`           | UUID PK                  | `uuid_generate_v4()` | Auto-generated       |
| `created_at`   | TIMESTAMPTZ              | `NOW()`        |                           |
| `updated_at`   | TIMESTAMPTZ              | `NOW()`        | Auto-updated via trigger  |
| `email`        | TEXT NOT NULL UNIQUE      |                | Indexed                   |
| `password_hash`| TEXT NOT NULL             |                | bcrypt hash               |
| `name`         | TEXT NOT NULL             |                | Display name              |
| `role`         | TEXT NOT NULL             | `'doctor'`     | `'doctor'` or `'admin'`   |
| `email_verified`| BOOLEAN NOT NULL         | `FALSE`        |                           |
| `admin_approved`| BOOLEAN NOT NULL         | `FALSE`        |                           |

### `verification_codes` (owned by this backend)

| Column       | Type              | Default              | Notes                 |
|-------------|-------------------|----------------------|-----------------------|
| `id`        | UUID PK           | `uuid_generate_v4()` |                       |
| `created_at`| TIMESTAMPTZ       | `NOW()`              |                       |
| `email`     | TEXT NOT NULL      |                      | Indexed               |
| `code`      | TEXT NOT NULL      |                      | 6-digit numeric       |
| `expires_at`| TIMESTAMPTZ       |                      | `NOW() + 10 minutes`  |
| `used`      | BOOLEAN NOT NULL   | `FALSE`              |                       |

### `doctors` (READ-ONLY — owned by external pipeline)

| Column              | Type          | Notes                                     |
|--------------------|---------------|--------------------------------------------|
| `id`               | UUID PK       |                                            |
| `email`            | TEXT          | **Links to `users.email`**                 |
| `name`             | TEXT          |                                            |
| `specialty`        | TEXT          |                                            |
| `declared_univ`    | TEXT          |                                            |
| `status`           | TEXT          | Pipeline state (pending → verdict_ready)   |
| `verdict`          | TEXT          | `VERIFIED`, `NEEDS_MANUAL_REVIEW`, `REJECTED` |
| `final_score`      | FLOAT         | Confidence score                           |
| `report_json`      | JSONB         | Full verification report                   |

> The backend **never writes** to the `doctors` table. It only reads `verdict` and `status` to show pipeline progress on the admin dashboard.

---

## Environment Variables

| Variable               | Required | Description                                |
|------------------------|----------|--------------------------------------------|
| `SUPABASE_URL`         | ✅       | Supabase project URL                       |
| `SUPABASE_KEY`         | ✅       | Supabase anon key (unused by backend, kept for reference) |
| `SUPABASE_SERVICE_KEY` | ✅       | Supabase service role key (bypasses RLS)   |
| `EMAIL_USERNAME`       | ✅       | Gmail address for sending OTPs             |
| `EMAIL_APP_PASSWORD`   | ✅       | Gmail App Password (16-char)               |
| `ADMIN_EMAIL`          | ✅       | Initial admin account email                |
| `ADMIN_PASSWORD`       | ✅       | Initial admin account password             |
| `JWT_SECRET`           | ✅       | Secret key for signing JWT tokens          |
| `JWT_ALGORITHM`        | ❌       | Default: `HS256`                           |
| `JWT_EXPIRY_MINUTES`   | ❌       | Default: `60`                              |

---

## Setup & Installation

### Prerequisites

- Python 3.14+
- Node.js 18+ (for frontend)
- A Supabase project with the `users` and `verification_codes` tables created

### 1. Install Python dependencies

```bash
py -3.14 -m pip install -r requirements.txt
```

### 2. Create database tables

Open the **Supabase SQL Editor** and run the contents of `auth_tables.sql`.

### 3. Configure environment

Copy `.env.example` or create `.env` with all required variables (see table above).

### 4. Seed the admin user

```bash
py -3.14 -m app.seed_admin
```

### 5. Start the backend

```bash
py -3.14 -m uvicorn app.main:app --reload --port 8000
```

### 6. Start the frontend

```bash
cd telemedicine-client
npm install
npm run dev
```

### 7. Access

| Service         | URL                            |
|----------------|--------------------------------|
| Backend API    | http://localhost:8000           |
| API Docs       | http://localhost:8000/docs      |
| Frontend       | http://localhost:5173           |

---

## API Reference

Base URL: `http://localhost:8000/api`

### Health

| Method | Endpoint       | Auth | Description      |
|--------|---------------|------|------------------|
| `GET`  | `/health`     | —    | Server health check |

**Response:** `{ "status": "ok", "service": "clinical-identity-verification" }`

---

### Auth Routes (`/api/auth`)

#### `POST /auth/register`

Create a new doctor account and send a 6-digit OTP to their email.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```

**Responses:**

| Status | Body | Condition |
|--------|------|-----------|
| `201`  | `{ "message": "Verification code sent to your email." }` | Success |
| `409`  | `{ "detail": "An account with this email already exists." }` | Duplicate email |
| `500`  | `{ "detail": "Failed to send verification email: ..." }` | SMTP error |

---

#### `POST /auth/verify-email`

Validate the 6-digit OTP and mark the user's email as verified.

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "code": "482916"
}
```

**Responses:**

| Status | Body | Condition |
|--------|------|-----------|
| `200`  | `{ "message": "Email verified successfully." }` | Valid code |
| `400`  | `{ "detail": "Invalid or expired verification code." }` | Wrong/expired code |
| `404`  | `{ "detail": "User not found." }` | No user with that email |

---

#### `POST /auth/login`

Authenticate with email and password. Three-gate check:
1. **Credentials** valid
2. **Email verified** (`email_verified = true`)
3. **Admin approved** (`admin_approved = true`, doctors only)

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "name": "John Doe",
    "role": "doctor",
    "email_verified": true,
    "admin_approved": true,
    "created_at": "2026-05-02T18:30:00Z"
  }
}
```

**Error Responses:**

| Status | Detail | Condition |
|--------|--------|-----------|
| `401`  | `"Invalid email or password."` | Bad credentials |
| `403`  | `"Please verify your email address first."` | Email not verified |
| `403`  | `"Account pending administrative approval."` | Not yet admin-approved |

---

#### `GET /auth/me`

Return the currently authenticated user's profile.

**Headers:** `Authorization: Bearer <token>`

**Response (200):** `UserResponse` object (same shape as `user` in login response)

**Error:** `401` if token is invalid/expired.

---

### Admin Routes (`/api/admin`)

> All admin routes require `Authorization: Bearer <admin_token>` where the token belongs to a user with `role = "admin"`.

#### `GET /admin/doctors`

Fetch all registered doctors, enriched with their pipeline verification status.

**Response (200):**
```json
[
  {
    "id": "550e8400-...",
    "email": "john.doe@example.com",
    "name": "John Doe",
    "email_verified": true,
    "admin_approved": false,
    "created_at": "2026-05-02T18:30:00Z",
    "pipeline_status": "verdict_ready",
    "verdict": "VERIFIED",
    "final_score": 0.95,
    "is_verified_by_service": true
  }
]
```

| Field                   | Source          | Description |
|------------------------|-----------------|-------------|
| `id` through `admin_approved` | `users` table | Auth data |
| `pipeline_status`      | `doctors` table | Pipeline stage |
| `verdict`              | `doctors` table | `VERIFIED` / `NEEDS_MANUAL_REVIEW` / `REJECTED` |
| `final_score`          | `doctors` table | Confidence score (0–1) |
| `is_verified_by_service` | Computed      | `true` when `verdict == "VERIFIED"` |

**Errors:** `401` (bad token), `403` (not admin)

---

#### `PATCH /admin/doctors/{user_id}/approval`

Toggle admin approval on a doctor's account.

**Request Body:**
```json
{ "admin_approved": true }
```

**Response (200):** Updated `UserResponse` object.

**Errors:** `404` (doctor not found), `401`/`403` (auth)

---

## Authentication Flow

```
Doctor                          Backend                        Supabase
  │                               │                               │
  │──── POST /auth/register ─────▶│                               │
  │                               │── insert users row ──────────▶│
  │                               │── insert verification_code ──▶│
  │                               │── send OTP email              │
  │◀──── 201 "Code sent" ────────│                               │
  │                               │                               │
  │──── POST /auth/verify-email ─▶│                               │
  │                               │── validate OTP ──────────────▶│
  │                               │── update email_verified=true ▶│
  │◀──── 200 "Email verified" ───│                               │
  │                               │                               │
  │──── POST /auth/login ────────▶│                               │
  │                               │── check password              │
  │                               │── check email_verified        │
  │                               │── check admin_approved        │
  │◀──── 403 "Pending approval" ─│                               │
  │                               │                               │
  │         ┌── Admin approves via PATCH /admin/doctors/{id} ──┐  │
  │         │                     │── update admin_approved ───┼─▶│
  │         └─────────────────────┘                            │  │
  │                               │                               │
  │──── POST /auth/login ────────▶│                               │
  │◀──── 200 + JWT token ────────│                               │
```

---

## Role-Based Access Control

| Role     | Permissions                                         |
|----------|-----------------------------------------------------|
| `doctor` | Register, verify email, login (after approval), access `/auth/me` |
| `admin`  | Login (bypasses `admin_approved` check), access `/admin/*` routes, approve/revoke doctors |

### JWT Payload

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "role": "doctor",
  "exp": 1746211200
}
```

### Dependency Chain

```python
get_current_user   →  Decodes JWT, fetches user from DB
    └── require_admin  →  Checks user.role == "admin"
```

---

## Frontend Integration

The React frontend communicates with the backend via `src/api.js`:

| Frontend Page           | API Call                         | Route          |
|------------------------|----------------------------------|----------------|
| `RegisterPage`         | `api.register()`                 | Register       |
| `VerifyEmailPage`      | `api.verifyEmail()`              | Verify OTP     |
| `LoginPage`            | `api.login()`                    | Login          |
| `DashboardPage`        | `api.getMe()`                    | Get profile    |
| `AdminDashboardPage`   | `api.getAdminDoctors()`          | List doctors   |
| `AdminDashboardPage`   | `api.updateDoctorApproval()`     | Toggle approval|

JWT tokens and user data are persisted in `localStorage` via `api.saveAuth()` / `api.getToken()`.

---

## External Pipeline Integration

The external **Identity Verification Pipeline** (identity-vaas) operates independently:

1. Doctor uploads credentials to the pipeline (via `IdentityHandoffPage`)
2. Pipeline processes documents, scrapes the web, conducts AI interview
3. Pipeline writes results to the `doctors` table (columns: `status`, `verdict`, `final_score`, `report_json`)
4. This backend **reads** those results when the admin views the doctor list
5. Admin sees both the pipeline verdict and can independently approve/reject

**Linkage:** The `users.email` field matches the `doctors.email` field — this is the only connection between the two systems.

**Important:** This backend never writes to the `doctors` table. The pipeline has full ownership of that table's data.
