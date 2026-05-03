/**
 * API utility module — all backend communication goes through here.
 *
 * Every function returns the parsed JSON response or throws an error
 * with the `detail` message from the backend.
 */

const BASE_URL = "http://localhost:8000/api";

// ── Helpers ──────────────────────────────────────────────────────────────

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(method, path, { body = null, token = null } = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...authHeaders(token),
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const message =
      data?.detail || `Request failed with status ${res.status}`;
    const err = new Error(message);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

// ── Auth ─────────────────────────────────────────────────────────────────

export function register({ firstName, lastName, email, password }) {
  return request("POST", "/auth/register", {
    body: { first_name: firstName, last_name: lastName, email, password },
  });
}

export function verifyEmail({ email, code }) {
  return request("POST", "/auth/verify-email", {
    body: { email, code },
  });
}

export function login({ email, password }) {
  return request("POST", "/auth/login", {
    body: { email, password },
  });
}

export function getMe(token) {
  return request("GET", "/auth/me", { token });
}

// ── Admin ────────────────────────────────────────────────────────────────

export function getAdminDoctors(token) {
  return request("GET", "/admin/doctors", { token });
}

export function updateDoctorApproval(token, userId, adminApproved) {
  return request("PATCH", `/admin/doctors/${userId}/approval`, {
    body: { admin_approved: adminApproved },
    token,
  });
}

// ── Token persistence ────────────────────────────────────────────────────

export function saveAuth(tokenResponse) {
  localStorage.setItem("token", tokenResponse.access_token);
  localStorage.setItem("user", JSON.stringify(tokenResponse.user));
}

export function getToken() {
  return localStorage.getItem("token");
}

export function getStoredUser() {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

export function clearAuth() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}
