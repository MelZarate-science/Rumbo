"""
Puebla la base con datos ficticios para probar el motor de matching.

Backlog: tarea 2.1
Objetivo: 6 perfiles variados y 6 empresas con 9 puestos en total, con dos
solapamientos deliberados entre empresas distintas (mismo rol real, título y
redacción distintos) para que `roles_normalizados` tenga roles con más de un
puesto -- si no, las frecuencias de mercado siempre dan 100% y no hay forma de
ver la separación "estándar del mercado" vs. "particular de esta empresa".
También incluye un caso negativo (Product Manager vs. Product Marketing
Manager) para confirmar que el clasificador NO fusiona roles parecidos en el
nombre pero distintos en el fondo -- ver `Auditoria-Rumbo-Normalizacion.md`
(fuera del repo) para el detalle de por qué se armó así.

Uso:
    export GOOGLE_CLOUD_PROJECT=tu-proyecto
    export FIRESTORE_EMULATOR_HOST=localhost:8080  # opcional, para emulador local
    python -m scripts.seed_data
"""

import sys
from datetime import UTC, datetime

from models.empresa import Empresa
from models.perfil import CvData, ExperienciaItem, FormacionItem, Perfil, ProyectoItem
from models.puesto import Puesto
from services.auth import hashear_password
from services.firestore_client import crear, FirestoreError

PASSWORD_DEMO = "rumbo2026"


