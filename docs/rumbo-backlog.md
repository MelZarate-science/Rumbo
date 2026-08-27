# Rumbo — Backlog de Desarrollo (v2, reordenado)
### All Things Agentic Hackathon 2026 · 8 días restantes

> **Nota sobre la columna "Quién":** las etiquetas Persona A / Persona B son provisorias, de cuando el equipo era de dos. Con cuatro integrantes hay que reasignarlas antes de arrancar — la columna indica *cuántos frentes distintos* tiene cada fase, no quién específicamente.

> Reordenado para priorizar lo que da valor demostrable más rápido: primero los datos (registro), después el motor de afinidad completo (que es el corazón del producto y lo menos riesgoso de mostrar), y recién con eso funcionando se suman CV asistido y la visibilidad escalonada de dos lados.

**Prioridades:** 🔴 Imprescindible para submission · 🟡 Suma valor si hay tiempo · ⚪ Bonus/fase futura

---

## FASE 0 — Infraestructura base (hacer primero, sin repartir)

| ID | Tarea | Quién | Prioridad | Depende de | Hecho cuando... |
|---|---|---|---|---|---|
| 0.1 | Crear proyecto en GCP, habilitar billing, aplicar créditos del hackathon | Ambos | 🔴 | — | El proyecto existe en la consola y los créditos están acreditados |
| 0.2 | Habilitar APIs: Vertex AI/Gemini, Firestore (con soporte vectorial), Cloud Run, Pub/Sub | Ambos | 🔴 | 0.1 | Las APIs aparecen "habilitadas" en la consola |
| 0.3 | Crear las 6 colecciones de Firestore según el esquema (`empresas`, `puestos`, `perfiles`, `matches`, `roles_normalizados`, `requisitos_normalizados`) | Persona A | 🔴 | 0.2 | Las colecciones existen, con sus campos documentados |
| 0.4 | Estructura de carpetas del repo (ver detalle completo en `rumbo-flujo-trabajo.md`, sección 1) + `requirements.txt`, entorno virtual, `.gitignore` | Persona A | 🔴 | 0.7 | La estructura de carpetas existe vacía en `develop` y `pip install -r requirements.txt` corre sin errores en una máquina limpia |
| 0.5 | Esqueleto de Cloud Run desplegado ("hola mundo", sin lógica todavía) | Persona A | 🔴 | 0.2, 0.4 | Hay una URL `.run` pública que responde, visible en consola |
| 0.6 | Configurar Secret Manager / variables de entorno para credenciales | Persona A | 🔴 | 0.5 | Ninguna credencial hardcodeada ni commiteada |
| 0.7 | Crear repositorio en GitHub con ramas `main` y `develop` | Persona A | 🔴 | — | El repo existe con ambas ramas creadas |
| 0.8 | Configurar protección de ramas: nadie puede pushear directo a `main` ni `develop`, solo vía Pull Request | Persona A | 🔴 | 0.7 | Un push directo a esas ramas es rechazado por GitHub |
| 0.9 | Conectar Cloud Build a GitHub (integración nativa) con dos triggers: push a `develop` → despliega a `rumbo-dev`; push a `main` → despliega a `rumbo-prod` | Persona A | 🔴 | 0.5 | Un push de prueba a cada rama dispara el despliegue correspondiente, visible en consola |
| 0.10 | Crear `.env.example` (plantilla sin valores reales) y confirmar que el `.env` real está en `.gitignore` | Persona A | 🔴 | 0.4 | El archivo de ejemplo está en el repo; ningún valor real de credencial aparece en ningún commit |
| 0.11 | Cargar en Google Secret Manager cualquier credencial que la app necesite en tiempo de ejecución (más allá de la autenticación nativa de GCP) | Persona A | 🟡 | 0.6 | Las credenciales están en Secret Manager, vinculadas al servicio de Cloud Run, no en el código |
| 0.12 | Documentar en el README qué variables de entorno son necesarias y de dónde se obtienen | Persona B | 🔴 | 0.10 | Alguien externo podría configurar su propio entorno siguiendo el README, sin adivinar nada |

---

## FASE 1 — Registro y perfiles (usuarios y empresas)

Sin esto no hay datos con qué probar nada del resto. Se hace completo antes de avanzar.

| ID | Tarea | Quién | Prioridad | Depende de | Hecho cuando... |
|---|---|---|---|---|---|
| 1.1 | Login/autenticación básica (puede ser simple, sin OAuth complejo) | Persona A | 🔴 | 0.5 | Un usuario o empresa puede iniciar sesión y mantener su sesión activa |
| 1.2 | Registro de perfil de usuario: nombre, apellido, email, teléfono | Persona A | 🔴 | 0.3, 1.1 | Un documento en `perfiles` queda creado con los datos básicos |
| 1.3 | Carga de `cv_data` estructurado: experiencia, formación, habilidades, proyectos (formulario, no PDF todavía) | Persona A | 🔴 | 1.2 | Los cuatro arrays de `cv_data` se guardan con su subestructura completa (fechas, descripciones) |
| 1.4 | Registro de perfil de empresa: nombre, contexto (system prompt), email de registro | Persona A | 🔴 | 0.3, 1.1 | Un documento en `empresas` queda creado |
| 1.5 | Carga de puesto por parte de la empresa: título, descripción libre | Persona A | 🔴 | 1.4 | Un documento en `puestos` queda creado, vinculado a su empresa |
| 1.6 | Pantallas mínimas de registro (usuario y empresa) — solo lo justo para cargar datos, sin diseño final todavía | Persona B | 🔴 | 1.2, 1.4, 1.5 | Se puede completar todo el registro desde una interfaz, no solo desde Postman |

