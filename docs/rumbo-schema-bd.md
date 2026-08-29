# Rumbo — Esquema de Base de Datos (Firestore)

> Firestore es NoSQL orientado a documentos, no relacional. Acá "colección" = tabla, "documento" = fila, y las relaciones se resuelven guardando el ID del documento relacionado como referencia (no hay JOINs). Se optó por colecciones a nivel raíz con referencias cruzadas, en vez de subcolecciones anidadas, porque el sistema necesita consultar `matches` cruzando `perfiles` y `puestos` con frecuencia, y eso es más simple con colecciones planas.

---

## Colección: `empresas`

| Campo | Tipo | Descripción |
|---|---|---|
| `empresa_id` | string (ID del doc) | Identificador único, autogenerado |
| `nombre_empresa` | string | Nombre público de la empresa |
| `contexto` | string (texto libre) | El "system prompt" de la empresa: quién es, cultura, ambiente, a quién busca en general |
| `email_registro` | string | Email de contacto usado en el registro (sin validación de dominio en el MVP) |
| `created_at` | timestamp | Fecha de registro |
| `activa` | boolean | Permite desactivar sin borrar (soft delete) |
| `updated_at` | timestamp (opcional) | Última vez que se editó la empresa |

**Nota de scope:** sin campo de validación/verificación — decisión consciente del MVP, documentada en el spec.

---

## Colección: `roles_normalizados`

Capa intermedia de retrieval — un documento por cada tipo de rol (no por cada puesto individual). Esta colección crece lento y es la que se compara por embedding contra el perfil del usuario, evitando comparar contra el universo completo de puestos duplicados.

| Campo | Tipo | Descripción |
|---|---|---|
| `rol_normalizado_id` | string (ID del doc) | Identificador único (ej: `product_management`). **Mismo nombre exacto que el campo que lo referencia en `puestos`** — nunca `rol_id` a secas |
| `nombre_normalizado` | string | Nombre legible del rol (ej: "Product Manager") |
| `descripcion_consolidada` | string | Síntesis narrativa generada por Gemini, en prosa, de lo que en general piden las empresas para este rol — para uso conversacional/explicativo |
| `requisitos_frecuencia` | array de maps | Tabla de frecuencias: `[{requisito_id: "sql", cantidad: 6, porcentaje: 60}, {requisito_id: "gestion_stakeholders", cantidad: 10, porcentaje: 100}, ...]` — cada `requisito_id` referencia un documento en `requisitos_normalizados`, no texto suelto |
| `requisitos_ids` | array de strings | Copia plana de los mismos IDs que aparecen en `requisitos_frecuencia`, sin la info de conteo — existe solo para poder hacer consultas tipo `array-contains` (ej: "¿en qué roles aparece la habilidad SQL?") sin tener que leer todos los roles y filtrar en el cliente |
| `embedding` | vector | Embedding de `descripcion_consolidada` — este es el campo contra el que se corre `find_nearest()` |
| `cantidad_puestos` | number | Cuántos puestos reales aportaron a esta síntesis, para saber qué tan representativa es |
| `updated_at` | timestamp | Última vez que se resintetizó la descripción consolidada |

---

## Colección: `requisitos_normalizados`

Cada habilidad/herramienta/requisito es una entidad única, sin importar en cuántos roles distintos aparezca. Esto evita tener "SQL" escrito de formas distintas repetido dentro de cada rol, y permite preguntar "¿en qué roles aparece este requisito?" sin necesitar un motor de grafos — es, en esencia, la mitad de un grafo bipartito (roles ↔ requisitos) modelada con referencias simples.

| Campo | Tipo | Descripción |
|---|---|---|
| `requisito_id` | string (ID del doc) | Identificador único (ej: `sql`, `gestion_stakeholders`) |
| `nombre` | string | Nombre legible (ej: "SQL") |
| `tipo` | string (opcional) | Categoría del requisito: `herramienta`, `habilidad_blanda`, `certificacion`, etc. — ayuda a que el roadmap pueda agrupar por tipo si hace falta |
| `created_at` | timestamp | Cuándo se creó esta entidad |

