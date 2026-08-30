import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import CompassMark from '../components/CompassMark';
import OrbField from '../components/OrbField';
import { IconBell } from '../components/Icons';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

export default function PerfilDashboard() {
  const { sesion, logout } = useAuth();
  const navigate = useNavigate();

  const [matches, setMatches] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState(null);
  const [toastAbierto, setToastAbierto] = useState(false);

  const notificadosVistos = useRef(new Set());
  const primeraCarga = useRef(true);

  const cargarMatches = useCallback(async () => {
    try {
      const data = await api(`/perfiles/${sesion.id}/matches`);

      const conDescripcion = await Promise.all(
        data.map(async (m) => {
          if (!m.puesto_id) return m;
          try {
            const puesto = await api(`/puestos/${m.puesto_id}`);
            return { ...m, descripcion: puesto.descripcion };
          } catch {
            return m;
          }
        })
      );

      const notificadosAhora = conDescripcion.filter((m) => m.estado === 'notificado');
      if (!primeraCarga.current) {
        const nuevo = notificadosAhora.find((m) => !notificadosVistos.current.has(m.match_id));
        if (nuevo) {
          setToast(nuevo);
          setToastAbierto(true);
        }
      }
      notificadosVistos.current = new Set(notificadosAhora.map((m) => m.match_id));
      primeraCarga.current = false;

      setMatches(conDescripcion);
      setError('');
    } catch (err) {
      setError('No se pudieron cargar tus matches.');
    } finally {
      setCargando(false);
    }
  }, [sesion.id]);

  useEffect(() => {
    cargarMatches();
    const id = setInterval(cargarMatches, 20000);
    return () => clearInterval(id);
  }, [cargarMatches]);

  async function responder(matchId, aceptar) {
    try {
      await api(`/matches/${matchId}/responder`, { method: 'POST', body: { aceptar } });
      cargarMatches();
    } catch {
      setError('No se pudo enviar tu respuesta. Probá de nuevo.');
    }
  }

  const hayNotificados = matches.some((m) => m.estado === 'notificado');

  return (
    <div style={{ background: 'var(--navy-deep)', minHeight: '100%', color: '#eceef3' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1.25rem 8vw', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CompassMark size={24} needleColor="#fff" />
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.15rem' }}>Rumbo</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setToastAbierto((v) => !v)}
              aria-label="Ver notificaciones"
              style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', width: 40, height: 40, borderRadius: '50%', color: '#fff', cursor: 'pointer', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              <IconBell />
              {hayNotificados && (
                <span style={{ position: 'absolute', top: 8, right: 9, width: 8, height: 8, borderRadius: '50%', background: '#e85d4a', border: '2px solid var(--navy-deep)' }} />
              )}
            </button>
            {toastAbierto && toast && (
              <div style={{ position: 'absolute', top: 52, right: 0, width: 280, background: '#16324f', border: '1px solid rgba(255,255,255,0.14)', borderRadius: 14, padding: '1rem 1.1rem', boxShadow: '0 20px 40px -12px rgba(0,0,0,0.5)', zIndex: 10 }}>
                <p style={{ fontWeight: 700, fontSize: '0.9rem', margin: '0 0 0.25rem' }}>Tenés una invitación nueva</p>
                <p style={{ color: '#a9b8c6', fontSize: '0.85rem', margin: 0 }}>Una empresa quiere conocerte para {toast.puesto_titulo}. Respondé cuando quieras.</p>
              </div>
            )}
          </div>
          <button className="btn btn-ghost-dark" onClick={async () => { await logout(); navigate('/'); }}>Salir</button>
        </div>
      </div>

      <section style={{ padding: '3.5rem 8vw', maxWidth: 1300, margin: '0 auto' }}>
        <p className="eyebrow">Tus posiciones más afines</p>
        <h2 style={{ fontSize: '1.9rem', marginTop: '0.5rem', maxWidth: '26ch', color: '#fff' }}>Flotando hasta que elegís una</h2>

        {cargando && <p style={{ color: '#7d8fa1' }}>Cargando…</p>}
        {error && <p style={{ color: '#e8837a' }}>{error}</p>}
        {!cargando && <OrbField matches={matches} onResponder={responder} />}
      </section>
    </div>
  );
}
