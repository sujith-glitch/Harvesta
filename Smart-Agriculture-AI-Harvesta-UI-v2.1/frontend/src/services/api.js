import { requestChatTurn, resolveApiBase } from '../utils/chatRequest';

const API_BASE_URL = resolveApiBase(
  import.meta.env.VITE_API_BASE_URL,
  typeof window !== 'undefined' ? window.location : undefined,
  import.meta.env.DEV,
);
const IS_DEMO_ALLOWED = import.meta.env.VITE_ENABLE_DEMO_MODE === 'true';

const TOKEN_KEY = 'smart_agri_auth_token';
const DEMO_FLAG_KEY = 'smart_agri_demo_mode';
const SESSION_KEY = 'smart_agri_session_id';
export const DEMO_TOKEN = 'demo-token-no-backend';

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function clearAuthToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(DEMO_FLAG_KEY);
  localStorage.removeItem(SESSION_KEY);
}

export function getSessionId() {
  return localStorage.getItem(SESSION_KEY);
}

function setSessionId(sessionId) {
  if (sessionId) localStorage.setItem(SESSION_KEY, sessionId);
  else localStorage.removeItem(SESSION_KEY);
}

export function isDemoMode() {
  if (!IS_DEMO_ALLOWED) return false;
  return localStorage.getItem(DEMO_FLAG_KEY) === '1' || getAuthToken() === DEMO_TOKEN;
}

function enableDemoMode() {
  if (!IS_DEMO_ALLOWED) return;
  localStorage.setItem(DEMO_FLAG_KEY, '1');
  setAuthToken(DEMO_TOKEN);
  setSessionId('demo-session');
}

const wait = (ms) => new Promise((res) => setTimeout(res, ms));

/* ===================== DEMO MOCK DATA ===================== */
const DEMO_USER = {
  id: 1,
  email: 'demo.farmer@harvesta.app',
  full_name: 'Aanya Sharma',
  is_verified: true,
  created_at: '2026-07-12T08:24:00Z',
};

const DEMO_FARM = {
  id: 1,
  name: 'Greenfield Acres',
  location: 'Coimbatore',
  state: 'Tamil Nadu',
  size_acres: 18.5,
  created_at: '2026-07-12T08:30:00Z',
};

const DEMO_CROPS = [
  { id: 1, farm_id: 1, name: 'Basmati Rice', variety: 'Pusa 1121', planting_date: '2026-06-04', growth_stage: 'Tillering', health_status: 'healthy', days_to_harvest: 64, area_acres: 6.2, notes: 'Routine monitoring; field looks lush after last rain.' },
  { id: 2, farm_id: 1, name: 'Sweet Corn', variety: 'Sugar Bantam', planting_date: '2026-06-22', growth_stage: 'Vegetative', health_status: 'needs attention', days_to_harvest: 88, area_acres: 4.5, notes: 'Minor nitrogen deficiency noticed on northern rows.' },
  { id: 3, farm_id: 1, name: 'Tomato', variety: 'Heirloom Roma', planting_date: '2026-07-01', growth_stage: 'Flowering', health_status: 'healthy', days_to_harvest: 52, area_acres: 3.0, notes: 'Pollinator activity good; staking scheduled next week.' },
  { id: 4, farm_id: 1, name: 'Cotton', variety: 'Bt-Bunny', planting_date: '2026-05-18', growth_stage: 'Boll', health_status: 'critical', days_to_harvest: 35, area_acres: 4.8, notes: 'Bollworm pressure detected; scout daily.' },
];

const DEMO_SUMMARY = {
  total_analyses: 24,
  irrigation_required_count: 6,
  monitor_count: 8,
  no_irrigation_needed_count: 10,
  high_priority_count: 3,
  latest_analysis_timestamp: '2026-08-26T03:42:00Z',
};

const DEMO_HOME = {
  farm: DEMO_FARM,
  total_crops: DEMO_CROPS.length,
  overall_health_percent: 78,
  recent_crops: DEMO_CROPS.slice(0, 4).map((c) => ({ id: c.id, name: c.name, health_status: c.health_status })),
};

