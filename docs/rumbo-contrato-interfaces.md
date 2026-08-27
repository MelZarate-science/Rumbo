# Rumbo — Contrato de Interfaces
### Convenciones de nombres y endpoints — de cumplimiento obligatorio para todo el equipo

> Este documento se para entre el esquema de base de datos y los prompts de desarrollo de cada persona. Nadie inventa un nombre de variable, función o endpoint que no esté acá — si hace falta uno nuevo, se agrega a este documento primero y se avisa al equipo, no se decide en solitario dentro de una rama.

---

## 1. Convenciones generales de nombres (Python)

| Elemento | Convención | Ejemplo |
|---|---|---|
| Variables y funciones | `snake_case` | `calcular_score_fit`, `perfil_id` |
| Clases | `PascalCase` | `Perfil`, `RolNormalizado` |
| Constantes | `MAYUSCULAS_CON_GUION_BAJO` | `UMBRAL_FIT_MINIMO = 75` |
| Archivos y módulos | `snake_case`, en inglés o español pero consistente (se eligió **español**, porque el dominio del producto es en español) | `auditor_fit.py`, `firestore_client.py` |
| Nombres de campos en Firestore | `snake_case`, siempre en español, **exactamente como figuran en el esquema de base de datos** | `nombre_empresa`, `rol_normalizado_id` |

**Regla de oro:** los nombres de campos en el código (diccionarios, clases, JSON de requests/responses) tienen que ser **idénticos** a los nombres de campos del esquema de Firestore. Nunca traducir, abreviar, ni cambiar de `snake_case` a `camelCase` en ningún punto del sistema — ni en el backend, ni en el frontend, ni en las respuestas de la API.

---

## 2. Convención de endpoints (REST)

- Sustantivos en plural para los recursos: `/perfiles`, `/empresas`, `/puestos`, `/matches`.
- El verbo lo da el método HTTP (`GET`, `POST`, `PUT`), nunca el nombre del endpoint (nada de `/crear-perfil` o `/get-matches`).
- IDs de recurso en la URL, no en el body: `/perfiles/{perfil_id}`.
- Acciones que no son CRUD puro (como "invitar" o "responder a una invitación") van como sub-recurso con verbo en infinitivo: `/matches/{match_id}/invitar`.

---

## 3. Lista de endpoints (mapeados a las tareas del backlog)

### Perfiles

| Método | Endpoint | Body / Params | Responde | Tarea backlog |
|---|---|---|---|---|
| `POST` | `/perfiles` | `{nombre, apellido, email, telefono}` | `{perfil_id}` | 1.2 |
| `GET` | `/perfiles/{perfil_id}` | — | Documento completo del perfil (sin campos privados si lo pide alguien que no es el propio dueño) | 1.2 |
| `PUT` | `/perfiles/{perfil_id}` | `{nombre?, apellido?, email?, telefono?}` | `{ok: true}` | 1.2 |
| `PUT` | `/perfiles/{perfil_id}/cv` | `{cv_data: {experiencia, formacion, habilidades, proyectos}}` | `{ok: true}` — al guardar, se regenera el `embedding` del perfil | 1.3 |
| `POST` | `/perfiles/{perfil_id}/cv/pdf` | `{}` (usa el `cv_texto_original` ya cargado) | El texto extraído, mapeado a `cv_data` | 3.1 |
| `POST` | `/perfiles/{perfil_id}/cv/generar` | `{busqueda_interes: string opcional}` | `{cv_generado_harvard: string}` | 3.2, 3.3 |
| `GET` | `/perfiles/{perfil_id}/cv/descargar` | — | Archivo PDF | 3.4 |
| `GET` | `/perfiles/{perfil_id}/matches` | — | Lista de `matches` del perfil, con `titulo`, `score`, `roadmap` (array de maps, ver esquema) — **nunca** `nombre_empresa` salvo que el `match` esté en estado `notificado` o posterior | 2.12 |

### Empresas y puestos

| Método | Endpoint | Body / Params | Responde | Tarea backlog |
|---|---|---|---|---|
| `POST` | `/empresas` | `{nombre_empresa, contexto, email_registro}` | `{empresa_id}` | 1.4 |
| `GET` | `/empresas/{empresa_id}` | — | Documento completo de la empresa | 1.4 |
| `PUT` | `/empresas/{empresa_id}` | `{nombre_empresa?, contexto?}` | `{ok: true}` | 1.4 |
| `POST` | `/empresas/{empresa_id}/puestos` | `{titulo, descripcion}` | `{puesto_id}` | 1.5 |
| `GET` | `/empresas/{empresa_id}/puestos` | — | Lista de puestos de esa empresa | 1.5 |
| `PUT` | `/puestos/{puesto_id}` | `{titulo?, descripcion?, activo?}` | `{ok: true}` — si cambia `descripcion`, se vuelve a correr la clasificación y extracción de requisitos | 1.5 |
| `GET` | `/empresas/{empresa_id}/mapa-perfiles` | `?puesto_id=` (opcional) | Lista de `matches` con `nombre` (sin apellido), `score`, `cv_data` — nunca `apellido`, `email`, `telefono` salvo `estado = confirmado` | 4.1 |

### Matches (el corazón del flujo de invitación)

