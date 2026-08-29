import { createContext, useContext, useState, useCallback } from 'react';
import { api, guardarSesion, leerSesion, limpiarSesion } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(() => leerSesion());

  const login = useCallback(async (email, password, tipo) => {
    const data = await api('/auth/login', { method: 'POST', body: { email, password, tipo } });
    guardarSesion(data.tipo, data.id, data.token);
    setSesion({ tipo: data.tipo, id: data.id, token: data.token });
    return data;
  }, []);

  const registrarPerfil = useCallback(async (datos) => {
    const data = await api('/perfiles', { method: 'POST', body: datos });
    guardarSesion('perfil', data.perfil_id, data.token);
    setSesion({ tipo: 'perfil', id: data.perfil_id, token: data.token });
    return data;
  }, []);

  const registrarEmpresa = useCallback(async (datos) => {
    const data = await api('/empresas', { method: 'POST', body: datos });
    guardarSesion('empresa', data.empresa_id, data.token);
    setSesion({ tipo: 'empresa', id: data.empresa_id, token: data.token });
    return data;
  }, []);

  const logout = useCallback(() => {
    limpiarSesion();
    setSesion(null);
  }, []);

  return (
    <AuthContext.Provider value={{ sesion, login, registrarPerfil, registrarEmpresa, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}
