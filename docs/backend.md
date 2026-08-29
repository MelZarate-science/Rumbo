# Rumbo — Roadmap de Backend para MVP

> Objetivo: dejar un backend funcional, simple y mantenible para el MVP, usando **FastAPI + Firestore** como base.  
> Cambio de alcance: se evita depender fuertemente de Google Cloud más allá de Firestore. Todo lo que sea Vertex AI, Pub/Sub, Cloud Run u orquestación avanzada queda fuera del camino crítico del MVP.

## 1. Qué debe resolver el backend del MVP

El backend tiene que permitir este flujo mínimo:

1. Crear un perfil.
2. Guardar su CV estructurado.
3. Crear empresas y puestos.
4. Clasificar puestos por rol.
5. Extraer requisitos de cada puesto.
6. Calcular matches entre perfil y puesto.
7. Exponer resultados con privacidad básica.

Si una parte no aporta a ese flujo, no entra en el MVP.

## 2. Alcance técnico del MVP

### Sí entra

- API REST con FastAPI.
- Persistencia en Firestore.
- Modelos Pydantic para validar datos.
- Matching básico entre perfil y puesto.
- Roadmap cuantitativo simple.
- Visibilidad escalonada de datos sensibles.
- Seed data para probar el sistema.
- Tests básicos de las rutas y lógica central.

### No entra por ahora

- Pub/Sub.
- Cloud Run como requisito del diseño.
- Vertex AI / Gemini como dependencia obligatoria.
- Agentes con orquestación compleja.
- PDFs, generación Harvard y features asistidas por IA si retrasan el MVP.
- Paneles frontend completos.

## 3. Estado actual del proyecto

En el repo la implementación activa del backend vive en `backend/`:

- `backend/api/routes/` para HTTP.
- `backend/models/` para modelos internos.
- `backend/schemas/` para request/response.
- `backend/services/` para lógica y Firestore.
- `backend/pipeline/` para orquestación.
- `backend/agents/` para clasificación, extracción y auditoría.

`frontend/` queda separado en la raíz. `main.py` y `routes/` se mantienen sólo
como compatibilidad para imports viejos.

## 4. Hoja de ruta del MVP

### Fase 1. Base de datos y acceso

Prioridad máxima.

- Implementar `services/firestore_client.py`.
- Definir el mapeo entre modelos Pydantic y documentos Firestore.
- Resolver `crear`, `obtener`, `actualizar` y `listar`.
- Normalizar timestamps, IDs y serialización.
- Agregar manejo de errores consistente.

**Salida esperada:** se pueden crear y leer perfiles, empresas, puestos y matches sin tocar Firestore directamente desde otros módulos.

### Fase 2. Modelo `Perfil` y carga de datos

El archivo `models/perfil.py` debe quedar seguro para uso real.

- Reemplazar defaults mutables por `default_factory`.
- Validar `email`, `telefono` y fechas.
- Separar datos privados de datos públicos cuando haga falta.
- Mantener `cv_data` como estructura validada, no como JSON libre.

**Salida esperada:** un perfil se puede crear, actualizar y leer sin riesgo de estado compartido entre instancias.

### Fase 3. CRUD mínimo de negocio

- `POST /perfiles`
- `GET /perfiles/{perfil_id}`
- `PUT /perfiles/{perfil_id}`
- `PUT /perfiles/{perfil_id}/cv`
- `POST /empresas`
- `POST /empresas/{empresa_id}/puestos`
- `GET /puestos` o `GET /empresas/{empresa_id}/puestos`
- `GET /matches/{match_id}` si ya existen matches

**Salida esperada:** cargar datos base desde API o tests sin depender de scripts manuales.

### Fase 4. Matching básico

- Implementar generación de embedding solo si realmente se usa en el MVP.
- Implementar retrieval simple.
- Implementar clasificador de roles.
- Implementar extractor de requisitos.
- Implementar auditor de fit.
- Guardar matches con `estado = pendiente`.

**Salida esperada:** al registrar un perfil o cargar un puesto, se pueden generar matches consultables.

### Fase 5. Privacidad y estados

- Ocultar apellido, email y teléfono antes de `confirmado`.
- Mostrar empresa y puesto sólo cuando corresponda.
- Manejar `pendiente`, `notificado`, `confirmado` y `rechazado`.
- Definir respuestas públicas y privadas separadas.

**Salida esperada:** la API no filtra datos sensibles por accidente.

### Fase 6. Calidad mínima para producción

- Tests unitarios de servicios.
- Tests de rutas principales.
- Seed data reproducible.
- Logging claro.
- Variables de entorno documentadas.
- Manejo de errores con mensajes y códigos consistentes.

**Salida esperada:** se puede validar el backend localmente antes de subirlo.

## 5. Prioridad real de implementación

Si hay poco tiempo, el orden correcto es este:

1. Firestore client.
2. Modelo `Perfil` saneado.
3. CRUD de perfiles, empresas y puestos.
4. Matches persistidos.
5. Privacidad por estado.
6. Matching básico.
7. Tests y seed data.

Todo lo demás es secundario.

## 6. Decisiones concretas para este proyecto

- Firestore es la única base de datos obligatoria.
- No se construye una arquitectura distribuida para el MVP.
- No se fuerza IA generativa donde alcanza con lógica de negocio.
- No se mete complejidad de infraestructura antes de tener flujo funcional.
- Los agentes quedan como evolución, no como requisito de arranque.

## 7. Criterio de terminado para el MVP

El backend está listo para el MVP cuando:

- Se puede crear un perfil con datos válidos.
- Se puede guardar y leer su `cv_data`.
- Se puede crear una empresa y un puesto.
- Se puede generar al menos un match persistido.
- Se respeta la privacidad mínima del perfil.
- Los endpoints principales responden sin errores.
- Hay tests básicos que cubren el flujo crítico.

## 8. Riesgos a vigilar

- Defaults mutables en los modelos.
- Mezclar datos públicos y privados en una sola respuesta.
- Acoplar el backend a Google Cloud más de lo necesario.
- Meter IA antes de tener CRUD confiable.
- No tener tests para el flujo de visibilidad.

## 9. Próximo paso recomendado

Implementar primero la capa `firestore_client.py` y luego corregir `models/perfil.py`, porque esas dos piezas destraban todo lo demás.
