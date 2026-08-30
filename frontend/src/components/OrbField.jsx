import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import RoadmapCluster from './RoadmapCluster';
import { IconArrowLeft } from './Icons';

const POSICIONES = [
  { top: '10%', left: '18%' },
  { top: '55%', left: '8%' },
  { top: '15%', left: '62%' },
  { top: '62%', left: '58%' },
  { top: '35%', left: '38%' },
  { top: '78%', left: '30%' },
];

function scoreColor(score) {
  if (score >= 75) return '#5fbfb3';
  if (score >= 50) return '#f0900f';
  return '#d9756a';
}

export default function OrbField({ matches, onResponder }) {
  const [seleccionadoId, setSeleccionadoId] = useState(null);
  const seleccionado = matches.find((m) => m.match_id === seleccionadoId) || null;

  if (matches.length === 0) {
    return (
      <p style={{ color: '#7d8fa1', textAlign: 'center', padding: '3rem 0' }}>
        Todavía no tenés puestos afines. Apenas una empresa cargue un puesto que cruce con tu perfil, va a aparecer acá.
      </p>
    );
  }

  return (
    <div style={{ position: 'relative', height: 500 }}>
      {matches.map((m, i) => {
        const pos = POSICIONES[i % POSICIONES.length];
        const oculto = seleccionadoId && seleccionadoId !== m.match_id;
        const esElegido = seleccionadoId === m.match_id;
        return (
          <motion.div
            key={m.match_id}
            role="button"
            tabIndex={0}
            aria-label={`Ver detalle de ${m.puesto_titulo}`}
            onClick={() => setSeleccionadoId(m.match_id)}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSeleccionadoId(m.match_id); } }}
            initial={false}
            animate={
              esElegido
                ? { top: '50%', left: '12%', y: '-50%', opacity: 1, scale: 1.1 }
                : oculto
                ? { opacity: 0, scale: 0.5, top: pos.top, left: pos.left, y: 0 }
                : { opacity: 1, scale: 1, top: pos.top, left: pos.left, y: [0, -16, 0] }
            }
            transition={
              esElegido || oculto
                ? { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
                : { y: { duration: 4.5 + i * 0.6, repeat: Infinity, ease: 'easeInOut' } }
            }
            style={{
              position: 'absolute',
              width: esElegido ? 148 : 128,
              height: esElegido ? 148 : 128,
              borderRadius: '50%',
              background: 'radial-gradient(circle at 35% 30%, #1c3a58, #12233a 72%)',
              border: `1px solid ${esElegido ? '#f0900f' : 'rgba(240,144,15,0.32)'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              padding: '1rem',
              cursor: oculto ? 'default' : 'pointer',
              color: '#eceef3',
              fontSize: '0.83rem',
              fontWeight: 600,
              pointerEvents: oculto ? 'none' : 'auto',
              boxShadow: esElegido ? '0 0 0 1px #f0900f, 0 0 40px -6px rgba(240,144,15,0.4)' : 'none',
            }}
          >
            <span
              style={{
                position: 'absolute',
                top: -10,
                right: -6,
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                background: scoreColor(m.score),
                color: '#0c2843',
                padding: '2px 7px',
                borderRadius: 999,
              }}
            >
              {m.score}
            </span>
            {m.puesto_titulo}
          </motion.div>
        );
      })}

      <AnimatePresence>
        {seleccionado && (
          <motion.div
            key="detalle"
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 24 }}
            transition={{ duration: 0.45, delay: 0.2 }}
            style={{
              position: 'absolute',
              right: 0,
              top: '50%',
              transform: 'translateY(-50%)',
              width: '50%',
              maxWidth: 460,
            }}
          >
            <button
              onClick={() => setSeleccionadoId(null)}
              style={{ background: 'none', border: 'none', color: '#8fa2b4', fontSize: '0.85rem', cursor: 'pointer', padding: 0, marginBottom: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <IconArrowLeft /> Volver
            </button>
            <h3 style={{ fontSize: '1.45rem', marginBottom: '0.5rem', color: '#fff' }}>{seleccionado.puesto_titulo}</h3>
            <p style={{ color: '#a9b8c6', fontSize: '0.88rem', lineHeight: 1.6, margin: '0 0 1rem', maxWidth: '48ch' }}>
              {seleccionado.descripcion || 'Descripción no disponible.'}
            </p>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#7d8fa1', margin: '0 0 1.2rem' }}>
              score <span style={{ color: '#f0900f' }}>{seleccionado.score}</span>/100
            </p>
            {seleccionado.justificacion && (
              <p style={{ color: '#cfe0ee', fontSize: '0.85rem', lineHeight: 1.6, margin: '0 0 1.3rem' }}>{seleccionado.justificacion}</p>
            )}
            <RoadmapCluster roadmap={seleccionado.roadmap} />

            {seleccionado.estado === 'notificado' && (
              <div style={{ display: 'flex', gap: '0.6rem', marginTop: '1.6rem' }}>
                <button className="btn btn-primary" onClick={() => onResponder(seleccionado.match_id, true)}>Aceptar</button>
                <button className="btn btn-ghost-dark" onClick={() => onResponder(seleccionado.match_id, false)}>Rechazar</button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
