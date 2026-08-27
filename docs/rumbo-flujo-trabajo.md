# Rumbo — Flujo de Trabajo del Equipo
### Leer antes de tocar el repo. Aplica a todos por igual.

> **Nota sobre el nombre de este archivo:** este documento es el que cada integrante le va a dar como contexto a su asistente de IA de desarrollo. Cada uno debe copiarlo y renombrarlo según la herramienta que use — `GEMINI.md` si trabaja con Gemini, `CLAUDE.md` si trabaja con Claude, etc. El contenido es el mismo para todos; solo cambia el nombre del archivo según qué asistente lo va a leer.

---

## 1. Estructura de carpetas del repo

```
rumbo/
├── README.md                    # instrucciones de setup y spin-up (obligatorio para submission)
├── requirements.txt
├── Dockerfile                   # imagen para desplegar en Cloud Run
├── .env.example                 # plantilla de variables de entorno, sin valores reales
├── .gitignore                   # incluye .env, __pycache__/, *.pyc, credenciales locales
├── main.py                      # entrypoint FastAPI (expone el backend en Cloud Run)
│
├── agents/                      # SOLO los agentes que usan razonamiento de Gemini
│   ├── clasificador_roles.py    # Agente 1 — asigna el puesto a un rol normalizado
│   ├── extractor_requisitos.py  # Agente 2 — extrae requisitos y actualiza frecuencias
│   ├── auditor_fit.py           # Agente 3 — score + roadmap cuantitativo
│   └── prompts/                 # system prompts de cada agente, en archivos separados
│       ├── clasificador_roles_prompt.txt
│       ├── extractor_requisitos_prompt.txt
│       └── auditor_fit_prompt.txt
│
├── pipeline/
│   └── matching_pipeline.py     # orquestación en código plano — NO es un agente:
│                                # la secuencia es fija, ningún modelo decide el enrutamiento
│
├── services/                    # lógica sin razonamiento de modelo
│   ├── firestore_client.py      # único punto de acceso a Firestore
│   ├── embeddings.py            # generación de embeddings (perfil, roles normalizados)
│   ├── retrieval.py             # retrieval de dos niveles (find_nearest + filtro por rol)
│   ├── normalizacion.py         # helpers de roles y frecuencias de requisitos
│   ├── invitaciones.py          # ciclo de vida del match y visibilidad escalonada
│   └── cv_generator.py          # generación del CV en formato Harvard
│
├── models/                      # una clase por colección, reflejando el esquema de datos
│   ├── perfil.py
│   ├── empresa.py
│   ├── puesto.py
│   ├── match.py
│   ├── rol_normalizado.py
│   └── requisito_normalizado.py
│
├── routes/                      # endpoints HTTP expuestos por el backend
│   ├── perfiles.py
│   ├── empresas.py
│   ├── puestos.py
│   └── matches.py
│
├── frontend/                    # interfaz mínima
│
├── scripts/
│   └── seed_data.py             # poblar datos ficticios (tarea 2.1 del backlog)
│
├── tests/                       # pruebas, aunque sean básicas
│
└── docs/
    ├── architecture-diagram.png
    └── (copia de los documentos del equipo)
```

**Por qué `agents/` tiene solo tres archivos:** un agente es un componente que usa el razonamiento del modelo para decidir algo. El pipeline no decide nada (la secuencia es fija), el retrieval es matemática y consultas, y las invitaciones son cambios de estado. Llamarlos "agentes" sería inflar el conteo — y un jurado técnico que mire el código lo va a notar.

**Antes de escribir la primera línea de lógica de negocio**, quien resuelva la tarea 0.4 del backlog crea esta estructura vacía (carpetas + archivos `__init__.py` donde corresponda) y la sube a `develop`. Nadie más empieza su parte hasta que esta base exista — evita que cada uno invente su propia organización de carpetas y haya que reconciliar después.

---

## 2. Estructura de ramas

```
main        ← producción. Nadie pushea directo acá. Solo llega vía merge desde develop.
  └── develop   ← rama de integración. Acá se juntan todas las features antes de ir a producción.
        ├── feature/1.1-login
        ├── feature/2.9-auditor-agent
        ├── feature/4.2-invitacion-empresa
        └── feature/... (una por tarea o bloque de tareas del backlog)
```

