export class ApiError extends Error {
  constructor(mensaje, codigo, status) {
    super(mensaje);
    this.codigo = codigo;
    this.status = status;
  }
}

export async function api(path, { method = 'GET', body } = {}) {
  const headers = {};
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(data.mensaje || `Error ${response.status}`, data.codigo, response.status);
  }
  return data;
}