---

## Colección: `puestos`

| Campo | Tipo | Descripción |
|---|---|---|
| `puesto_id` | string (ID del doc) | Identificador único |
| `empresa_id` | string (referencia) | ID del documento en `empresas` al que pertenece |
| `titulo` | string | Ej: "Product Manager" |
| `descripcion` | string (texto libre) | Descripción completa del puesto, tal como la carga la empresa |
| `created_at` | timestamp | Fecha de publicación |
| `activo` | boolean | Si sigue disponible para matching |
| `rol_normalizado_id` | string (referencia) | ID del documento en `roles_normalizados` al que pertenece este puesto. Lo asigna Gemini automáticamente al momento de cargar el puesto |
| `requisitos_extraidos` | array de strings (IDs) | Referencias a `requisitos_normalizados` — Gemini extrae los requisitos de `descripcion` al cargar el puesto y los matchea contra entidades existentes (o crea una nueva si no hay ninguna lo bastante cercana) |
| `requisitos_nuevos` | array de strings (IDs, opcional) | Subconjunto de `requisitos_extraidos` creados recién por el Agente 2 para este puesto puntual (no estaban en el catálogo antes). El Auditor de fit lo usa para marcar `especifico_de_esta_empresa` en el roadmap — ver colección `matches` |
| `updated_at` | timestamp (opcional) | Última vez que se editó el puesto (dispara re-indexado si cambia `titulo`/`descripcion`) |

**Nota:** un puesto es opcional — una empresa puede existir solo con `contexto` y sin ningún puesto cargado todavía, y el matching igual puede correr contra ese contexto general.

---

## Colección: `perfiles`

| Campo | Tipo | Descripción | Visible a empresa antes de opt-in |
|---|---|---|---|
| `perfil_id` | string (ID del doc) | Identificador único | — |
| `nombre` | string | Nombre de pila | ✅ sí |
| `apellido` | string | Apellido completo | ❌ no |
| `email` | string | Contacto | ❌ no |
| `telefono` | string (opcional) | Contacto | ❌ no |
| `cv_texto_original` | string | Texto extraído del PDF subido, si aplica | ❌ no (uso interno) |
| `cv_data` | map | Estructura parseada — ver detalle completo en la sección siguiente | ✅ sí (contenido, no metadatos de contacto) |
| `cv_generado_harvard` | string (opcional) | CV generado en formato Harvard, si el usuario lo pidió | ❌ no (es para el propio usuario) |
| `busqueda_interes` | string (opcional) | Puesto/rol que el usuario indicó como objetivo, para adaptar el CV generado | — |
| `embedding` | vector | Embedding generado a partir de todo el `cv_data` consolidado — es contra este campo que se corre `find_nearest()` sobre `roles_normalizados` | — |
| `created_at` | timestamp | Fecha de registro | — |
| `updated_at` | timestamp (opcional) | Última vez que se editaron los datos personales del perfil o su `cv_data` | — |

**Nota de privacidad (Fase 4 del backlog):** los campos marcados como visibles antes del opt-in son los únicos que debe devolver la función/endpoint que arma el "mapa de perfiles" para la empresa. `apellido`, `email` y `telefono` solo se incluyen en la respuesta después de que el `match` correspondiente pase a estado `confirmado`.

### Detalle de `cv_data` (subestructura completa)

`cv_data` es un mapa con cuatro arrays. Cada elemento de cada array tiene su propia estructura, no son strings sueltos:

**`experiencia`** (array de maps):

| Campo | Tipo | Descripción |
|---|---|---|
| `puesto` | string | Cargo que ocupó (ej: "Analista de Datos Jr.") |
| `empresa` | string | Nombre de la empresa donde trabajó (texto libre del candidato, no referencia a la colección `empresas`) |
| `descripcion` | string | Detalle de tareas y logros |
| `fecha_desde` | date | Inicio |
| `fecha_hasta` | date \| null | Fin — `null` si sigue vigente |
| `actual` | boolean | `true` si es el trabajo actual |