| Método | Endpoint | Body / Params | Responde | Tarea backlog |
|---|---|---|---|---|
| `POST` | `/matches/{match_id}/invitar` | `{}` (acción manual de la empresa) | `{ok: true, estado: "notificado"}` | 4.2 |
| `POST` | `/matches/{match_id}/responder` | `{aceptar: boolean}` | `{ok: true, estado: "confirmado" \| "rechazado"}` | 4.4 |
| `GET` | `/matches/{match_id}` | — | Documento completo del match, con visibilidad de campos según `estado` (ver esquema de datos) | 2.10 |

---

## 4. Convención de nombres de funciones internas (por módulo)

Cada módulo del backend expone funciones con nombres predecibles — así, quien escriba un endpoint sabe de antemano cómo se va a llamar la función que necesita, sin tener que leer el código de otra persona primero.

| Módulo | Función | Qué hace | ¿Usa Gemini? |
|---|---|---|---|
| `agents/clasificador_roles.py` | `clasificar_puesto(puesto_id)` | Asigna `rol_normalizado_id` al puesto (crea el rol si no existe uno cercano) | ✅ sí |
| `agents/extractor_requisitos.py` | `extraer_requisitos(puesto_id)` | Extrae requisitos discretos, los reconcilia contra `requisitos_normalizados` y actualiza frecuencias | ✅ sí |
| `agents/auditor_fit.py` | `calcular_score_y_roadmap(perfil_id, puesto_id)` | Devuelve `{score, roadmap, justificacion}` — `roadmap` con la subestructura de maps del esquema, nunca strings sueltos | ✅ sí |
| `pipeline/matching_pipeline.py` | `ejecutar_pipeline_matching(perfil_id)` | Corre el retrieval de dos niveles y dispara el auditor por cada puesto candidato. **No es un agente**: secuencia fija en código | ❌ no |
| `pipeline/matching_pipeline.py` | `ejecutar_pipeline_indexado(puesto_id)` | Al cargarse un puesto: lo clasifica y le extrae los requisitos | ❌ no |
| `services/retrieval.py` | `buscar_roles_afines(perfil_id)` | **Nivel 1**: `find_nearest()` del embedding del perfil contra `roles_normalizados`. Devuelve lista de `rol_normalizado_id` | ❌ no |
| `services/retrieval.py` | `buscar_puestos_de_roles(roles_ids)` | **Nivel 2**: filtro simple de `puestos` por `rol_normalizado_id`. Devuelve lista de `puesto_id` | ❌ no |
| `services/invitaciones.py` | `enviar_invitacion(match_id)` / `procesar_respuesta(match_id, aceptar)` | Cambia el `estado` del match y gestiona qué campos se revelan a cada lado | ❌ no |
| `services/invitaciones.py` | `filtrar_campos_visibles(perfil, estado_match)` | Aplica la regla de visibilidad escalonada sobre un perfil | ❌ no |
| `services/embeddings.py` | `generar_embedding(texto)` | Devuelve el vector, sin importar si es para un perfil o un rol | ❌ no |
| `services/normalizacion.py` | `actualizar_frecuencias(rol_id, requisitos_ids)` / `obtener_frecuencias(rol_id)` | Operaciones de lectura/escritura sobre la tabla de frecuencias | ❌ no |
| `services/firestore_client.py` | `obtener(coleccion, doc_id)` / `crear(coleccion, datos)` / `actualizar(coleccion, doc_id, datos)` / `listar(coleccion, filtros)` | Wrappers genéricos, usados por todos los módulos | ❌ no |
| `services/cv_generator.py` | `generar_cv_harvard(cv_data, busqueda_interes=None)` | Devuelve el texto del CV formateado | ✅ sí |

**Sobre la columna "¿Usa Gemini?":** solo lo que está en `agents/` (más el generador de CV) hace llamadas de razonamiento al modelo. Todo lo demás es determinístico — esa separación es deliberada y es lo que mantiene bajo el costo y la latencia del sistema.

**Regla de oro:** nadie llama a Firestore directamente desde un endpoint o un agente — siempre a través de `services/firestore_client.py`. Esto evita que cada integrante escriba su propia forma de leer/escribir la misma colección.

---

## 5. Formato estándar de respuestas de error

Todos los endpoints, sin excepción, devuelven errores con esta forma:

```json
{
  "error": true,
  "mensaje": "Descripción legible del problema",
  "codigo": "PERFIL_NO_ENCONTRADO"
}
```

`codigo` es un string en `MAYUSCULAS_CON_GUION_BAJO`, específico del caso (no un código HTTP genérico). Cada quien que agregue un caso de error nuevo, define su propio `codigo` siguiendo este patrón y lo suma a este documento.

---

## 6. Qué hacer si hace falta un endpoint o campo que no está acá

1. Se avisa al equipo (no se decide en solitario dentro de una rama).
2. Se agrega a este documento, con el mismo formato de tabla que las secciones de arriba.
3. Recién ahí se escribe el código que lo usa.

Este documento es la fuente de verdad de nombres — si el código y este documento no coinciden, gana este documento, y el código se corrige.

---

*Este contrato es lo que permite que los prompts de desarrollo de cada integrante se armen en paralelo sin que nadie tenga que adivinar cómo llamó otro a algo. El esqueleto del repo ya refleja estos nombres.*
