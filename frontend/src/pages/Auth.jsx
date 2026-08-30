import { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import CompassMark from '../components/CompassMark';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../api';

export default function Auth() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login, registrarPerfil, registrarEmpresa } = useAuth();

  const [modo, setModo] = useState(location.pathname === '/ingresar' ? 'login' : 'registro');
  const [tipo, setTipo] = useState('perfil');
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);

  const [form, setForm] = useState({
    nombre: '', apellido: '', email: '', password: '', telefono: '',
    cv_texto: '', habilidades: '',
    nombre_empresa: '', contexto: '', email_registro: '',
  });

  function actualizar(campo, valor) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  async function enviar(e) {
    e.preventDefault();
    setError('');

    if (modo === 'login') {
      const email = tipo === 'perfil' ? form.email : form.email_registro;
      if (!email || !form.password) { setError('Completá email y contraseña.'); return; }
      setCargando(true);
      try {
        await login(email, form.password, tipo);
        navigate(tipo === 'perfil' ? '/perfil' : '/empresa');
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'No se pudo iniciar sesión.');
      } finally {
        setCargando(false);
      }
      return;
    }

    // registro
    if (tipo === 'perfil') {
      if (!form.nombre || !form.apellido || !form.email || form.password.length < 8) {
        setError('Completá nombre, apellido, email y una contraseña de al menos 8 caracteres.');
        return;
      }
      setCargando(true);
      try {
        const habilidades = form.habilidades.split(',').map((h) => h.trim()).filter(Boolean);
        const cv_data = { experiencia: [], formacion: [], habilidades, proyectos: [] };
        const registrado = await registrarPerfil({
          nombre: form.nombre,
          apellido: form.apellido,
          email: form.email,
          password: form.password,
          telefono: form.telefono || undefined,
          cv_texto_original: form.cv_texto || undefined,
          cv_data,
        });
        // Dispara el matching real con las habilidades recién cargadas.
        await api(`/perfiles/${registrado.perfil_id}/cv`, { method: 'PUT', body: cv_data });
        navigate('/perfil');
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'No se pudo crear la cuenta.');
      } finally {
        setCargando(false);
      }
    } else {
      if (!form.nombre_empresa || !form.email_registro || form.password.length < 8) {
        setError('Completá el nombre de la empresa, email y una contraseña de al menos 8 caracteres.');
        return;
      }
      setCargando(true);
      try {
        await registrarEmpresa({
          nombre_empresa: form.nombre_empresa,
          contexto: form.contexto || '',
          email_registro: form.email_registro,
          password: form.password,
        });
        navigate('/empresa');
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'No se pudo crear la cuenta.');
      } finally {
        setCargando(false);
      }
    }
  }

  return (
    <div style={{ background: 'var(--cream)', minHeight: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2.5rem 1.5rem' }}>
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2.5rem', textDecoration: 'none' }}>
        <CompassMark size={28} />
        <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.15rem', fontWeight: 600, color: 'var(--navy)' }}>Rumbo</span>
      </Link>

      <div style={{ background: '#fff', border: '1px solid #e3e7eb', borderRadius: 18, padding: '2.5rem', maxWidth: 440, width: '100%' }}>
        <div style={tabRow}>
          <button type="button" onClick={() => setTipo('perfil')} style={tabBtn(tipo === 'perfil')}>Soy un perfil</button>
          <button type="button" onClick={() => setTipo('empresa')} style={tabBtn(tipo === 'empresa')}>Soy una empresa</button>
        </div>

        <h2 style={{ fontSize: '1.3rem', color: 'var(--navy)', marginBottom: '0.3rem' }}>
          {modo === 'registro' ? 'Crear cuenta' : 'Iniciar sesión'}
        </h2>
        <p style={{ fontSize: '0.88rem', color: '#5a6a7a', margin: '0 0 1.5rem' }}>
          {modo === 'registro' ? '¿Ya tenés cuenta? ' : '¿Todavía no tenés cuenta? '}
          <button type="button" onClick={() => { setModo(modo === 'registro' ? 'login' : 'registro'); setError(''); }} style={linkBtn}>
            {modo === 'registro' ? 'Iniciá sesión' : 'Registrate'}
          </button>
        </p>

        <form onSubmit={enviar}>
          {modo === 'registro' && tipo === 'perfil' && (
            <>
              <label className="field-label">Nombre</label>
              <input className="field-input" value={form.nombre} onChange={(e) => actualizar('nombre', e.target.value)} />
              <label className="field-label">Apellido</label>
              <input className="field-input" value={form.apellido} onChange={(e) => actualizar('apellido', e.target.value)} />
            </>
          )}

          {modo === 'registro' && tipo === 'empresa' && (
            <>
              <label className="field-label">Nombre de la empresa</label>
              <input className="field-input" value={form.nombre_empresa} onChange={(e) => actualizar('nombre_empresa', e.target.value)} />
              <label className="field-label">Contexto (cultura, a quién buscan en general)</label>
              <textarea className="field-input" value={form.contexto} onChange={(e) => actualizar('contexto', e.target.value)} />
            </>
          )}

          <label className="field-label">Email</label>
          <input
            className="field-input"
            type="email"
            value={tipo === 'perfil' ? form.email : form.email_registro}
            onChange={(e) => actualizar(tipo === 'perfil' ? 'email' : 'email_registro', e.target.value)}
          />

          {modo === 'registro' && tipo === 'perfil' && (
            <>
              <label className="field-label">Teléfono (opcional)</label>
              <input className="field-input" value={form.telefono} onChange={(e) => actualizar('telefono', e.target.value)} />
              <label className="field-label">Sobre tu experiencia (texto libre, para tu CV)</label>
              <textarea className="field-input" value={form.cv_texto} onChange={(e) => actualizar('cv_texto', e.target.value)} placeholder="Ej: Desarrolladora Python con 5 años en backend y APIs REST." />
              <label className="field-label">Habilidades (separadas por coma)</label>
              <input className="field-input" value={form.habilidades} onChange={(e) => actualizar('habilidades', e.target.value)} placeholder="Python, FastAPI, PostgreSQL, Docker" />
            </>
          )}

          <label className="field-label">Contraseña{modo === 'registro' ? ' (mínimo 8 caracteres)' : ''}</label>
          <input className="field-input" type="password" value={form.password} onChange={(e) => actualizar('password', e.target.value)} />

          {error && <p className="field-error">{error}</p>}

          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }} disabled={cargando}>
            {cargando ? 'Un momento…' : modo === 'registro' ? 'Crear cuenta' : 'Iniciar sesión'}
          </button>
        </form>
      </div>
    </div>
  );
}

const tabRow = { display: 'flex', background: 'var(--cream)', borderRadius: 999, padding: 4, marginBottom: '1.75rem' };

function tabBtn(activo) {
  return {
    flex: 1,
    padding: '0.6rem 1rem',
    borderRadius: 999,
    border: 'none',
    background: activo ? 'var(--orange)' : 'none',
    color: activo ? '#2a1400' : '#5a6a7a',
    fontWeight: 600,
    fontSize: '0.9rem',
    cursor: 'pointer',
  };
}

const linkBtn = { background: 'none', border: 'none', padding: 0, color: 'var(--orange-deep)', fontWeight: 600, cursor: 'pointer', fontSize: 'inherit' };
