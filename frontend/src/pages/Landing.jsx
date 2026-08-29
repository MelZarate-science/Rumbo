import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import CompassMark from '../components/CompassMark';
import { IconSearch, IconBuilding, IconShield } from '../components/Icons';

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
};

export default function Landing() {
  return (
    <div style={{ background: 'var(--cream)', color: 'var(--navy-deep)', minHeight: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '1.75rem 8vw 0' }}>
        <CompassMark size={30} />
        <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', fontWeight: 600 }}>Rumbo</span>
      </div>

      <section style={sectionStyle} className="hero-grid">
        <motion.div initial="hidden" animate="show" variants={fadeUp} style={{ paddingTop: '2.5rem' }}>
          <p className="eyebrow">Matching agentic para talento</p>
          <h1 style={{ fontSize: 'clamp(2.5rem, 3.8vw, 3.6rem)', lineHeight: 1.08, letterSpacing: '-0.01em', margin: '1rem 0 1.4rem', color: 'var(--navy)' }}>
            La empresa no busca gente.<br />
            Le da <em style={{ fontStyle: 'italic', color: 'var(--orange-deep)' }}>rumbo</em> al agente.
          </h1>
          <p style={{ fontSize: '1.12rem', color: '#4a5a6b', maxWidth: '46ch', margin: '0 0 2.1rem' }}>
            Un agente audita el fit real entre perfiles y empresas, y le muestra a cada lado exactamente lo que necesita saber — sin que nadie tenga que salir a buscar.
          </p>
          <div style={{ display: 'flex', gap: '0.9rem', flexWrap: 'wrap' }}>
            <Link to="/registro" className="btn btn-primary">Crear cuenta</Link>
            <Link to="/ingresar" className="btn btn-ghost-light">Ya tengo cuenta</Link>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          aria-hidden="true"
        >
          <svg viewBox="0 0 200 200" style={{ width: '100%', maxWidth: 340 }}>
            <circle cx="100" cy="100" r="92" fill="none" stroke="#123a5c" strokeWidth="1.5" opacity="0.25" />
            <circle cx="100" cy="100" r="70" fill="none" stroke="#f0900f" strokeWidth="1.5" opacity="0.4" />
            <path d="M100 22 L118 100 L100 178 L82 100 Z" fill="#f0900f" opacity="0.9" />
            <path d="M100 46 L110 100 L100 154 L90 100 Z" fill="#123a5c" />
          </svg>
        </motion.div>
      </section>

      <section style={sectionStyle}>
        <p className="eyebrow">Cómo funciona</p>
        <div className="steps-grid" style={{ marginTop: '2.5rem' }}>
          <Step n="01" title="Registrás tu perfil">Cargás tu experiencia una sola vez. Nada de repetir el mismo CV en veinte formularios distintos.</Step>
          <Step n="02" title="El agente cruza el fit">Audita tu perfil contra cada puesto real y te muestra qué cumplís, qué te falta, y qué tan común es cada cosa en el mercado.</Step>
          <Step n="03" title="Nadie ve a nadie hasta que hay consentimiento">La empresa invita, vos aceptás. Recién ahí se revela quién es quién.</Step>
        </div>
      </section>

      <section style={sectionStyle}>
        <p className="eyebrow">Casos de uso</p>
        <div className="usecase-grid" style={{ marginTop: '2.5rem' }}>
          <UseCase icon={<IconSearch />} title="Buscás sin buscar">Entrás y ya están tus posiciones más afines, con lo que te falta para cada una.</UseCase>
          <UseCase icon={<IconBuilding />} title="Contratás sin publicar en 5 lugares">Cargás tu contexto una vez, el agente cruza contra todos los perfiles registrados.</UseCase>
          <UseCase icon={<IconShield />} title="Privacidad real">Ningún dato de contacto se comparte sin que ambos lados digan que sí.</UseCase>
        </div>
      </section>

      <section style={sectionStyle}>
        <div style={{ background: 'var(--navy)', borderRadius: 20, padding: '3.2rem 3rem', textAlign: 'center' }}>
          <h2 style={{ color: '#fff', fontSize: '1.9rem', marginBottom: '1.4rem' }}>Encontrá tu rumbo</h2>
          <p style={{ color: '#b9c8d6', margin: '0 0 1.6rem' }}>Registro gratuito, resultados desde el primer minuto.</p>
          <Link to="/registro" className="btn btn-primary">Crear cuenta</Link>
        </div>
      </section>

      <style>{`
        .hero-grid { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 3rem; align-items: center; }
        .steps-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2.5rem; }
        .usecase-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
        @media (max-width: 900px) {
          .hero-grid, .steps-grid, .usecase-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

const sectionStyle = { padding: '5.5rem 8vw', maxWidth: 1300, margin: '0 auto' };

function Step({ n, title, children }) {
  return (
    <div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--orange-deep)', marginBottom: '0.7rem' }}>{n}</div>
      <h3 style={{ fontSize: '1.25rem', marginBottom: '0.55rem', color: 'var(--navy)' }}>{title}</h3>
      <p style={{ color: '#4a5a6b', margin: 0, fontSize: '0.97rem' }}>{children}</p>
    </div>
  );
}

function UseCase({ icon, title, children }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e3e7eb', borderRadius: 14, padding: '1.6rem' }}>
      <div style={{ color: 'var(--orange-deep)', marginBottom: '0.8rem' }}>{icon}</div>
      <h3 style={{ fontSize: '1.05rem', marginBottom: '0.4rem', color: 'var(--navy)' }}>{title}</h3>
      <p style={{ fontSize: '0.9rem', color: '#5a6a7a', margin: 0 }}>{children}</p>
    </div>
  );
}
