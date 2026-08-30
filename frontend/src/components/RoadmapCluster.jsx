function circleSize(pct) {
  return 36 + Math.round((pct / 100) * 30);
}

function Nodo({ item, especifico }) {
  const size = especifico ? 44 : circleSize(item.porcentaje_mercado ?? 20);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem', width: 70 }}>
      <div
        title={item.sugerencia || undefined}
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          border: `1.5px ${especifico ? 'dashed' : 'solid'} ${item.cumplido ? '#5fbfb3' : '#4a6a86'}`,
          background: item.cumplido ? 'rgba(95,191,179,0.22)' : 'transparent',
          color: item.cumplido ? '#dff5f0' : '#cfe0ee',
          fontSize: 10,
          fontFamily: 'var(--font-mono)',
        }}
      >
        {item.porcentaje_mercado !== undefined ? `${item.porcentaje_mercado}%` : ''}
      </div>
      <div style={{ fontSize: 10.5, color: '#a9b8c6', textAlign: 'center', lineHeight: 1.25 }}>{item.nombre}</div>
    </div>
  );
}

function GroupLabel({ children }) {
  return (
    <div style={{ fontSize: '0.78rem', color: '#7d8fa1', margin: '1.1rem 0 0.7rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      {children}
      <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.1)' }} />
    </div>
  );
}

/**
 * roadmap: array de {requisito_id, nombre, cumplido, porcentaje_mercado, especifico_de_esta_empresa, sugerencia}
 * Nunca muestra a qué empresa pertenece — eso lo filtra la visibilidad escalonada del lado del backend.
 */
export default function RoadmapCluster({ roadmap }) {
  const comunes = roadmap.filter((r) => !r.especifico_de_esta_empresa);
  const particulares = roadmap.filter((r) => r.especifico_de_esta_empresa);

  return (
    <div>
      <GroupLabel>Estándar del mercado para este rol</GroupLabel>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem 0.4rem', alignItems: 'flex-end' }}>
        {comunes.map((r) => <Nodo key={r.requisito_id} item={r} especifico={false} />)}
        {comunes.length === 0 && <p style={{ color: '#7d8fa1', fontSize: '0.85rem' }}>Sin datos de mercado todavía.</p>}
      </div>

      {particulares.length > 0 && (
        <>
          <GroupLabel>Particular de este puesto</GroupLabel>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem 0.4rem', alignItems: 'flex-end' }}>
            {particulares.map((r) => <Nodo key={r.requisito_id} item={r} especifico />)}
          </div>
        </>
      )}
    </div>
  );
}