**`formacion`** (array de maps):

| Campo | Tipo | Descripción |
|---|---|---|
| `titulo` | string | Ej: "Licenciatura en Sistemas" |
| `institucion` | string | Ej: "Universidad Nacional de Córdoba" |
| `descripcion` | string (opcional) | Detalle adicional si aplica |
| `fecha_desde` | date | Inicio |
| `fecha_hasta` | date \| null | Fin — `null` si sigue en curso |
| `en_curso` | boolean | `true` si todavía lo está cursando |

**`habilidades`** (array de strings): lista simple de tags, sin subestructura propia (ej: `["Python", "SQL", "Gestión de equipos"]`).

**`proyectos`** (array de maps):

| Campo | Tipo | Descripción |
|---|---|---|
| `nombre` | string | Nombre del proyecto |
| `descripcion` | string | De qué se trató, qué hizo el candidato |
| `fecha` | date (opcional) | Cuándo lo hizo |
| `link` | string (opcional) | Repositorio o demo, si aplica |

---

## Colección: `matches`

Este es el corazón del sistema — conecta un `perfil` con un `puesto` (o directamente con una `empresa` si todavía no hay puesto específico), y lleva el estado de todo el flujo de notificación y opt-in.

| Campo | Tipo | Descripción |
|---|---|---|
| `match_id` | string (ID del doc) | Identificador único |
| `perfil_id` | string (referencia) | ID del documento en `perfiles` |
| `empresa_id` | string (referencia) | ID del documento en `empresas` |
| `puesto_id` | string (referencia, opcional) | ID del documento en `puestos`, si el match es contra un puesto específico y no solo contra el contexto general |
| `score` | number (0-100) | % de afinidad calculado por el Auditor Agent |
| `roadmap` | array de maps | Lista de requisitos evaluados, con datos cuantitativos — ver detalle abajo. **No es texto libre**: la vista de red de la interfaz necesita el porcentaje por requisito para dibujarse |
| `justificacion` | string | Breve explicación del Auditor Agent sobre el score |
| `estado` | string (enum) | `pendiente` \| `notificado` \| `confirmado` \| `rechazado` |
| `created_at` | timestamp | Cuándo se generó el match |
| `updated_at` | timestamp | Última vez que cambió el estado |

### Detalle de `roadmap` (subestructura)

Cada elemento del array es un map con esta forma:

| Campo | Tipo | Descripción |
|---|---|---|
| `requisito_id` | string (referencia) | ID del documento en `requisitos_normalizados` |
| `nombre` | string | Nombre legible del requisito (copiado para no tener que resolver la referencia al mostrarlo) |
| `cumplido` | boolean | Si el perfil ya lo tiene (según su `cv_data`) o le falta |
| `porcentaje_mercado` | number (0-100) | Qué porcentaje de los puestos de ese rol lo piden — viene de `requisitos_frecuencia` del rol |
| `especifico_de_esta_empresa` | boolean | `true` si este puesto lo pide pero está por debajo del promedio del rol (es una particularidad de esta empresa, no un estándar del mercado) |
| `sugerencia` | string (opcional) | Qué hacer para cubrirlo, si no está cumplido (ej: "sumar un proyecto con SQL") |

Con esta estructura, la pantalla de detalle (tarea 2.13) puede dibujar la vista de red: `porcentaje_mercado` define el tamaño/centralidad de cada nodo, `cumplido` define el color, y `especifico_de_esta_empresa` distingue lo que pide el mercado en general de lo que pide esta empresa en particular.

### Ciclo de vida de `estado`

```
pendiente → notificado → confirmado   (perfil aceptó la invitación → pasa a "candidato")
                       → rechazado    (perfil no aceptó la invitación)
```