def _perfil_ana() -> Perfil:
    return Perfil(
        nombre="Ana",
        apellido="García",
        email="ana.garcia@email.com",
        telefono="+34 600 111 222",
        cv_texto_original="Desarrolladora Python con 5 años en backend y APIs.",
        cv_data=CvData(
            experiencia=[
                ExperienciaItem(
                    puesto="Backend Developer",
                    empresa="TechCorp",
                    descripcion="Diseño y mantenimiento de APIs REST con FastAPI, PostgreSQL, Docker. Testing con pytest. CI/CD GitHub Actions.",
                    fecha_desde=datetime(2020, 3, 1, tzinfo=UTC),
                    fecha_hasta=datetime(2023, 6, 1, tzinfo=UTC),
                ),
                ExperienciaItem(
                    puesto="Senior Backend Engineer",
                    empresa="DataFlow",
                    descripcion="Arquitectura de microservicios, mensajería con RabbitMQ, observabilidad con Prometheus/Grafana. Python, Go.",
                    fecha_desde=datetime(2023, 7, 1, tzinfo=UTC),
                    actual=True,
                ),
            ],
            formacion=[
                FormacionItem(
                    titulo="Ingeniería Informática",
                    institucion="Universidad Politécnica",
                    fecha_desde=datetime(2015, 9, 1, tzinfo=UTC),
                    fecha_hasta=datetime(2019, 6, 1, tzinfo=UTC),
                )
            ],
            habilidades=["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "pytest", "RabbitMQ", "Go"],
            proyectos=[
                ProyectoItem(
                    nombre="API de pagos",
                    descripcion="Servicio de pagos idempotente con Stripe, webhook handling, conciliación automática.",
                    fecha=datetime(2022, 5, 1, tzinfo=UTC),
                    link="https://github.com/ana/payments-api",
                )
            ],
        ),
        busqueda_interes="Backend / Arquitectura de sistemas",
    )


def _perfil_carlos() -> Perfil:
    return Perfil(
        nombre="Carlos",
        apellido="Ruiz",
        email="carlos.ruiz@email.com",
        telefono="+34 600 333 444",
        cv_texto_original="Fullstack con foco en React y Node, moviéndome a Python.",
        cv_data=CvData(
            experiencia=[
                ExperienciaItem(
                    puesto="Fullstack Developer",
                    empresa="StartupXYZ",
                    descripcion="Frontend React/TypeScript, backend Node/Express, base de datos MongoDB. Despliegue en Vercel y AWS.",
                    fecha_desde=datetime(2021, 1, 1, tzinfo=UTC),
                    actual=True,
                )
            ],
            formacion=[
                FormacionItem(
                    titulo="Bootcamp Fullstack",
                    institucion="CodeAcademy",
                    fecha_desde=datetime(2020, 3, 1, tzinfo=UTC),
                    fecha_hasta=datetime(2020, 9, 1, tzinfo=UTC),
                )
            ],
            habilidades=["JavaScript", "TypeScript", "React", "Node.js", "Express", "MongoDB", "HTML", "CSS", "Python", "SQL"],
            proyectos=[
                ProyectoItem(
                    nombre="E-commerce demo",
                    descripcion="Tienda online con carrito, pagos mock, panel admin. React + Node.",
                    fecha=datetime(2021, 6, 1, tzinfo=UTC),
                )
            ],
        ),
        busqueda_interes="Fullstack / Python backend",
    )


def _perfil_laura() -> Perfil:
    return Perfil(
        nombre="Laura",
        apellido="Martín",
        email="laura.martin@email.com",
        telefono="+34 600 555 666",
        cv_texto_original="Data Scientist con experiencia en ML y pipelines de datos.",
        cv_data=CvData(
            experiencia=[
                ExperienciaItem(
                    puesto="Data Scientist",
                    empresa="InsightAI",
                    descripcion="Modelado predictivo con scikit-learn, XGBoost. Pipelines Airflow, feature engineering, A/B testing. Python, SQL, Pandas.",
                    fecha_desde=datetime(2019, 6, 1, tzinfo=UTC),
                    actual=True,
                )
            ],
            formacion=[
                FormacionItem(
                    titulo="Máster en Data Science",
                    institucion="Universidad Carlos III",
                    fecha_desde=datetime(2017, 9, 1, tzinfo=UTC),
                    fecha_hasta=datetime(2019, 6, 1, tzinfo=UTC),
                )
            ],
            habilidades=["Python", "Pandas", "NumPy", "scikit-learn", "XGBoost", "SQL", "Airflow", "MLflow", "Tableau"],
            proyectos=[
                ProyectoItem(
                    nombre="Churn prediction",
                    descripcion="Modelo de predicción de abandono de clientes, 87% recall. Deploy como API FastAPI.",
                    fecha=datetime(2022, 11, 1, tzinfo=UTC),
                    link="https://github.com/laura/churn",
                )
            ],
        ),
        busqueda_interes="Data Science / ML Engineering",
    )


def _perfil_miguel() -> Perfil:
    return Perfil(
        nombre="Miguel",
        apellido="Torres",
        email="miguel.torres@email.com",
        telefono="+34 600 777 888",
        cv_texto_original="DevOps / SRE con foco en Kubernetes y cloud nativo.",
        cv_data=CvData(
            experiencia=[
                ExperienciaItem(
                    puesto="Platform Engineer",
                    empresa="CloudNative Inc",
                    descripcion="Kubernetes en EKS/GKE, Helm, ArgoCD, Terraform. Observabilidad completa: Loki, Tempo, Prometheus. Go, Python.",
                    fecha_desde=datetime(2020, 8, 1, tzinfo=UTC),
                    actual=True,
                )
            ],
            formacion=[
                FormacionItem(
                    titulo="Ingeniería de Sistemas",
                    institucion="Universidad de Sevilla",
                    fecha_desde=datetime(2014, 9, 1, tzinfo=UTC),
                    fecha_hasta=datetime(2018, 6, 1, tzinfo=UTC),
                )
            ],
            habilidades=["Kubernetes", "Docker", "Terraform", "Helm", "ArgoCD", "Prometheus", "Grafana", "Go", "Python", "AWS", "GCP"],
            proyectos=[
                ProyectoItem(
                    nombre="Cluster multi-region",
                    descripcion="Diseño y despliegue de clúster GKE multi-región con failover automático.",
                    fecha=datetime(2023, 2, 1, tzinfo=UTC),
                )
            ],
        ),
        busqueda_interes="Platform Engineering / SRE",
    )


def _perfil_sofia() -> Perfil:
    return Perfil(
        nombre="Sofía",
        apellido="López",
        email="sofia.lopez@email.com",
        telefono="+34 600 999 000",
        cv_texto_original="Frontend specialist, React/Next.js, accesibilidad y performance.",
        cv_data=CvData(
            experiencia=[
                ExperienciaItem(
                    puesto="Frontend Engineer",
                    empresa="PixelPerfect",
                    descripcion="Next.js, TypeScript, Tailwind, testing con Playwright. Core Web Vitals optimization. Design systems.",
                    fecha_desde=datetime(2021, 5, 1, tzinfo=UTC),
                    actual=True,
                )
            ],
            formacion=[
                FormacionItem(
                    titulo="Diseño y Desarrollo Web",
                    institucion="Escuela de Arte",
                    fecha_desde=datetime(2018, 9, 1, tzinfo=UTC),
                    fecha_hasta=datetime(2021, 6, 1, tzinfo=UTC),
                )
            ],
            habilidades=["React", "Next.js", "TypeScript", "Tailwind", "Playwright", "Jest", "Storybook", "Figma", "Accesibilidad"],
            proyectos=[
                ProyectoItem(
                    nombre="Design system corporativo",
                    descripcion="Librería de componentes React documentada en Storybook, adoptada por 5 equipos.",
                    fecha=datetime(2022, 9, 1, tzinfo=UTC),
                )
            ],
        ),
        busqueda_interes="Frontend / Design Systems",
    )


def _perfil_jorge() -> Perfil:
    return Perfil(
        nombre="Jorge",
        apellido="Sánchez",
        email="jorge.sanchez@email.com",
        telefono="+34 600 222 333",
        cv_texto_original="Backend Java/Spring, migración a cloud, microservicios.",
        cv_data=CvData(
            experiencia=[
                ExperienciaItem(
                    puesto="Java Developer",
                    empresa="BancaDigital",
                    descripcion="Spring Boot, JPA/Hibernate, Kafka, PostgreSQL. Migración de monolitho a microservicios en OpenShift.",
                    fecha_desde=datetime(2018, 2, 1, tzinfo=UTC),
                    actual=True,
                )
            ],
            formacion=[
                FormacionItem(
                    titulo="Ingeniería Informática",
                    institucion="Universidad Complutense",
                    fecha_desde=datetime(2013, 9, 1, tzinfo=UTC),
                    fecha_hasta=datetime(2017, 6, 1, tzinfo=UTC),
                )
            ],
            habilidades=["Java", "Spring Boot", "Kafka", "PostgreSQL", "JPA", "Docker", "OpenShift", "JUnit", "Maven"],
            proyectos=[
                ProyectoItem(
                    nombre="Core bancario modular",
                    descripcion="Descomposición de módulos de cuentas, tarjetas, préstamos en servicios independientes.",
                    fecha=datetime(2022, 3, 1, tzinfo=UTC),
                )
            ],
        ),
        busqueda_interes="Backend Java / Arquitectura cloud",
    )


def _empresas_y_puestos():
    """
    Devuelve lista de (Empresa, [Puesto, ...]).

    Solapamiento deliberado #1 -- rol "Backend Python", 3 empresas, 3 títulos y
    redacciones distintas (TechNova, DataMind, FinTech Solutions): debería
    normalizarse a un único `rol_normalizado` con `cantidad_puestos = 3`.

    Solapamiento deliberado #2 -- rol "Platform/Infra", 2 empresas, 2 títulos
    distintos (TechNova "Platform Engineer", FinTech Solutions "DevOps
    Engineer"): debería normalizarse a un único rol con `cantidad_puestos = 2`.

    Caso negativo -- "Product Manager" (Nimbus Retail) vs. "Product Marketing
    Manager" (BrightWave Media): títulos parecidos, roles distintos en el
    fondo. Deberían quedar como DOS roles separados. Ninguno de los perfiles
    sembrados matchea bien con estos dos -- están para probar clasificación,
    no matching.
    """
    return [
        (
            Empresa(
                nombre_empresa="TechNova",
                contexto="Scale-up B2B SaaS, cultura de ownership, deploy diario, buscamos ingenieros que piensen en producto.",
                email_registro="talento@technova.io",
            ),
            [
                Puesto(
                    empresa_id="",  # se rellena luego
                    titulo="Senior Backend Engineer (Python)",
                    descripcion=(
                        "Buscamos un backend engineer para diseñar y mantener APIs de alto rendimiento. "
                        "Stack: Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes. "
                        "Requisitos: 4+ años Python, diseño de APIs REST, testing automatizado, "
                        "conocimientos de mensajería (Kafka/RabbitMQ), observabilidad."
                    ),
                ),
                Puesto(
                    empresa_id="",
                    titulo="Platform Engineer",
                    descripcion=(
                        "Encargado de la plataforma interna: Kubernetes (GKE), Terraform, CI/CD, "
                        "observabilidad (Prometheus, Grafana, Loki). Go y Python. "
                        "Requisitos: experiencia en K8s, IaC, GitOps, cloud GCP/AWS."
                    ),
                ),
            ],
        ),
        (
            Empresa(
                nombre_empresa="DataMind",
                contexto="Consultoría de datos, proyectos variados, metodología ágil, foco en impacto de negocio.",
                email_registro="jobs@datamind.es",
            ),
            [
                Puesto(
                    empresa_id="",
                    titulo="Machine Learning Engineer",
                    descripcion=(
                        "Llevar modelos a producción: ML pipelines, feature stores, monitoring, A/B testing. "
                        "Stack: Python, scikit-learn, XGBoost, MLflow, Airflow, Kubernetes. "
                        "Requisitos: 3+ años ML en prod, MLOps, SQL avanzado, Docker."
                    ),
                ),
                Puesto(
                    empresa_id="",
                    titulo="Ingeniero/a de Backend Python",
                    descripcion=(
                        "Diseñar servicios de datos internos: APIs de acceso a datasets, pipelines de "
                        "ingesta, integración con el equipo de ML. Stack: Python, Django REST Framework, "
                        "PostgreSQL, Celery, Docker. Requisitos: 3+ años Python, diseño de APIs REST, "
                        "testing automatizado, colas de trabajo asincrónicas (Celery/RQ), Docker."
                    ),
                ),
            ],
        ),
        (
            Empresa(
                nombre_empresa="FinTech Solutions",
                contexto="Fintech regulada, compliance estricto, arquitectura hexagonal, testing exhaustivo.",
                email_registro="rrhh@fintechsolutions.com",
            ),
            [
                Puesto(
                    empresa_id="",
                    titulo="Backend Developer (Java/Kotlin)",
                    descripcion=(
                        "Desarrollo de servicios core: cuentas, pagos, tarjetas. "
                        "Java 21, Spring Boot 3, Kafka, PostgreSQL, JUnit, Testcontainers. "
                        "Requisitos: Spring Boot, arquitectura hexagonal, DDD, Kafka, testing."
                    ),
                ),
                Puesto(
                    empresa_id="",
                    titulo="DevOps Engineer",
                    descripcion=(
                        "Automatización de despliegues en OpenShift, GitOps con ArgoCD, "
                        "políticas de seguridad, compliance. Terraform, Helm, Prometheus."
                    ),
                ),
                Puesto(
                    empresa_id="",
                    titulo="Python Developer — Core Services",
                    descripcion=(
                        "Servicios core del banco digital: cuentas, pagos, conciliación. "
                        "Python, FastAPI, PostgreSQL, Docker. Ambiente regulado: testing exhaustivo "
                        "(unit + contract testing), trazabilidad de cambios, cumplimiento PCI-DSS. "
                        "Requisitos: 3+ años Python, FastAPI o equivalente, testing automatizado, "
                        "experiencia con entornos regulados/compliance."
                    ),
                ),
            ],
        ),
        (
            Empresa(
                nombre_empresa="CreativeLab",
                contexto="Agencia digital, proyectos variados, diseño y código juntos, cultura de craft.",
                email_registro="hola@creativelab.studio",
            ),
            [
                Puesto(
                    empresa_id="",
                    titulo="Frontend Developer (React/Next.js)",
                    descripcion=(
                        "Implementación pixel-perfect de diseños Figma en Next.js + Tailwind. "
                        "Accesibilidad WCAG 2.1, testing visual, Storybook. "
                        "Requisitos: React, Next.js, TypeScript, Tailwind, Playwright, diseño responsivo."
                    ),
                ),
            ],
        ),
        (
            Empresa(
                nombre_empresa="Nimbus Retail",
                contexto="E-commerce B2C, equipos chicos multidisciplinarios, foco en experimentación rápida.",
                email_registro="talento@nimbusretail.com",
            ),
            [
                Puesto(
                    empresa_id="",
                    titulo="Product Manager",
                    descripcion=(
                        "Liderar el roadmap de nuestra app de e-commerce B2C. Research de usuarios, "
                        "priorización de backlog, coordinación con diseño e ingeniería, métricas de "
                        "producto (activation, retention). Requisitos: 3+ años como PM, escritura de "
                        "specs/PRDs, priorización basada en datos, Jira/Linear."
                    ),
                ),
            ],
        ),
        (
            Empresa(
                nombre_empresa="BrightWave Media",
                contexto="Suite de productos B2B, equipo de marketing y ventas integrado, ciclos de GTM cortos.",
                email_registro="jobs@brightwavemedia.com",
            ),
            [
                Puesto(
                    empresa_id="",
                    titulo="Product Marketing Manager",
                    descripcion=(
                        "Liderar el posicionamiento y go-to-market de nuestra suite de productos B2B. "
                        "Mensajería de marca, campañas de lanzamiento, research competitivo, "
                        "habilitación al equipo de ventas. Requisitos: 3+ años en product marketing, "
                        "copywriting, campañas B2B, coordinación con ventas y contenido."
                    ),
                ),
            ],
        ),
    ]


def main():
    print("=== Rumbo Seed Data ===")

    # 1) Crear perfiles
    perfiles = [
        _perfil_ana(), _perfil_carlos(), _perfil_laura(),
        _perfil_miguel(), _perfil_sofia(), _perfil_jorge(),
    ]
    perfil_ids = []
    for p in perfiles:
        p.password_hash = hashear_password(PASSWORD_DEMO)
        try:
            pid = crear("perfiles", p.model_dump(mode="python", exclude_none=True))
            perfil_ids.append(pid)
            print(f"✓ Perfil creado: {p.nombre} {p.apellido} (id={pid})")
        except FirestoreError as e:
            print(f"✗ Error creando perfil {p.nombre}: {e}", file=sys.stderr)
            return 1

    # 2) Crear empresas y puestos
    for emp, puestos in _empresas_y_puestos():
        emp.password_hash = hashear_password(PASSWORD_DEMO)
        try:
            emp_id = crear("empresas", emp.model_dump(mode="python", exclude_none=True))
            print(f"✓ Empresa creada: {emp.nombre_empresa} (id={emp_id})")
        except FirestoreError as e:
            print(f"✗ Error creando empresa {emp.nombre_empresa}: {e}", file=sys.stderr)
            return 1

        for puesto in puestos:
            puesto.empresa_id = emp_id
            try:
                pid = crear("puestos", puesto.model_dump(mode="python", exclude_none=True))
                print(f"  ✓ Puesto: {puesto.titulo} (id={pid})")
                # Indexar (clasificar + extraer requisitos)
                from pipeline.matching_pipeline import ejecutar_pipeline_indexado
                ejecutar_pipeline_indexado(pid)
                print(f"    → Indexado completado")
            except FirestoreError as e:
                print(f"  ✗ Error creando puesto {puesto.titulo}: {e}", file=sys.stderr)
                return 1

    # 3) Disparar matching para cada perfil
    print("\n--- Ejecutando matching para perfiles ---")
    from pipeline.matching_pipeline import ejecutar_pipeline_matching
    for pid in perfil_ids:
        try:
            match_ids = ejecutar_pipeline_matching(pid)
            print(f"✓ Perfil {pid}: {len(match_ids)} matches creados")
        except Exception as e:
            print(f"✗ Error en matching perfil {pid}: {e}", file=sys.stderr)

    # 4) Verificación visual: cómo quedaron los roles normalizados
    print("\n--- Roles normalizados resultantes ---")
    from services.firestore_client import listar
    for rol in listar("roles_normalizados"):
        print(f"  · {rol.get('nombre_normalizado')} — cantidad_puestos={rol.get('cantidad_puestos')} (id={rol['_document_id']})")
    print(
        "\nEsperado: 'Backend Python' (o similar) con cantidad_puestos=3, "
        "'Platform/Infra' (o similar) con cantidad_puestos=2, y 'Product Manager' / "
        "'Product Marketing Manager' como DOS roles separados con cantidad_puestos=1 cada uno."
    )

    print(f"\n=== Seed completado — contraseña de todas las cuentas de prueba: {PASSWORD_DEMO} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())