const DEMO_HISTORY = [
  {
    id: 1001,
    crop_type: 'Basmati Rice',
    location: 'Coimbatore, Tamil Nadu',
    created_at: '2026-08-26T03:42:00Z',
    weather: { temperature: 31.4, humidity: 72, rainfall: 4.2, description: 'Light rain' },
    soil: { moisture: 38.5, ph: 6.4, temperature: 27.1 },
    analysis: {
      status: 'IRRIGATION_REQUIRED',
      priority: 'HIGH',
      irrigation_volume_liters: 1240,
      soil_moisture_status: 'Below optimal',
      recommendation: 'Apply 1240 L/acre within the next 24 hours. Soil moisture is at 38.5% — below the 45% threshold for tillering rice.',
      risk_factors: ['Low rainfall in last 72h', 'High evapotranspiration forecast'],
      next_check_hours: 24,
    },
  },
  {
    id: 1002,
    crop_type: 'Sweet Corn',
    location: 'Coimbatore, Tamil Nadu',
    created_at: '2026-08-25T11:10:00Z',
    weather: { temperature: 28.7, humidity: 81, rainfall: 12.6, description: 'Cloudy' },
    soil: { moisture: 52.4, ph: 6.7, temperature: 25.9 },
    analysis: {
      status: 'MONITOR',
      priority: 'MEDIUM',
      irrigation_volume_liters: 0,
      soil_moisture_status: 'Adequate',
      recommendation: 'No irrigation needed for 48 hours. Watch for nitrogen deficiency on north rows.',
      risk_factors: ['Mild nutrient imbalance'],
      next_check_hours: 48,
    },
  },
  {
    id: 1003,
    crop_type: 'Cotton',
    location: 'Coimbatore, Tamil Nadu',
    created_at: '2026-08-24T16:05:00Z',
    weather: { temperature: 33.1, humidity: 58, rainfall: 0, description: 'Clear' },
    soil: { moisture: 29.8, ph: 6.5, temperature: 30.2 },
    analysis: {
      status: 'IRRIGATION_REQUIRED',
      priority: 'HIGH',
      irrigation_volume_liters: 2100,
      soil_moisture_status: 'Critical low',
      recommendation: 'Boll development stage needs urgent water. Apply 2100 L/acre today; bollworm scouting advised.',
      risk_factors: ['No rainfall last 5 days', 'Critical boll stage', 'Pest pressure'],
      next_check_hours: 12,
    },
  },
  {
    id: 1004,
    crop_type: 'Tomato',
    location: 'Coimbatore, Tamil Nadu',
    created_at: '2026-08-22T09:30:00Z',
    weather: { temperature: 27.6, humidity: 76, rainfall: 6.4, description: 'Showers' },
    soil: { moisture: 48.1, ph: 6.6, temperature: 26.0 },
    analysis: {
      status: 'NO_IRRIGATION_NEEDED',
      priority: 'LOW',
      irrigation_volume_liters: 0,
      soil_moisture_status: 'Optimal',
      recommendation: 'Field is healthy and well-watered. Re-check in 3 days.',
      risk_factors: [],
      next_check_hours: 72,
    },
  },
];

function mockFieldAnalysis(payload) {
  return {
    id: 1005,
    crop_type: payload.crop_type || 'Wheat',
    location: 'Coimbatore, Tamil Nadu',
    created_at: new Date().toISOString(),
    weather: { temperature: 30.2, humidity: 68, rainfall: 1.8, description: 'Partly cloudy' },
    soil: {
      moisture: Number(payload.current_soil_moisture) || 36.5,
      ph: Number(payload.soil_ph) || 6.4,
      temperature: Number(payload.soil_temperature) || 27.4,
    },
    analysis: {
      status: 'IRRIGATION_REQUIRED',
      priority: 'HIGH',
      irrigation_volume_liters: 980,
      soil_moisture_status: 'Below optimal',
      recommendation: `Apply 980 L/acre within 24h to bring soil moisture above the 45% threshold for ${payload.crop_type || 'your crop'}.`,
      risk_factors: ['Low recent rainfall', 'High evapotranspiration forecast'],
      next_check_hours: 24,
    },
  };
}

function mockIrrigation(payload) {
  return {
    id: 1006,
    crop_type: payload.crop_type || 'Wheat',
    created_at: new Date().toISOString(),
    weather: { temperature: Number(payload.temperature) || 30, humidity: Number(payload.humidity) || 65, rainfall: Number(payload.rainfall) || 2 },
    soil: { moisture: Number(payload.current_soil_moisture) || 36, ph: Number(payload.soil_ph) || 6.5, temperature: Number(payload.soil_temperature) || 27 },
    analysis: {
      status: 'IRRIGATION_REQUIRED',
      priority: 'MEDIUM',
      irrigation_volume_liters: 760,
      soil_moisture_status: 'Below optimal',
      recommendation: 'Apply 760 L/acre within the next 18 hours based on the manual inputs provided.',
      risk_factors: ['Manual weather inputs', 'Soil moisture below 40%'],
      next_check_hours: 18,
    },
  };
}