---

## FASE 2 — Motor de afinidad completo (score + roadmap)

El corazón del producto. Incluye la capa intermedia de roles y requisitos normalizados. Se prueba con datos ficticios generados a propósito, no esperando usuarios reales.

| ID | Tarea | Quién | Prioridad | Depende de | Hecho cuando... |
|---|---|---|---|---|---|
| 2.1 | Poblar la base con perfiles y empresas/puestos ficticios variados (al menos 5-6 perfiles, 3-4 empresas con 1-2 puestos cada una) | Persona B | 🔴 | Fase 1 completa | Hay datos suficientes y variados para que el motor tenga con qué trabajar |
| 2.2 | Generación de embedding de `cv_data` al registrar un perfil | Persona A | 🔴 | 1.3, 0.2 | Cada perfil tiene su campo `embedding` poblado |
| 2.3 | Agente 1 · Clasificador de roles: asigna `rol_normalizado_id` al cargar un puesto (crea el rol si no existe uno cercano) | Persona A | 🔴 | 1.5 | Cada puesto queda vinculado a un rol; `roles_normalizados` se puebla progresivamente |
| 2.4 | Generación de embedding de `descripcion_consolidada` en cada rol normalizado | Persona A | 🔴 | 2.3 | Cada rol tiene su campo `embedding` poblado |
| 2.5 | Agente 2 · Extractor de requisitos: extrae `requisitos_extraidos` por puesto + matching contra `requisitos_normalizados` (crear entidad si no existe) | Persona A | 🔴 | 2.3 | Cada puesto tiene su lista de requisitos referenciados por ID |
| 2.6 | Actualización de `requisitos_frecuencia` y `requisitos_ids` en el rol correspondiente cada vez que se carga un puesto nuevo | Persona A | 🔴 | 2.5 | Los porcentajes de frecuencia se recalculan correctamente |
| 2.7 | Retrieval Nivel 1: `find_nearest()` del embedding del perfil contra `roles_normalizados` | Persona A | 🔴 | 2.2, 2.4 | Devuelve los 1-3 roles más afines a un perfil dado |
| 2.8 | Retrieval Nivel 2: filtro simple de `puestos` por `rol_normalizado_id` sobre los roles obtenidos | Persona A | 🔴 | 2.7 | Devuelve los puestos reales de esos roles, sin costo de vector |
| 2.9 | Agente 3 · Auditor de fit: score + roadmap cuantitativo por puesto, usando `requisitos_frecuencia` como referencia de mercado | Persona A | 🔴 | 2.8, 2.6 | Devuelve `{score, roadmap, justificacion}` — `roadmap` con la subestructura de maps del esquema (`requisito_id`, `cumplido`, `porcentaje_mercado`, `especifico_de_esta_empresa`), nunca strings sueltos |
| 2.10 | Guardar resultado en `matches` (estado `pendiente`) | Persona A | 🔴 | 2.9 | Cada evaluación queda persistida y consultable |
| 2.11 | Disparo automático: al registrarse un perfil nuevo, correr 2.7 a 2.10 sin acción manual | Persona A | 🟡 | 2.10, 0.2 (Pub/Sub) | El perfil ve sus matches apenas entra, sin haber pedido nada |
| 2.12 | Pantalla del perfil: sección "posiciones más afines" (las 3 detectadas) | Persona B | 🔴 | 2.10 | Se ven al entrar, sin botón de búsqueda |
| 2.13 | Pantalla de detalle de posición: score + roadmap + vista de red de requisitos (comunes vs. raros) | Persona B | 🔴 | 2.12 | Se navega del listado al detalle sin errores; la vista de red se distingue de una lista plana |

---

## FASE 3 — Generación de CV asistida por IA

| ID | Tarea | Quién | Prioridad | Depende de | Hecho cuando... |
|---|---|---|---|---|---|
| 3.1 | Carga de CV por PDF: extracción de texto y mapeo a la estructura de `cv_data` | Persona B | 🟡 | 1.3 | El contenido del PDF queda parseado en el mismo formato que la carga manual |
| 3.2 | Generación de CV en formato Harvard a partir de `cv_data`, con Gemini | Persona B | 🟡 | 1.3 o 3.1 | El sistema devuelve un CV formateado |
| 3.3 | Adaptación del CV generado a una búsqueda puntual indicada por el usuario | Persona B | 🟡 | 3.2 | El CV cambia según el puesto de interés indicado |
| 3.4 | Exportar el CV generado a PDF descargable | Persona B | 🟡 | 3.2 | El usuario puede descargar el archivo |
| 3.5 | Entrada por voz (agente conversacional) | — | ⚪ | 1.3 | Fuera del MVP salvo que sobre tiempo real |

