const TOKEN_KEY = 'rumbo_token';
const TIPO_KEY = 'rumbo_tipo';
const ID_KEY = 'rumbo_id';

export function guardarSesion(tipo, id, token) {
  localStorage.setItem(TIPO_KEY, tipo);
  localStorage.setItem(ID_KEY, id);
  localStorage.setItem(TOKEN_KEY, token);
}

export function limpiarSesion() {
  localStorage.removeItem(TIPO_KEY);
  localStorage.removeItem(ID_KEY);
  localStorage.removeItem(TOKEN_KEY);
}

export function leerSesion() {
  const tipo = localStorage.getItem(TIPO_KEY);
  const id = localStorage.getItem(ID_KEY);
  const token = localStorage.getItem(TOKEN_KEY);
  if (!tipo || !id || !token) return null;
  return { tipo, id, token };
}

export class ApiError extends Error {
  constructor(mensaje, codigo, status) {
    super(mensaje);
    this.codigo = codigo;
    this.status = status;
  }
}

export async function api(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const sesion = leerSesion();
    if (!sesion) throw new ApiError('No hay sesión activa', 'NO_AUTENTICADO', 401);
    headers.Authorization = `Bearer ${sesion.token}`;
  }
  const r = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new ApiError(data.mensaje || `Error ${r.status}`, data.codigo, r.status);
  }
  return data;
}