- **`pendiente`**: el Auditor Agent ya calculó el score y el match aparece en el "mapa de perfiles" de la empresa — pero todavía no pasó nada más. El perfil, del otro lado, puede ver este mismo match entre sus "puestos afines", con roadmap y score, **pero sin saber qué empresa es**.
- **`notificado`**: la empresa, mirando su mapa de perfiles, decidió manualmente invitar a este perfil en particular (acción humana, no automática). Recién en este momento el perfil ve **qué empresa lo invitó** y el detalle completo del puesto.
- **`confirmado`**: el perfil aceptó la invitación — recién acá la empresa puede ver `apellido`, `email`, `telefono`. El perfil pasa a llamarse "candidato" de acá en adelante.
- **`rechazado`**: el perfil no aceptó — la empresa nunca ve los datos completos.

**Importante:** pasar de `pendiente` a `notificado` es siempre una decisión manual de una persona del lado de la empresa, nunca algo que el sistema dispare solo — es el mismo principio de human-in-the-loop que ya rige del lado del perfil (nadie es contactado sin que alguien, de un lado o del otro, decida activamente dar ese paso).

**Visibilidad de `puesto`/`empresa` del lado del perfil:** mientras el match esté en `pendiente`, el perfil ve `titulo`, `descripcion`, `roadmap` y `score` del puesto — nunca `nombre_empresa` ni `contexto`. Esos dos campos solo se revelan al perfil cuando el match pasa a `notificado`.

**Comportamiento proactivo (sin lenguaje de búsqueda):** apenas un perfil termina de registrarse, el disparo asíncrono por Pub/Sub (backlog 2.11) calcula sus matches contra los puestos existentes y se los muestra directamente al entrar a la plataforma — no hay un botón de "buscar", el sistema ya le presenta sus puestos más afines de entrada.

---

## Retrieval en dos niveles: por qué "Product Manager" no siempre es lo mismo, y cómo evitar comparar contra puestos duplicados

Buscar directamente por embedding contra **todos** los puestos individuales es correcto semánticamente, pero ineficiente en la práctica: si hay 20 puestos de "Product Manager" cargados por 20 empresas distintas, la mayoría son semánticamente muy parecidos entre sí — comparar el perfil contra cada uno por separado es esfuerzo redundante, y si además el perfil también matchea con roles vecinos (Team Lead, Analista de Datos), el universo a comparar crece rápido y sin necesidad.

La solución es un **retrieval en dos niveles**, apoyado en la colección `roles_normalizados`:

**Nivel 1 — Búsqueda semántica contra la capa chica (`roles_normalizados`):**
El embedding del perfil se compara, con `find_nearest()`, contra los embeddings de `roles_normalizados` — una colección que crece lento (decenas de roles, no miles de puestos) porque agrupa por tipo de rol, no por publicación individual. Esto devuelve los 1-3 roles más afines al perfil, sin necesidad de tocar los puestos reales todavía.

**Nivel 2 — Filtro barato contra los puestos reales (`puestos`):**
Una vez identificado el rol (ej: "product_management"), se consulta `puestos` filtrando por `rol_normalizado_id` — una consulta simple de Firestore, sin costo de embedding ni de LLM, que trae todos los puestos reales de ese rol sin importar cuántas empresas los publicaron.

**Recién ahí entra el Auditor Agent (Gemini):**
Sobre ese conjunto ya acotado, Gemini evalúa cada puesto individualmente contra el perfil — acá sí vale la pena mirar cada uno por separado, porque es donde surge el roadmap específico de cada empresa (*"en general el mercado pide A, B, C para este rol — y esta empresa en particular también pide D"*, usando `descripcion_consolidada` como referencia del "general" y la descripción propia del puesto como la particularidad).