function getHeaders(extraHeaders = {}) {
  const headers = {
    'Accept': 'application/json',
    ...extraHeaders,
  };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse(response) {
  if (response.status === 401) {
    clearAuthToken();
    let detail = 'Session expired or unauthorized. Please log in again.';
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) detail = errJson.detail;
    } catch {
      // Fallback
    }
    const err = new Error(detail);
    err.isAuthError = true;
    err.status = 401;
    throw err;
  }

  if (response.status === 403) {
    let detail = 'Access forbidden. Verification required.';
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) detail = errJson.detail;
    } catch {
      // Fallback
    }
    const err = new Error(detail);
    err.isForbidden = true;
    err.status = 403;
    throw err;
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.detail) {
        if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorDetail = errorJson.detail.map(e => e.msg || e.detail).join('; ');
        }
      }
    } catch {
      // Fallback
    }
    const err = new Error(errorDetail);
    err.status = response.status;
    throw err;
  }

  return response.json();
}

/** Farmer Demo Login — only allowed when VITE_ENABLE_DEMO_MODE=true */
export async function demoLogin() {
  if (!IS_DEMO_ALLOWED) {
    throw new Error('Demo mode is disabled in this environment.');
  }
  await wait(280);
  enableDemoMode();
  return { access_token: DEMO_TOKEN, user: DEMO_USER };
}

/** Check backend health */
export async function checkHealth() {
  if (isDemoMode()) { await wait(150); return { status: 'ok' }; }
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Farmer Signup */
export async function signup(payload) {
  if (isDemoMode()) { await wait(280); return { access_token: DEMO_TOKEN, user: DEMO_USER }; }
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/** Farmer Login */
export async function login(payload) {
  // Demo bypass — only active when VITE_ENABLE_DEMO_MODE is explicitly enabled.
  if (IS_DEMO_ALLOWED && payload && (payload.email === 'demo' || payload.email === 'demo@harvesta.app' || payload.email === 'demo.farmer@harvesta.app')) {
    await wait(280);
    enableDemoMode();
    return { access_token: DEMO_TOKEN, user: DEMO_USER };
  }
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await handleResponse(response);
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  setSessionId(data.session_id || null);
  return data;
}

/** Verify the email link. Password creation happens on the original signup device. */
export async function verifyEmailToken(token) {
  const url = `${API_BASE_URL}/api/auth/verify-email`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ token }),
  });
  return handleResponse(response);
}

/** Recover the secure browser registration session after a refresh. */
export async function getRegistrationStatus(setupToken) {
  const response = await fetch(`${API_BASE_URL}/api/auth/registration-status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ setup_token: setupToken }),
  });
  return handleResponse(response);
}

/** Verify the four-digit code entered on the registration screen. */
export async function verifyRegistrationOtp(setupToken, code) {
  const response = await fetch(`${API_BASE_URL}/api/auth/verify-registration-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ setup_token: setupToken, code }),
  });
  return handleResponse(response);
}

/** Create the account password on the browser that started registration. */
export async function completeRegistration(setupToken, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/complete-registration`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ setup_token: setupToken, password }),
  });
  return handleResponse(response);
}

/** Resend Email Verification Code */
export async function resendVerificationEmail(email) {
  if (isDemoMode()) { await wait(280); return { message: 'Demo mode: verification email is not actually sent.' }; }
  const response = await fetch(`${API_BASE_URL}/api/auth/resend-verification`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ email }),
  });
  return handleResponse(response);
}

/** Request Password Reset Link */
export async function forgotPassword(email) {
  const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ email }),
  });
  return handleResponse(response);
}

/** Reset Password via token from reset email link */
export async function resetPassword(token, newPassword) {
  const response = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  return handleResponse(response);
}

/** Get Current User Profile */
export async function getMe() {
  if (isDemoMode()) { await wait(200); return DEMO_USER; }
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Keep server-side session duration accurate while the app is active. */
export async function sendSessionHeartbeat(currentView = 'dashboard') {
  if (isDemoMode()) return { status: 'ok', session_id: 'demo-session', current_view: currentView };
  const sessionId = getSessionId();
  if (!sessionId) return { status: 'skipped' };
  const response = await fetch(`${API_BASE_URL}/api/auth/session/heartbeat`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ session_id: sessionId, current_view: currentView }),
  });
  return handleResponse(response);
}

/** Close the server-side session before removing local credentials. */
export async function logout() {
  if (isDemoMode()) {
    clearAuthToken();
    return { status: 'success' };
  }
  const sessionId = getSessionId();
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ session_id: sessionId }),
    });
    return await handleResponse(response);
  } finally {
    clearAuthToken();
  }
}

/** Get Farmer Dashboard Summary Statistics */
export async function getDashboardSummary() {
  if (isDemoMode()) { await wait(200); return { ...DEMO_SUMMARY }; }
  const response = await fetch(`${API_BASE_URL}/api/dashboard/summary`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Get Farmer Analysis History */
export async function getAnalysisHistory(limit = 50, offset = 0) {
  if (isDemoMode()) { await wait(220); return DEMO_HISTORY.slice(offset, offset + limit); }
  const url = `${API_BASE_URL}/api/history/field-analysis?limit=${limit}&offset=${offset}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Get Single Analysis by ID */
export async function getAnalysisById(id) {
  if (isDemoMode()) { await wait(180); return DEMO_HISTORY.find((h) => h.id === Number(id)) || DEMO_HISTORY[0]; }
  const response = await fetch(`${API_BASE_URL}/api/history/field-analysis/${id}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Delete Single Analysis by ID */
export async function deleteAnalysis(id) {
  if (isDemoMode()) { await wait(180); return { success: true, id }; }
  const response = await fetch(`${API_BASE_URL}/api/history/field-analysis/${id}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Request AI Field Analysis (Authenticated & Saved) */
export async function getFieldAnalysis(payload) {
  if (isDemoMode()) { await wait(900); return mockFieldAnalysis(payload); }
  const response = await fetch(`${API_BASE_URL}/api/ai/field-analysis`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      crop_type: String(payload.crop_type),
      current_soil_moisture: Number(payload.current_soil_moisture),
      soil_ph: Number(payload.soil_ph),
      soil_temperature: Number(payload.soil_temperature),
    }),
  });
  return handleResponse(response);
}