### Reglas

1. **Nadie pushea directo a `main` ni a `develop`.** Todo cambio nace en una rama `feature/` que sale de `develop`.
2. **Nombrá la rama con el ID de la tarea del backlog**: `feature/1.1-login`, `feature/2.9-auditor-agent`. Así queda trazable qué tarea resolvió cada rama, y cualquiera puede volver al backlog y entender el contexto.
3. **Antes de pushear tu rama**: traé los últimos cambios de `develop` a tu rama (`git pull origin develop` seguido de merge o rebase) y resolvé ahí cualquier conflicto que aparezca — antes de abrir el PR, no después. Si aparece un conflicto, no lo resuelvas mecánicamente: entendé primero *por qué* existe (¿tocaste un archivo que otro también modificó? ¿hay dos personas resolviendo la misma tarea sin saberlo?) — un conflicto casi nunca debería aparecer si el scope de cada tarea está bien delimitado en el backlog; si aparece seguido, es señal de que dos tareas se están pisando y hay que reordenar el reparto, no solo resolver el conflicto y seguir.
4. **Al terminar una tarea**: con tu rama ya actualizada y sin conflictos, push + Pull Request contra `develop` (nunca contra `main`).
5. **Antes de abrir el PR**: probá tu parte de punta a punta vos mismo. Un PR roto en `develop` bloquea al resto del equipo.
6. **Revisión del PR**: alcanza con que otra persona del equipo lea el diff y lo corra localmente antes de aprobar — no hace falta un proceso de aprobación pesado, pero ningún PR se automerge sin que alguien más lo haya mirado, aunque sea unos minutos.
7. **`develop` es donde se prueba la integración completa.** Cuando varias tareas ya mergeadas ahí funcionan juntas sin romperse, recién ahí se abre un PR de `develop` → `main`.
8. **`main` dispara el despliegue de producción** (el que se muestra en el video final). No se mergea a `main` sobre la fecha límite sin haber probado bien en `develop` antes.

### Convención de commits

Formato: `tipo: descripción corta`, usando estos tipos:
- `feat:` — funcionalidad nueva (ej: `feat: registro de empresa con contexto`)
- `fix:` — corrección de un error (ej: `fix: auditor agent no calculaba fit sin CV`)
- `docs:` — cambios de documentación
- `refactor:` — cambio de código que no altera comportamiento
- `test:` — agregar o corregir pruebas

Un commit no tiene que ser perfecto, pero sí tiene que explicar qué cambió y por qué, sin necesitar abrir el diff para entenderlo.

### Manejo de conflictos de merge

La prevención va antes que la resolución: si el scope de cada tarea del backlog está bien delimitado y nadie toca el trabajo de otro sin coordinar, los conflictos deberían ser raros. Si aparece uno igual, se resuelve **antes** de pushear (ver regla 3 arriba), nunca dejándolo para que lo encuentre quien revisa el PR. Si el conflicto es en un archivo compartido pesado (por ejemplo, algo dentro de `models/`), avisar por el canal del equipo antes de forzar la resolución — puede ser señal de que dos tareas se solapan y conviene reordenar el backlog, no solo resolver el conflicto puntual.

---

## 3. Dónde van las credenciales (GitHub vs. Google Cloud)

Hay dos tipos de credenciales, y van en lugares distintos — no se mezclan:

**1. Credenciales que la aplicación usa mientras corre** (ej: una API key de un servicio de terceros, si en algún momento se agrega alguno): van en **Google Secret Manager**. Cloud Run las lee de ahí en tiempo de ejecución. Nunca se escriben en el código ni se commitean al repo.

**2. Credenciales para que el despliegue automático funcione** (que un push a GitHub dispare un deploy en Google Cloud): se resuelve conectando **Cloud Build directamente al repositorio de GitHub** desde la consola de Google Cloud (integración nativa). Cloud Build usa su propia cuenta de servicio dentro de GCP para desplegar — **no hace falta guardar ninguna credencial de Google dentro de GitHub.**

*(Alternativa, no recomendada para el tiempo que tienen: usar GitHub Actions en vez de Cloud Build requeriría generar una clave de cuenta de servicio y guardarla como Secret en GitHub — Settings → Secrets and variables → Actions. Es un lugar más donde una credencial puede filtrarse por error, así que se descarta a favor de la integración nativa.)*

