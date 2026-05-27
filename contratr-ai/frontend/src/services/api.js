const API = import.meta.env.VITE_API_URL || 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev';
const TIMEOUT = 30000;

let authToken = null;

export function setToken(token) { authToken = token; }
export function getToken() { return authToken; }
export function clearToken() { authToken = null; }

async function apiFetch(url, options = {}) {
  const ctrl = new AbortController();
  const tid = setTimeout(() => ctrl.abort(), TIMEOUT);
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

  try {
    const r = await fetch(url, { ...options, signal: ctrl.signal, headers });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new ApiError(err.error || `HTTP ${r.status}`, r.status);
    }
    return r.json();
  } catch (e) {
    if (e.name === 'AbortError') throw new ApiError('Timeout', 408);
    if (e instanceof ApiError) throw e;
    throw new ApiError('Erro de conexão', 0);
  } finally { clearTimeout(tid); }
}

class ApiError extends Error {
  constructor(message, statusCode) {
    super(message); this.name = 'ApiError'; this.statusCode = statusCode;
  }
}

// Auth
export async function login(email, password) {
  const data = await apiFetch(`${API}/auth/login`, {
    method: 'POST', body: JSON.stringify({ email, password }),
  });
  authToken = data.token;
  return data;
}

// Companies
export async function listCompanies() {
  return apiFetch(`${API}/companies`);
}
export async function createCompany(data) {
  return apiFetch(`${API}/companies`, { method: 'POST', body: JSON.stringify(data) });
}
export async function getCompany(id) {
  return apiFetch(`${API}/companies/${id}`);
}
export async function deleteCompany(id) {
  return apiFetch(`${API}/companies/${id}`, { method: 'DELETE' });
}

// Policies
export async function addPolicy(companyId, policy) {
  return apiFetch(`${API}/companies/${companyId}/policies`, {
    method: 'POST', body: JSON.stringify(policy),
  });
}
export async function removePolicy(companyId, policyId) {
  return apiFetch(`${API}/companies/${companyId}/policies/${policyId}`, { method: 'DELETE' });
}

// Contracts
export async function requestUpload(file, companyId) {
  return apiFetch(`${API}/contracts/upload`, {
    method: 'POST',
    body: JSON.stringify({ filename: file.name, file_size: file.size, company_id: companyId }),
  });
}
export async function uploadToS3(url, file) {
  const r = await fetch(url, {
    method: 'PUT', body: file,
    headers: { 'Content-Type': 'application/pdf', 'x-amz-server-side-encryption': 'AES256' },
  });
  if (!r.ok) throw new ApiError('Upload falhou', r.status);
}
export async function getAnalysis(id) {
  return apiFetch(`${API}/contracts/${id}`);
}
export async function pollAnalysis(id, onProgress, max = 60) {
  for (let i = 0; i < max; i++) {
    const r = await getAnalysis(id);
    if (onProgress) onProgress(r);
    if (['completed', 'error'].includes(r.status)) {
      if (r.status === 'error') throw new ApiError(r.error_message || 'Erro', 500);
      return r;
    }
    await new Promise(res => setTimeout(res, i < 10 ? 2000 : 5000));
  }
  throw new ApiError('Timeout na análise', 408);
}

export { ApiError };

// Analysis History
export async function getAnalysisHistory(companyId, status = null) {
  const params = status ? `?status=${status}` : '';
  return apiFetch(`${API}/companies/${companyId}/analyses${params}`);
}

// Bulk Policies Import
export async function importPoliciesBulk(companyId, text, autoSave = false) {
  return apiFetch(`${API}/companies/${companyId}/policies/bulk`, {
    method: 'POST',
    body: JSON.stringify({ text, auto_save: autoSave }),
  });
}

// Save bulk-reviewed policies one by one
export async function saveBulkPolicies(companyId, policies) {
  const results = [];
  for (const p of policies) {
    const r = await addPolicy(companyId, {
      rule: p.rule,
      category: p.category,
      severity: p.severity,
    });
    results.push(r);
  }
  return results;
}

// Public Demo (no auth)
export async function getDemoInfo() {
  return apiFetch(`${API}/demo/info`);
}
export async function getDemoSteps() {
  return apiFetch(`${API}/demo/steps`);
}
export async function startDemoAnalysis(file) {
  return apiFetch(`${API}/demo/analyze`, {
    method: 'POST',
    body: JSON.stringify({ filename: file.name, file_size: file.size }),
  });
}

// External API
export async function externalGetAnalysis(analysisId, apiKey) {
  return apiFetch(`${API}/api/v1/analysis/${analysisId}`, {
    headers: { 'X-API-Key': apiKey },
  });
}
export async function externalStartAnalysis(filename, companyId, apiKey) {
  return apiFetch(`${API}/api/v1/analyze`, {
    method: 'POST',
    headers: { 'X-API-Key': apiKey },
    body: JSON.stringify({ filename, company_id: companyId }),
  });
}