/** Request Irrigation Recommendation (Manual inputs, Phase 6) */
export async function getIrrigationRecommendation(payload) {
  if (isDemoMode()) { await wait(900); return mockIrrigation(payload); }
  const response = await fetch(`${API_BASE_URL}/api/ai/irrigation-recommendation`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      crop_type: String(payload.crop_type),
      temperature: Number(payload.temperature),
      humidity: Number(payload.humidity),
      rainfall: Number(payload.rainfall),
      current_soil_moisture: Number(payload.current_soil_moisture),
      soil_ph: Number(payload.soil_ph),
      soil_temperature: Number(payload.soil_temperature),
    }),
  });
  return handleResponse(response);
}

/* ===================== Farm Management (Phase 2) ===================== */

/** Get Authenticated User's Home Overview (farm, crops, harvests, analyses) */
export async function getDashboardHome() {
  if (isDemoMode()) { await wait(220); return { ...DEMO_HOME }; }
  const response = await fetch(`${API_BASE_URL}/api/dashboard/home`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** List Farms owned by the authenticated user */
export async function getFarms() {
  if (isDemoMode()) { await wait(220); return [{ ...DEMO_FARM }]; }
  const response = await fetch(`${API_BASE_URL}/api/farms`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Get a single Farm by ID */
export async function getFarm(farmId) {
  if (isDemoMode()) { await wait(200); return { ...DEMO_FARM, id: Number(farmId) || DEMO_FARM.id }; }
  const response = await fetch(`${API_BASE_URL}/api/farms/${farmId}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Create a Farm */
export async function createFarm(payload) {
  if (isDemoMode()) { await wait(320); return { ...DEMO_FARM, ...payload, id: 99 }; }
  const response = await fetch(`${API_BASE_URL}/api/farms`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/** Update a Farm */
export async function updateFarm(farmId, payload) {
  if (isDemoMode()) { await wait(320); return { ...DEMO_FARM, ...payload, id: Number(farmId) || DEMO_FARM.id }; }
  const response = await fetch(`${API_BASE_URL}/api/farms/${farmId}`, {
    method: 'PUT',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/** Delete a Farm (cascades its crops) */
export async function deleteFarm(farmId) {
  if (isDemoMode()) { await wait(320); return { success: true, id: Number(farmId) }; }
  const response = await fetch(`${API_BASE_URL}/api/farms/${farmId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** List Crops in a Farm */
export async function getFarmCrops(farmId) {
  if (isDemoMode()) { await wait(220); return DEMO_CROPS.map((c) => ({ ...c, farm_id: Number(farmId) || c.farm_id })); }
  const response = await fetch(`${API_BASE_URL}/api/farms/${farmId}/crops`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Get a single Crop by ID */
export async function getCrop(cropId) {
  if (isDemoMode()) { await wait(200); return DEMO_CROPS.find((c) => c.id === Number(cropId)) || { ...DEMO_CROPS[0], id: Number(cropId) }; }
  const response = await fetch(`${API_BASE_URL}/api/crops/${cropId}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Add a Crop to a Farm */
export async function createCrop(farmId, payload) {
  if (isDemoMode()) { await wait(320); return { ...DEMO_CROPS[0], ...payload, id: 99, farm_id: Number(farmId) }; }
  const response = await fetch(`${API_BASE_URL}/api/farms/${farmId}/crops`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/** Update a Crop */
export async function updateCrop(cropId, payload) {
  if (isDemoMode()) { await wait(320); return { ...DEMO_CROPS[0], ...payload, id: Number(cropId) }; }
  const response = await fetch(`${API_BASE_URL}/api/crops/${cropId}`, {
    method: 'PUT',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/** Delete a Crop */
export async function deleteCrop(cropId) {
  if (isDemoMode()) { await wait(320); return { success: true, id: Number(cropId) }; }
  const response = await fetch(`${API_BASE_URL}/api/crops/${cropId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/* ===================== ADMIN & COMPANY ANALYTICS ===================== */

/** Fetch executive overview analytics (requires role='admin') */
export async function getAdminOverview() {
  const response = await fetch(`${API_BASE_URL}/api/admin/overview`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Fetch registered users list with activity context (requires role='admin') */
export async function getAdminUsers({ limit = 50, offset = 0, search = '', role = '' } = {}) {
  const params = new URLSearchParams();
  if (limit) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));
  if (search) params.set('search', search);
  if (role) params.set('role', role);

  const qs = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/admin/users${qs}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Fetch paginated activity telemetry events (requires role='admin') */
export async function getAdminActivity({ limit = 50, offset = 0, feature = '', event_name = '' } = {}) {
  const params = new URLSearchParams();
  if (limit) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));
  if (feature) params.set('feature', feature);
  if (event_name) params.set('event_name', event_name);

  const qs = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/admin/activity${qs}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Fetch paginated audit logs (requires role='admin') */
export async function getAdminAuditLogs({ limit = 50, offset = 0, action = '' } = {}) {
  const params = new URLSearchParams();
  if (limit) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));
  if (action) params.set('action', action);

  const qs = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/admin/audit-logs${qs}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Fetch paginated user sessions telemetry (requires role='admin') */
export async function getAdminSessions({ limit = 50, offset = 0, active_only = false } = {}) {
  const params = new URLSearchParams();
  if (limit) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));
  if (active_only) params.set('active_only', 'true');

  const qs = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/admin/sessions${qs}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** List every admin-visible database dataset and its current row count. */
export async function getAdminDataInventory() {
  const response = await fetch(`${API_BASE_URL}/api/admin/data-inventory`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Browse a secret-safe, paginated company dataset. */
export async function getAdminDataset(dataset, { limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  const response = await fetch(`${API_BASE_URL}/api/admin/data/${encodeURIComponent(dataset)}?${params.toString()}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/* ===================== PHYSICAL FARM SENSORS ===================== */

export async function getSensorReadings({ farm_id = '', device_id = '', limit = 100, offset = 0 } = {}) {
  if (isDemoMode()) return { total: 0, readings: [], limit, offset };
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (farm_id) params.set('farm_id', String(farm_id));
  if (device_id) params.set('device_id', String(device_id));
  const response = await fetch(`${API_BASE_URL}/api/sensors/readings?${params.toString()}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

export async function getSensorDevices() {
  if (isDemoMode()) return { total: 0, devices: [] };
  const response = await fetch(`${API_BASE_URL}/api/sensors/devices`, { method: 'GET', headers: getHeaders() });
  return handleResponse(response);
}

export async function registerSensorDevice(payload) {
  const response = await fetch(`${API_BASE_URL}/api/sensors/devices`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/* ===================== NOTIFICATIONS & FARM ALERTS (PHASE C) ===================== */

const DEMO_NOTIFICATIONS = [
  {
    id: 901,
    type: 'IRRIGATION_ALERT',
    title: 'High-priority irrigation alert: Basmati Rice',
    message: 'Field analysis for Basmati Rice indicates irrigation required. Soil moisture is at 38.5% — below the 45% threshold for tillering rice.',
    is_read: false,
    delivery_channel: 'BOTH',
    delivery_status: 'DELIVERED',
    created_at: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
    read_at: null,
  },
  {
    id: 902,
    type: 'WEATHER',
    title: 'Farm weather advisory: High temperature warning',
    message: 'Current temperature of 38.4°C exceeds 38°C threshold. Monitor soil evapotranspiration and crop heat stress.',
    is_read: false,
    delivery_channel: 'IN_APP',
    delivery_status: 'DELIVERED',
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
    read_at: null,
  },
  {
    id: 903,
    type: 'SECURITY',
    title: 'Email address verified',
    message: 'Your email address has been verified successfully. Your Harvesta farmer account is fully active.',
    is_read: true,
    delivery_channel: 'IN_APP',
    delivery_status: 'DELIVERED',
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    read_at: new Date(Date.now() - 1000 * 60 * 60 * 22).toISOString(),
  },
];

let demoNotifList = [...DEMO_NOTIFICATIONS];
let demoNotifPrefs = {
  id: 1,
  user_id: 1,
  email_enabled: true,
  irrigation_alerts: true,
  disease_alerts: true,
  security_alerts: true,
  weather_alerts: true,
};

/** Get Authenticated Farmer Notifications (paginated) */
export async function getNotifications({ limit = 50, offset = 0, unread_only = false } = {}) {
  if (isDemoMode()) {
    await wait(180);
    const filtered = unread_only ? demoNotifList.filter((n) => !n.is_read) : demoNotifList;
    const unreadCount = demoNotifList.filter((n) => !n.is_read).length;
    return {
      total: filtered.length,
      unread_count: unreadCount,
      limit,
      offset,
      notifications: filtered.slice(offset, offset + limit),
    };
  }

  const params = new URLSearchParams();
  if (limit) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));
  if (unread_only) params.set('unread_only', 'true');

  const qs = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/notifications${qs}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Get unread notification count */
export async function getUnreadNotificationCount() {
  if (isDemoMode()) {
    await wait(100);
    const count = demoNotifList.filter((n) => !n.is_read).length;
    return { unread_count: count };
  }

  const response = await fetch(`${API_BASE_URL}/api/notifications/unread-count`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Mark single notification as read */
export async function markNotificationRead(notificationId) {
  if (isDemoMode()) {
    await wait(120);
    const item = demoNotifList.find((n) => n.id === Number(notificationId));
    if (item) {
      item.is_read = true;
      item.read_at = new Date().toISOString();
    }
    return item || { id: notificationId, is_read: true };
  }

  const response = await fetch(`${API_BASE_URL}/api/notifications/${notificationId}/read`, {
    method: 'PATCH',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Mark all notifications as read */
export async function markAllNotificationsRead() {
  if (isDemoMode()) {
    await wait(150);
    let count = 0;
    demoNotifList.forEach((n) => {
      if (!n.is_read) {
        n.is_read = true;
        n.read_at = new Date().toISOString();
        count++;
      }
    });
    return { status: 'success', updated_count: count, message: `Marked ${count} notifications as read.` };
  }

  const response = await fetch(`${API_BASE_URL}/api/notifications/mark-all-read`, {
    method: 'POST',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Get farmer notification preferences */
export async function getNotificationPreferences() {
  if (isDemoMode()) {
    await wait(150);
    return { ...demoNotifPrefs };
  }

  const response = await fetch(`${API_BASE_URL}/api/notifications/preferences`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Update farmer notification preferences */
export async function updateNotificationPreferences(payload) {
  if (isDemoMode()) {
    await wait(200);
    demoNotifPrefs = { ...demoNotifPrefs, ...payload };
    return { ...demoNotifPrefs };
  }

  const response = await fetch(`${API_BASE_URL}/api/notifications/preferences`, {
    method: 'PUT',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/* ===================== CROP DISEASE VISION AI (PHASE D) ===================== */

const DEMO_DISEASE_SCANS = [
  {
    id: 101,
    predicted_crop: 'Tomato',
    predicted_disease: 'Early Blight',
    display_name: 'Tomato Early Blight (Alternaria solani)',
    confidence: 0.9125,
    is_healthy: false,
    urgency: 'MEDIUM',
    model_version: 'harvesta-disease-vision-v1.0',
    recommendation: 'Prune and safely destroy heavily infected lower leaves. Avoid overhead irrigation. Apply organic mulch around plant bases.',
    recommendations: [
      'Prune and safely destroy heavily infected lower leaves.',
      'Avoid overhead irrigation; water at soil level to minimize leaf wetness duration.',
      'Apply organic mulch around plant bases to prevent soil-to-leaf spore splash.',
    ],
    description: 'Characterized by concentric ringed brown lesions on older leaves.',
    top_predictions: [
      { class_key: 'Tomato___Early_Blight', label: 'Tomato Early Blight', confidence: 0.9125 },
      { class_key: 'Tomato___Late_Blight', label: 'Tomato Late Blight', confidence: 0.0540 },
      { class_key: 'Tomato___Leaf_Mold', label: 'Tomato Leaf Mold', confidence: 0.0210 },
    ],
    disclaimer: 'Smart Agriculture AI Harvesta crop disease screening is an AI assistance tool for early symptom identification. Always verify with a certified agronomist.',
    image_path: 'uploads/disease_scans/demo_leaf_01.jpg',
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
  },
];

let demoDiseaseList = [...DEMO_DISEASE_SCANS];

/** Upload and screen a crop leaf image for disease diagnosis */
export async function scanCropDisease(formData) {
  if (isDemoMode()) {
    await wait(1200);
    const mockResult = {
      id: Date.now(),
      scan_id: Date.now(),
      predicted_crop: 'Tomato',
      predicted_disease: 'Early Blight',
      display_name: 'Tomato Early Blight (Alternaria solani)',
      confidence: 0.8842,
      is_healthy: false,
      urgency: 'MEDIUM',
      model_version: 'harvesta-disease-vision-v1.0',
      recommendation: 'Prune infected lower leaves and water at soil level to minimize foliar wetness.',
      recommendations: [
        'Prune and destroy heavily infected lower leaves.',
        'Avoid overhead irrigation to minimize leaf wetness.',
        'Apply organic mulch around plant bases.',
      ],
      description: 'Concentric ringed brown lesions observed.',
      top_predictions: [
        { class_key: 'Tomato___Early_Blight', label: 'Tomato Early Blight', confidence: 0.8842 },
        { class_key: 'Tomato___Leaf_Mold', label: 'Tomato Leaf Mold', confidence: 0.0712 },
        { class_key: 'Tomato___Healthy', label: 'Healthy Tomato Leaf', confidence: 0.0446 },
      ],
      disclaimer: 'AI screening guidance. Always consult a local agricultural specialist.',
      image_path: 'uploads/disease_scans/demo_leaf_01.jpg',
      created_at: new Date().toISOString(),
    };
    demoDiseaseList.unshift(mockResult);
    return mockResult;
  }

  // Use getHeaders without Content-Type so browser sets correct multipart boundary
  const headers = {};
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  headers['Accept'] = 'application/json';

  const response = await fetch(`${API_BASE_URL}/api/ai/disease-scan`, {
    method: 'POST',
    headers,
    body: formData,
  });
  return handleResponse(response);
}

/** Get paginated list of crop disease scans */
export async function getDiseaseScans({ limit = 50, offset = 0, farm_id, crop_id } = {}) {
  if (isDemoMode()) {
    await wait(180);
    return {
      total: demoDiseaseList.length,
      limit,
      offset,
      scans: demoDiseaseList.slice(offset, offset + limit),
    };
  }

  const params = new URLSearchParams();
  if (limit) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));
  if (farm_id) params.set('farm_id', String(farm_id));
  if (crop_id) params.set('crop_id', String(crop_id));

  const qs = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/disease-scans${qs}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Get single disease scan by ID */
export async function getDiseaseScan(scanId) {
  if (isDemoMode()) {
    await wait(150);
    const item = demoDiseaseList.find((s) => s.id === Number(scanId)) || demoDiseaseList[0];
    return item;
  }

  const response = await fetch(`${API_BASE_URL}/api/disease-scans/${scanId}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Delete disease scan by ID */
export async function deleteDiseaseScan(scanId) {
  if (isDemoMode()) {
    await wait(180);
    demoDiseaseList = demoDiseaseList.filter((s) => s.id !== Number(scanId));
    return { status: 'success', id: scanId };
  }

  const response = await fetch(`${API_BASE_URL}/api/disease-scans/${scanId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/* ===================== REAL AI AGRONOMIST CHAT (PHASE E) ===================== */

const DEMO_CHAT_CONVERSATIONS = [
  {
    id: 1,
    title: 'Tomato Irrigation & Blight Guidance',
    farm_id: 1,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
  },
];

const DEMO_CHAT_MESSAGES = {
  1: [
    {
      id: 1,
      conversation_id: 1,
      role: 'user',
      content: 'How should I adjust my watering given the recent humidity and early blight scan?',
      model_name: null,
      created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    },
    {
      id: 2,
      conversation_id: 1,
      role: 'assistant',
      content:
        'Based on your registered **Tomato** plot and recent **Early Blight** detection:\n\n' +
        '1. **Switch Watering Timing**: Irrigate early in the morning so sun and air circulation dry foliage before evening.\n' +
        '2. **Ground-Level Application**: Use drip lines or root-zone watering instead of overhead sprinklers to prevent fungal spore splash.\n' +
        '3. **Pruning**: Remove infected lower leaves touching soil.\n' +
        '4. **Soil Moisture Target**: Maintain 55–65% soil moisture to prevent root stress while keeping the canopy dry.',
      model_name: 'qwen2.5-coder:7b (demo)',
      created_at: new Date(Date.now() - 1000 * 60 * 29).toISOString(),
    },
  ],
};

let demoConversations = [...DEMO_CHAT_CONVERSATIONS];
let demoMessagesMap = { ...DEMO_CHAT_MESSAGES };

/** Create a new AI chat conversation */
export async function createChatConversation({ title = 'New Conversation', farm_id = null } = {}) {
  if (isDemoMode()) {
    await wait(200);
    const newConv = {
      id: Date.now(),
      title: title || 'New Conversation',
      farm_id,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    demoConversations.unshift(newConv);
    demoMessagesMap[newConv.id] = [];
    return newConv;
  }

  const response = await fetch(`${API_BASE_URL}/api/chat/conversations`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ title, farm_id }),
  });
  return handleResponse(response);
}

/** Get list of chat conversations */
export async function getChatConversations({ limit = 20, offset = 0 } = {}) {
  if (isDemoMode()) {
    await wait(150);
    return {
      total: demoConversations.length,
      limit,
      offset,
      conversations: demoConversations.slice(offset, offset + limit),
    };
  }

  const params = new URLSearchParams();
  if (limit) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));

  const qs = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/chat/conversations${qs}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Get a conversation and its messages thread */
export async function getChatConversation(conversationId) {
  if (isDemoMode()) {
    await wait(150);
    const conv = demoConversations.find((c) => c.id === Number(conversationId)) || demoConversations[0];
    const messages = demoMessagesMap[conversationId] || [];
    return { conversation: conv, messages };
  }

  const response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Delete a chat conversation */
export async function deleteChatConversation(conversationId) {
  if (isDemoMode()) {
    await wait(180);
    demoConversations = demoConversations.filter((c) => c.id !== Number(conversationId));
    delete demoMessagesMap[conversationId];
    return { status: 'success', id: conversationId };
  }

  const response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

/** Send message to AI Agronomist */
export async function sendChatMessage(conversationId, message, { signal } = {}) {
  if (isDemoMode()) {
    if (!conversationId) conversationId = (await createChatConversation({ title: message.slice(0, 45) })).id;
    const userMsg = {
      id: Date.now(),
      conversation_id: Number(conversationId),
      role: 'user',
      content: message,
      model_name: null,
      created_at: new Date().toISOString(),
    };
    const asstMsg = {
      id: Date.now() + 1,
      conversation_id: Number(conversationId),
      role: 'assistant',
      content: `Here is agricultural guidance for your query: "${message}". In precision farming, maintaining steady root-zone moisture and adequate canopy aeration is key to maximizing crop yield.`,
      model_name: 'qwen2.5-coder:7b (demo)',
      created_at: new Date().toISOString(),
    };

    if (!demoMessagesMap[conversationId]) {
      demoMessagesMap[conversationId] = [];
    }
    demoMessagesMap[conversationId].push(userMsg, asstMsg);

    const conv = demoConversations.find((c) => c.id === Number(conversationId));
    if (conv) {
      conv.updated_at = new Date().toISOString();
      if (conv.title === 'New Conversation' || !conv.title) {
        conv.title = message.slice(0, 45);
      }
    }

    return {
      user_message: userMsg,
      assistant_message: asstMsg,
      conversation: conv,
    };
  }

  const response = await requestChatTurn({
    url: `${API_BASE_URL}/api/chat/messages`,
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    conversationId, message, signal,
  });
  return handleResponse(response);
}

/* ===================== PROFILE & APPLICATION PREFERENCES ===================== */

export async function getProfile() {
  const response = await fetch(`${API_BASE_URL}/api/account/profile`, {
    method: 'GET', headers: getHeaders(),
  });
  return handleResponse(response);
}

export async function updateProfile(payload) {
  const response = await fetch(`${API_BASE_URL}/api/account/profile`, {
    method: 'PUT',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

export async function getAppPreferences() {
  const response = await fetch(`${API_BASE_URL}/api/account/preferences`, {
    method: 'GET', headers: getHeaders(),
  });
  return handleResponse(response);
}

export async function updateAppPreferences(payload) {
  const response = await fetch(`${API_BASE_URL}/api/account/preferences`, {
    method: 'PUT',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/* ===================== FARM INVENTORY ===================== */

export async function getInventory({ category = '', low_stock_only = false } = {}) {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  if (low_stock_only) params.set('low_stock_only', 'true');
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/api/inventory${suffix}`, {
    method: 'GET', headers: getHeaders(),
  });
  return handleResponse(response);
}

export async function createInventoryItem(payload) {
  const response = await fetch(`${API_BASE_URL}/api/inventory`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

export async function updateInventoryItem(itemId, payload) {
  const response = await fetch(`${API_BASE_URL}/api/inventory/${itemId}`, {
    method: 'PUT',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

export async function deleteInventoryItem(itemId) {
  const response = await fetch(`${API_BASE_URL}/api/inventory/${itemId}`, {
    method: 'DELETE', headers: getHeaders(),
  });
  return handleResponse(response);
}

/* ===================== FARMER REPORTS ===================== */

export async function getReports() {
  const response = await fetch(`${API_BASE_URL}/api/reports`, {
    method: 'GET', headers: getHeaders(),
  });
  return handleResponse(response);
}

export async function getReport(reportKey) {
  const response = await fetch(`${API_BASE_URL}/api/reports/${encodeURIComponent(reportKey)}`, {
    method: 'GET', headers: getHeaders(),
  });
  return handleResponse(response);
}

export async function downloadReport(reportKey, format = 'pdf') {
  const response = await fetch(
    `${API_BASE_URL}/api/reports/${encodeURIComponent(reportKey)}/download?format=${encodeURIComponent(format)}`,
    { method: 'GET', headers: getHeaders() },
  );
  if (!response.ok) return handleResponse(response);
  const disposition = response.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename="?([^";]+)"?/i);
  return {
    blob: await response.blob(),
    filename: match?.[1] || `harvesta-${reportKey}.${format}`,
  };
}
