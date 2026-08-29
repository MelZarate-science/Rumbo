import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import CompassMark from '../components/CompassMark';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

function scoreColor(score) {
  if (score >= 75) return '#5fbfb3';
  if (score >= 50) return '#f0900f';
  return '#d9756a';
}

export default function EmpresaDashboard() {
  const { sesion, logout } = useAuth();
  const navigate = useNavigate();

  const [titulo, setTitulo] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [publicando, setPublicando] = useState(false);
  const [mensajePuesto, setMensajePuesto] = useState('');

  const [mapa, setMapa] = useState([]);
  const [cargandoMapa, setCargandoMapa] = useState(true);

  const cargarMapa = useCallback(async () => {
    setCargandoMapa(true);
    try {
      const data = await api(`/empresas/${sesion.id}/mapa-perfiles`, { auth: true });
      setMapa(data);
    } catch {
      // silencioso: puede no haber puestos todavía
    } finally {
      setCargandoMapa(false);
    }
  }, [sesion.id]);

  useEffect(() => { cargarMapa(); }, [cargarMapa]);

  async function publicarPuesto(e) {
    e.preventDefault();
    if (!titulo || !descripcion) { setMensajePuesto('Completá título y descripción.'); return; }
    setPublicando(true);
    setMensajePuesto('Publicando y clasificando con el agente… puede tardar unos segundos.');
    try {
      await api(`/empresas/${sesion.id}/puestos`, { method: 'POST', auth: true, body: { titulo, descripcion } });
      setMensajePuesto('Puesto publicado e indexado.');
      setTitulo('');
      setDescripcion('');
      cargarMapa();
    } catch (err) {
      setMensajePuesto(err.message || 'No se pudo publicar el puesto.');
    } finally {
      setPublicando(false);
    }
  }

  async function invitar(matchId) {
    try {
      await api(`/matches/${matchId}/invitar`, { method: 'POST', auth: true });
      cargarMapa();
    } catch {
      // no-op
    }
  }

  return (
    <div style={{ background: 'var(--navy-deep)', minHeight: '100%', color: '#eceef3' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1.25rem 8vw', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CompassMark size={24} needleColor="#fff" />
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.15rem' }}>Rumbo</span>
        </div>
        <button className="btn btn-ghost-dark" onClick={() => { logout(); navigate('/'); }}>Salir</button>
      </div>

      <section style={{ padding: '3rem 8vw', maxWidth: 1000, margin: '0 auto' }}>
        <p className="eyebrow">Cargar puesto</p>
        <form onSubmit={publicarPuesto} style={{ background: '#16324f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16, padding: '1.75rem', marginTop: '1rem', maxWidth: 560 }}>
          <label className="field-label" style={{ color: '#a9b8c6' }}>Título</label>
          <input className="field-input" style={{ background: 'var(--navy-deep)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }} value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Ej: Senior Backend Engineer (Python)" />
          <label className="field-label" style={{ color: '#a9b8c6' }}>Descripción</label>
          <textarea className="field-input" style={{ background: 'var(--navy-deep)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} placeholder="Ej: Python, FastAPI, PostgreSQL, Docker. 4+ años de experiencia." />
          <button type="submit" className="btn btn-primary" disabled={publicando}>{publicando ? 'Publicando…' : 'Publicar puesto'}</button>
          {mensajePuesto && <p style={{ color: '#a9b8c6', fontSize: '0.85rem', marginTop: '0.9rem' }}>{mensajePuesto}</p>}
        </form>
      </section>

      <section style={{ padding: '0 8vw 4rem', maxWidth: 1000, margin: '0 auto' }}>
        <p className="eyebrow">Mapa de perfiles</p>
        <h2 style={{ fontSize: '1.5rem', marginTop: '0.5rem', color: '#fff' }}>Perfiles afines a tus puestos</h2>

        {cargandoMapa && <p style={{ color: '#7d8fa1' }}>Cargando…</p>}
        {!cargandoMapa && mapa.length === 0 && (
          <p style={{ color: '#7d8fa1' }}>Todavía no hay perfiles afines a tus puestos.</p>
        )}

        <div style={{ display: 'grid', gap: '0.9rem', marginTop: '1.5rem' }}>
          {mapa.map((m) => (
            <div key={m.match_id} style={{ background: '#16324f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 14, padding: '1.3rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div>
                <p style={{ fontWeight: 600, margin: '0 0 0.2rem' }}>{m.perfil?.nombre || 'Perfil'} · {m.puesto?.titulo}</p>
                <p style={{ color: '#a9b8c6', fontSize: '0.85rem', margin: '0 0 0.3rem' }}>
                  {(m.perfil?.cv_data?.habilidades || []).join(', ')}
                </p>
                {m.perfil?.apellido && (
                  <p style={{ color: '#5fbfb3', fontSize: '0.85rem', margin: 0 }}>{m.perfil.apellido} · {m.perfil.email} {m.perfil.telefono}</p>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, background: scoreColor(m.score), color: '#0c2843', padding: '3px 10px', borderRadius: 999 }}>{m.score}</span>
                {m.estado === 'pendiente' && (
                  <button className="btn btn-primary" onClick={() => invitar(m.match_id)}>Invitar</button>
                )}
                {m.estado !== 'pendiente' && (
                  <span style={{ fontSize: '0.8rem', color: '#a9b8c6', textTransform: 'capitalize' }}>{m.estado}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
