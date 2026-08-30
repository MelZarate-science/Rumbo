import { Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Auth from './pages/Auth';
import PerfilDashboard from './pages/PerfilDashboard';
import EmpresaDashboard from './pages/EmpresaDashboard';
import { useAuth } from './context/AuthContext';

function RutaProtegida({ tipo, children }) {
  const { sesion, cargandoSesion } = useAuth();
  if (cargandoSesion) return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'var(--cream)', color: 'var(--navy)' }}>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>Cargando sesión…</p>
    </div>
  );
  if (!sesion) return <Navigate to="/ingresar" replace />;
  if (sesion.tipo !== tipo) return <Navigate to={sesion.tipo === 'perfil' ? '/perfil' : '/empresa'} replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/registro" element={<Auth />} />
      <Route path="/ingresar" element={<Auth />} />
      <Route path="/perfil" element={<RutaProtegida tipo="perfil"><PerfilDashboard /></RutaProtegida>} />
      <Route path="/empresa" element={<RutaProtegida tipo="empresa"><EmpresaDashboard /></RutaProtegida>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