**Regla simple:** si dudan dónde va algo, la pregunta es "¿esto lo necesita la aplicación corriendo, o lo necesita el proceso de despliegue?" — lo primero va a Secret Manager, lo segundo lo resuelve Cloud Build solo.

**Nunca:**
- Una credencial real en `.env` commiteado (por eso `.env` está en `.gitignore` desde el día 1, y se sube solo `.env.example` con las claves sin valores).
- Una credencial pegada directo en el código "para probar rápido" y después olvidada ahí.

---

## 4. Variables de entorno esperadas

`.env.example` debe listar, como mínimo, las variables que cada quien necesita para levantar el proyecto localmente — sin valores reales:

```
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_REGION=
FIRESTORE_DATABASE_ID=
VERTEX_AI_LOCATION=
```

Si a lo largo del desarrollo aparece una variable nueva, quien la agrega actualiza `.env.example` en el mismo PR — no se documenta "para después".

---

## 5. Infraestructura y entornos de despliegue

Dos servicios de Cloud Run, cada uno alimentado por su rama correspondiente — esto no depende de cuántas personas sean, solo de las dos ramas principales:

- **`rumbo-dev`**: recibe despliegues desde `develop`. Acá se prueba la integración antes de mostrar nada.
- **`rumbo-prod`**: recibe despliegues desde `main`. Es la versión que se graba en el video final y se muestra como prueba de Google Cloud.

Ambos triggers de Cloud Build se configuran una sola vez, al principio (tarea 0.9 del backlog), y de ahí en adelante el despliegue es automático con cada merge.

### Orden de la Fase 0 (no se reparte el resto del backlog hasta que esto esté resuelto)

El orden importa: cada paso habilita al siguiente. No se saltean pasos ni se paralelizan entre sí.

1. **Repositorio en GitHub creado**, con ramas `main` y `develop` y protección de ramas activada (backlog 0.7, 0.8)
2. **Estructura de carpetas** (sección 1 de este documento) creada y subida a `develop`, junto con `requirements.txt`, `.gitignore` y `.env.example` (backlog 0.4, 0.10)
3. **Proyecto GCP** + billing + créditos aplicados, y APIs habilitadas: Vertex AI/Gemini, Firestore, Cloud Run, Pub/Sub (backlog 0.1, 0.2)
4. **Firestore** con las 6 colecciones creadas según el esquema, aunque estén vacías (backlog 0.3)
5. **Cloud Run** con un esqueleto desplegado — responde algo, sin lógica de negocio; requiere que ya exista `main.py` del paso 2 (backlog 0.5)
6. **Cloud Build conectado** a GitHub con ambos triggers: `develop` → `rumbo-dev`, `main` → `rumbo-prod` (backlog 0.9)
7. **Credenciales de runtime** en Secret Manager, si hacen falta (backlog 0.6, 0.11)

Recién con estos 7 puntos resueltos se reparte el resto del backlog en paralelo.

---

## 6. Qué hacer si algo se rompe cerca de la fecha límite

- Si `develop` tiene algo roto y no da el tiempo de arreglarlo bien: **no se mergea a `main`**. Es preferible una versión más chica pero que funcione de punta a punta, a una más completa que se cae en la demo.
- El reglamento no exige que el proyecto esté público/desplegado en el momento exacto de la submission — se puede grabar el video con todo funcionando y después apagar los servicios para no seguir gastando créditos.
- Si el despliegue a `rumbo-prod` falla después de un merge a `main`, no se investiga bajo presión en el momento — se revierte el merge (`git revert`) y se vuelve a intentar con calma, no se parchea en caliente sobre producción.

---

## 7. Checklist final antes de la submission

- [ ] `main` refleja exactamente lo que se muestra en el video — nada se cambia ahí después de grabar.
- [ ] El README permite que alguien externo levante el proyecto sin tener que preguntarle nada al equipo.
- [ ] Ninguna credencial real aparece en el historial de commits (revisar, no asumir).
- [ ] Los dos servicios de Cloud Run pueden apagarse después de grabar el video sin perder nada necesario para la submission.

---

*Este documento se actualiza si el equipo decide cambiar algo del proceso — no es una regla fija e inamovible, pero mientras esté vigente, aplica para todos por igual.*