---

## FASE 4 — Visibilidad escalonada + invitación manual (matching a ciegas en los dos sentidos)

| ID | Tarea | Quién | Prioridad | Depende de | Hecho cuando... |
|---|---|---|---|---|---|
| 4.1 | Vista de "mapa de perfiles" para la empresa: nombre de pila, % de fit, `cv_data` — sin apellido ni contacto | Persona B | 🔴 | Fase 2 completa | La empresa ve exactamente lo permitido, nada más |
| 4.2 | Acción manual de la empresa: botón "invitar" sobre un perfil puntual del mapa | Persona B | 🔴 | 4.1 | Al invitar, el `match` pasa de `pendiente` a `notificado` |
| 4.3 | Al pasar a `notificado`, revelar al perfil el nombre de la empresa + detalle completo del puesto | Persona A | 🔴 | 4.2 | El perfil ve la invitación con la identidad de la empresa, cosa que antes no veía |
| 4.4 | Botón de aceptar/rechazar la invitación del lado del perfil | Persona B | 🔴 | 4.3 | El estado pasa a `confirmado` o `rechazado` según la respuesta |
| 4.5 | Al confirmar, revelar a la empresa apellido + contacto del perfil (que pasa a ser "candidato") | Persona A | 🔴 | 4.4 | La empresa ve los datos completos solo después de la confirmación |

---

## FASE 5 — Pruebas de punta a punta

| ID | Tarea | Quién | Prioridad | Depende de | Hecho cuando... |
|---|---|---|---|---|---|
| 5.1 | Correr el flujo completo (registro → matching → invitación → opt-in) al menos 3 veces sin intervención manual fuera de lo esperado | Ambos | 🔴 | Fases 1-4 completas | El flujo corre sin errores de punta a punta |
| 5.2 | Revisar manejo de errores (CV vacío, perfil incompleto, sin matches, empresa sin puestos) | Persona A | 🟡 | 5.1 | El sistema no se rompe ante estos casos, responde con mensaje claro |

---

## FASE 6 — Documentación y submission

| ID | Tarea | Quién | Prioridad | Depende de | Hecho cuando... |
|---|---|---|---|---|---|
| 6.1 | README con spin-up instructions reproducibles | Persona B | 🔴 | Fase 0 estable | Alguien externo podría levantar el proyecto siguiendo el README |
| 6.2 | Diagrama de arquitectura final (con el esquema de datos y el retrieval de dos niveles) | Persona B | 🔴 | Arquitectura estable | El diagrama refleja el sistema real |
| 6.3 | Descripción de texto de la submission (features, stack, fuentes de datos, aprendizajes) | Persona B | 🔴 | Proyecto casi terminado | Cubre los 4 puntos que pide Devpost |
| 6.4 | Definir repo público o privado; si es privado, dar acceso a testing@devpost.com y cloudhackathons@google.com | Ambos | 🔴 | — | El acceso está confirmado antes del 31/8 |

---

## FASE 7 — Video demo

| ID | Tarea | Quién | Prioridad | Depende de | Hecho cuando... |
|---|---|---|---|---|---|
| 7.1 | Guion (~4 min): problema → registro → score/roadmap → invitación → opt-in → prueba de Cloud | Persona B | 🔴 | Fase 5 completa | El guion cabe en el tiempo, con foco en mostrar, no explicar |
| 7.2 | Grabar con prueba visible de Google Cloud (consola, logs, o URL `.run`) | Persona B | 🔴 | 7.1 | La grabación existe y muestra la prueba de despliegue |
| 7.3 | Editar y subir a YouTube/Vimeo, público, en inglés o con subtítulos | Persona B | 🔴 | 7.2 | El link es público y funciona |

---

## FASE 8 — Bonus (solo si todo lo anterior está cerrado)

| ID | Tarea | Quién | Prioridad |
|---|---|---|---|
| 8.1 | Contenido público sobre cómo se construyó | — | ⚪ |
| 8.2 | Post en redes con el hashtag del hackathon | — | ⚪ |
| 8.3 | Integrar otro modelo de Google AI (Gemma/Veo/Lyria) | — | ⚪ |

---

## Decisiones aún abiertas

- Nombre final del proyecto (Posta / Rumbo / Encaje / Norte) — no bloquea desarrollo, pero sí naming de repo y servicios.
- Reasignar la columna "Quién" al equipo real de cuatro integrantes.
- Cuánto de la normalización de requisitos (Fase 2) entra completo al MVP vs. queda simplificado si el tiempo aprieta — ver nota de scope en el esquema de base de datos.

---

*Backlog reordenado para reflejar la secuencia: registro → motor de afinidad → CV asistido → visibilidad de dos lados. Cada fila sigue siendo la base para armar el prompt de desarrollo de cada persona.*
