import { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api';

const AuthContext = createContext(null);

function buildSession(data) {
  if (!data?.id || !data?.tipo) return null;
  return { id: data.id, tipo: data.tipo };
}

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(null);
  const [cargandoSesion, setCargandoSesion] = useState(true);

  useEffect(() => {
    let activa = true;

    async function bootstrap() {
      try {
        const data = await api('/auth/session');
        if (activa) setSesion(buildSession(data));
      } catch {
        if (activa) setSesion(null);
      } finally {
        if (activa) setCargandoSesion(false);
      }
    }

    bootstrap();
    return () => {
      activa = false;
    };
  }, []);

  async function login(email, password, tipo) {
    const data = await api('/auth/login', { method: 'POST', body: { email, password, tipo } });
    const nextSession = buildSession(data);
    setSesion(nextSession);
    return data;
  }

  async function registrarPerfil(datos) {
    const data = await api('/perfiles', { method: 'POST', body: datos });
    const nextSession = buildSession({ id: data.perfil_id, tipo: data.tipo });
    setSesion(nextSession);
    return data;
  }

  async function registrarEmpresa(datos) {
    const data = await api('/empresas', { method: 'POST', body: datos });
    const nextSession = buildSession({ id: data.empresa_id, tipo: data.tipo });
    setSesion(nextSession);
    return data;
  }

  async function logout() {
    try {
      await api('/auth/logout', { method: 'POST' });
    } finally {
      setSesion(null);
    }
  }

  return (
    <AuthContext.Provider value={{ sesion, cargandoSesion, login, registrarPerfil, registrarEmpresa, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}