**Cómo se mantiene todo actualizado:** cuando una empresa carga un puesto nuevo, Gemini hace tres cosas en la misma pasada: (1) clasifica el puesto contra los roles existentes en `roles_normalizados` (o crea uno nuevo), (2) extrae sus requisitos discretos de la descripción y los matchea contra `requisitos_normalizados` (reconoce que "SQL" y "manejo de bases de datos" son la misma entidad, creando una nueva solo si de verdad no existe algo equivalente), y (3) actualiza `requisitos_frecuencia` y `requisitos_ids` del rol correspondiente, incrementando conteos y recalculando porcentajes. Así, el roadmap de un perfil puede ser concreto y cuantitativo: *"el 100% de los puestos de este rol piden gestión de stakeholders (ya lo tenés), el 60% pide SQL (te falta), y esta empresa en particular además pide experiencia en fintech"* — combinando el patrón general del rol con la particularidad del puesto puntual.

**Conectando esto con la pregunta original sobre grafos:** lo que terminó armándose acá es, en esencia, un **grafo bipartito** — dos tipos de entidades (`roles_normalizados` y `requisitos_normalizados`) conectadas por relaciones con peso (la frecuencia), modelado con colecciones normalizadas y referencias por ID en vez de con un motor de grafos dedicado. Esto es suficiente para todo lo que necesitan en el hackathon (incluida la consulta "¿en qué roles aparece esta habilidad?", vía `requisitos_ids`). Si a futuro el producto necesita recorridos más profundos — por ejemplo, "encontrame perfiles con habilidades similares a los que ya matchearon bien con este rol" (dos o más saltos de relación) — ahí sí **Spanner Graph** se vuelve la herramienta correcta, porque ese tipo de recorrido de varios saltos es exactamente donde un motor de grafos nativo empieza a rendir mejor que las consultas simples de Firestore.

---

## Índices compuestos necesarios

Firestore requiere índices explícitos para queries que combinan filtros y orden. Van a necesitar como mínimo:

1. `roles_normalizados` con índice vectorial sobre `embedding` → requerido para que `find_nearest()` funcione (índice de campo único).
2. `matches` filtrado por `empresa_id` (o `puesto_id`) + ordenado por `score` descendente → para armar el "mapa de perfiles" de la empresa, mostrando los de mayor afinidad primero.
3. `matches` filtrado por `perfil_id` + ordenado por `score` descendente → para la pantalla del perfil, mostrando sus puestos más afines.
4. `matches` filtrado por `estado` → para que el sistema encuentre rápido los que están en `pendiente` esperando acción de la empresa.
5. `puestos` filtrado por `rol_normalizado_id` → consulta simple del Nivel 2 del retrieval, sin necesidad de índice vectorial acá.

Firestore te va a avisar en la consola/logs cuándo falta crear un índice compuesto la primera vez que una query lo necesite — no hace falta crearlos todos de antemano, se resuelven sobre la marcha en desarrollo.

---

## Resumen visual de relaciones

```
requisitos_normalizados (muchos) ──< roles_normalizados (muchos)   [relación M:N vía requisitos_ids]
                                              │
                                              │ (1)
                                              ▼
roles_normalizados (1) ────< puestos (muchos)
                                  │
empresas (1) ────< puestos (muchos)
    │                    │
    │                    │
    └──────< matches >───┘
                │
           perfiles (1) ────< matches (muchos)
```

Un `match` siempre referencia un `perfil_id` y un `empresa_id`; `puesto_id` es opcional. El retrieval real ocurre en dos pasos: primero `perfiles.embedding` contra `roles_normalizados.embedding` (semántico), después un filtro simple de `puestos` por `rol_normalizado_id` (sin vector). Los requisitos discretos (`requisitos_normalizados`) se conectan a los roles como una relación muchos-a-muchos ponderada por frecuencia — el "grafo bipartito" mencionado arriba.

---

*Este esquema corresponde a la tarea 0.3 del backlog — se crea antes de repartir el resto de las tareas en paralelo, para que todo el equipo trabaje sobre la misma estructura de datos. Los nombres de campo definidos acá son la fuente de verdad: ver `rumbo-contrato-interfaces.md` para cómo se usan en endpoints y funciones.*
