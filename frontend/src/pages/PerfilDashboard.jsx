import { useState, useEffect, useCallback } from 'react';
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
  const [panelAbierto, setPanelAbierto] = useState(false);

  const cargarMatches = useCallback(async () => {
    try {
      const data = await api(`/perfiles/${sesion.id}/matches`, { auth: true });

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
      await api(`/matches/${matchId}/responder`, { method: 'POST', auth: true, body: { aceptar } });
      cargarMatches();
    } catch {
      setError('No se pudo enviar tu respuesta. Probá de nuevo.');
    }
  }

  const notificados = matches.filter((m) => m.estado === 'notificado');
  const hayNotificados = notificados.length > 0;

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
              onClick={() => setPanelAbierto((v) => !v)}
              aria-label="Ver notificaciones"
              style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', width: 40, height: 40, borderRadius: '50%', color: '#fff', cursor: 'pointer', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              <IconBell />
              {hayNotificados && (
                <span style={{ position: 'absolute', top: 8, right: 9, width: 8, height: 8, borderRadius: '50%', background: '#e85d4a', border: '2px solid var(--navy-deep)' }} />
              )}
            </button>
            {panelAbierto && (
              <div style={{ position: 'absolute', top: 52, right: 0, width: 300, background: '#16324f', border: '1px solid rgba(255,255,255,0.14)', borderRadius: 14, padding: '0.9rem', boxShadow: '0 20px 40px -12px rgba(0,0,0,0.5)', zIndex: 10, display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {notificados.length === 0 && (
                  <p style={{ color: '#a9b8c6', fontSize: '0.85rem', margin: 0, padding: '0.2rem' }}>No tenés invitaciones pendientes.</p>
                )}
                {notificados.map((m) => (
                  <div key={m.match_id} style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 10, padding: '0.8rem' }}>
                    <p style={{ fontWeight: 700, fontSize: '0.88rem', margin: '0 0 0.35rem' }}>Invitación para {m.puesto_titulo}</p>
                    <p style={{ color: '#a9b8c6', fontSize: '0.8rem', margin: '0 0 0.7rem' }}>Una empresa quiere conocerte. Respondé cuando quieras.</p>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn btn-primary" style={{ padding: '0.35rem 0.8rem', fontSize: '0.8rem' }} onClick={() => responder(m.match_id, true)}>Aceptar</button>
                      <button className="btn btn-ghost-dark" style={{ padding: '0.35rem 0.8rem', fontSize: '0.8rem' }} onClick={() => responder(m.match_id, false)}>Rechazar</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button className="btn btn-ghost-dark" onClick={() => { logout(); navigate('/'); }}>Salir</button>
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
