"""
Tests de servicios: invitaciones (visibilidad + estados) y auditor_fit.
"""

import pytest

from backend.services.invitaciones import (
    TransicionInvalidaError,
    enviar_invitacion,
    es_empresa_visible,
    filtrar_campos_visibles,
    procesar_respuesta,
)
from agents.auditor_fit import calcular_score_y_roadmap
from backend.models.match import EstadoMatch
from backend.models.perfil import Perfil
from backend.services.firestore_client import crear, obtener


def _crear_perfil_test():
    p = Perfil(
        nombre="Ana",
        apellido="García",
        email="ana@test.com",
        telefono="+34 600 111 222",
        cv_data={"experiencia": [], "formacion": [], "habilidades": ["Python", "FastAPI"], "proyectos": []},
    )
    pid = crear("perfiles", p.model_dump(mode="python", exclude_none=True))
    return pid


def _crear_puesto_test(empresa_id: str, titulo: str, desc: str):
    from backend.models.puesto import Puesto
    p = Puesto(empresa_id=empresa_id, titulo=titulo, descripcion=desc)
    pid = crear("puestos", p.model_dump(mode="python", exclude_none=True))
    # Indexar
    from backend.pipeline.matching_pipeline import ejecutar_pipeline_indexado
    ejecutar_pipeline_indexado(pid)
    return pid


def _crear_empresa_test():
    from backend.models.empresa import Empresa
    e = Empresa(nombre_empresa="TestCo", contexto="Test", email_registro="hr@test.com")
    return crear("empresas", e.model_dump(mode="python", exclude_none=True))


class TestInvitaciones:
    def test_filtrar_campos_visibles_pendiente_oculta_privados(self):
        perfil = {
            "nombre": "Ana",
            "apellido": "García",
            "email": "ana@test.com",
            "telefono": "+34 600 111 222",
            "cv_data": {"habilidades": ["Python"]},
        }
        filtrado = filtrar_campos_visibles(perfil, EstadoMatch.PENDIENTE.value)
        assert "apellido" not in filtrado
        assert "email" not in filtrado
        assert "telefono" not in filtrado
        assert filtrado["nombre"] == "Ana"
        assert "cv_data" in filtrado

    def test_filtrar_campos_visibles_confirmado_muestra_todo(self):
        perfil = {
            "nombre": "Ana",
            "apellido": "García",
            "email": "ana@test.com",
            "telefono": "+34 600 111 222",
        }
        filtrado = filtrar_campos_visibles(perfil, EstadoMatch.CONFIRMADO.value)
        assert filtrado["apellido"] == "García"
        assert filtrado["email"] == "ana@test.com"
        assert filtrado["telefono"] == "+34 600 111 222"

    def test_es_empresa_visible(self):
        assert es_empresa_visible("pendiente") is False
        assert es_empresa_visible("notificado") is True
        assert es_empresa_visible("confirmado") is True
        assert es_empresa_visible("rechazado") is True

    def test_enviar_invitacion_ok(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend", "Python, FastAPI")
        from backend.pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        assert matches
        mid = matches[0]

        match = enviar_invitacion(mid)
        assert match["estado"] == EstadoMatch.NOTIFICADO.value

    def test_enviar_invitacion_no_pendiente_falla(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend", "Python")
        from backend.pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]

        enviar_invitacion(mid)  # primera vez ok
        with pytest.raises(TransicionInvalidaError):
            enviar_invitacion(mid)  # segunda vez falla

    def test_procesar_respuesta_aceptar(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend", "Python")
        from backend.pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]

        enviar_invitacion(mid)
        match = procesar_respuesta(mid, aceptar=True)
        assert match["estado"] == EstadoMatch.CONFIRMADO.value

    def test_procesar_respuesta_rechazar(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend", "Python")
        from backend.pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]

        enviar_invitacion(mid)
        match = procesar_respuesta(mid, aceptar=False)
        assert match["estado"] == EstadoMatch.RECHAZADO.value

    def test_procesar_respuesta_sin_invitar_falla(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend", "Python")
        from backend.pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]

        with pytest.raises(TransicionInvalidaError):
            procesar_respuesta(mid, aceptar=True)


class TestAuditorFit:
    """
    Usa el doble de Gemini de `tests/fakes_gemini.py` (ver `tests/conftest.py`):
    reconoce un requisito como cumplido si sus tokens están en el texto del CV.
    Los datos de estos tests están armados para que ese criterio dé un
    resultado inequívoco — no para imitar el juicio real del modelo.
    """

    def test_score_alto_cumple_requisitos(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        # Puesto que solo pide justo lo que el perfil ya tiene
        pid_puesto = _crear_puesto_test(eid, "Python", "Python y FastAPI")
        from backend.pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        assert matches
        mid = matches[0]
        match = obtener("matches", mid)
        assert match["score"] == 100

    def test_score_bajo_no_cumple(self):
        eid = _crear_empresa_test()
        # Perfil con algunas habilidades que solapen parcialmente
        from backend.models.perfil import Perfil
        p = Perfil(
            nombre="Juan",
            apellido="Perez",
            email="juan@test.com",
            cv_data={"experiencia": [], "formacion": [], "habilidades": ["Python", "C++"], "proyectos": []},
        )
        pid = crear("perfiles", p.model_dump(mode="python", exclude_none=True))

        # Puesto con Python (match) y Django (no match)
        pid_puesto = _crear_puesto_test(eid, "Backend Python", "Python Django APIs")
        from backend.pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        assert matches
        mid = matches[0]
        match = obtener("matches", mid)
        # Python match, Django no -> score medio-bajo
        assert match["score"] < 75

    def test_roadmap_contiene_sugerencias_no_cumplidos(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend Python", "Python FastAPI Terraform")
        from backend.pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]
        match = obtener("matches", mid)
        roadmap = match["roadmap"]
        # Terraform no está en perfil -> sugerencia
        tf_items = [r for r in roadmap if "terraform" in r["nombre"].lower()]
        assert tf_items
        assert tf_items[0]["cumplido"] is False
        assert tf_items[0]["sugerencia"] is not None

    def test_roadmap_especifico_empresa_bajo_frecuencia_de_mercado(self):
        """
        `especifico_de_esta_empresa` ya no es un flag que se congela al
        indexar (bug real: un requisito que empezaba como capricho de una
        empresa se quedaba marcado así para siempre, aunque después se
        volviera estándar del mercado) -- se deriva en vivo de
        `porcentaje_mercado`. Con 3 puestos del mismo rol, un requisito que
        piden los 3 (100%) es estándar; uno que pide solo 1 (33%) es
        particular de esa empresa.
        """
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()

        _crear_puesto_test(eid, "Backend Python", "Python")
        _crear_puesto_test(eid, "Backend Python", "Python")
        pid_puesto = _crear_puesto_test(eid, "Backend Python", "Python QuasarFramework")

        from backend.pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        assert matches
        match = next(m for m in (obtener("matches", mid) for mid in matches) if m["puesto_id"] == pid_puesto)
        roadmap = {r["nombre"]: r for r in match["roadmap"]}

        assert roadmap["Python"]["especifico_de_esta_empresa"] is False
        assert roadmap["Quasarframework"]["especifico_de_esta_empresa"] is True


class TestFrecuencias:
    """
    Backlog 2.6: 'los porcentajes de frecuencia se recalculan correctamente'.
    Cubre el bug real encontrado en sesión: `ejecutar_pipeline_indexado` leía
    `rol_normalizado_id` de una copia del puesto obtenida ANTES de clasificarlo,
    así que en la primera indexación de cualquier puesto nunca se llamaba a
    `actualizar_frecuencias` — todos los `porcentaje_mercado` quedaban en 0
    para siempre. Ningún test anterior lo detectaba porque ninguno afirmaba
    el valor numérico de `porcentaje_mercado`, solo su presencia estructural.
    """

    def test_primer_puesto_del_rol_queda_al_100_por_ciento(self):
        eid = _crear_empresa_test()
        pid_puesto = _crear_puesto_test(eid, "Backend Python", "Python FastAPI")

        puesto = obtener("puestos", pid_puesto)
        rol = obtener("roles_normalizados", puesto["rol_normalizado_id"])
        frecuencias = {f["requisito_id"]: f for f in rol["requisitos_frecuencia"]}

        assert rol["cantidad_puestos"] == 1
        assert len(frecuencias) == 3  # Backend, Python, Fastapi
        for entrada in frecuencias.values():
            assert entrada["cantidad"] == 1
            assert entrada["porcentaje"] == 100

    def test_segundo_puesto_del_mismo_rol_recalcula_porcentajes(self):
        eid = _crear_empresa_test()
        pid_puesto1 = _crear_puesto_test(eid, "Backend Python", "Python FastAPI")
        pid_puesto2 = _crear_puesto_test(eid, "Backend Python", "Python Django")

        rol_id = obtener("puestos", pid_puesto1)["rol_normalizado_id"]
        # Ambos puestos deben haber quedado clasificados en el mismo rol
        assert obtener("puestos", pid_puesto2)["rol_normalizado_id"] == rol_id

        rol = obtener("roles_normalizados", rol_id)
        frecuencias = {f["requisito_id"]: f for f in rol["requisitos_frecuencia"]}
        por_nombre = {}
        for req_id, entrada in frecuencias.items():
            req = obtener("requisitos_normalizados", req_id)
            por_nombre[req["nombre"]] = entrada

        assert rol["cantidad_puestos"] == 2
        # "Python" y "Backend" aparecen en los dos puestos -> 100%
        assert por_nombre["Python"]["cantidad"] == 2
        assert por_nombre["Python"]["porcentaje"] == 100
        assert por_nombre["Backend"]["porcentaje"] == 100
        # "Fastapi" solo en el primer puesto, "Django" solo en el segundo -> 50%
        assert por_nombre["Fastapi"]["cantidad"] == 1
        assert por_nombre["Fastapi"]["porcentaje"] == 50
        assert por_nombre["Django"]["cantidad"] == 1
        assert por_nombre["Django"]["porcentaje"] == 50

    def test_reindexar_mismo_puesto_no_cambia_cantidad_puestos(self):
        """
        Bug real: `cantidad_puestos` se inferia de si la cantidad de
        requisitos subió o bajó al reindexar, no de cuántos puestos
        distintos aportaron al rol -- reindexar el MISMO puesto pidiendo
        MENOS requisitos que antes restaba 1, como si un puesto se hubiera
        ido del rol. Ahora se cuenta por `puesto_id` real (`puestos_ids` del
        rol), así que reindexar el mismo puesto no debe mover el contador,
        sin importar si esta vez pide más o menos requisitos.
        """
        eid = _crear_empresa_test()
        pid_puesto = _crear_puesto_test(eid, "Backend Python", "Python FastAPI Docker")

        rol_id = obtener("puestos", pid_puesto)["rol_normalizado_id"]
        assert obtener("roles_normalizados", rol_id)["cantidad_puestos"] == 1

        # Reindexar el mismo puesto pidiendo MENOS requisitos que antes.
        from backend.services.firestore_client import actualizar as _actualizar
        _actualizar("puestos", pid_puesto, {"titulo": "Backend Python", "descripcion": "Python"})
        from backend.pipeline.matching_pipeline import ejecutar_pipeline_indexado
        ejecutar_pipeline_indexado(pid_puesto)

        rol = obtener("roles_normalizados", rol_id)
        assert obtener("puestos", pid_puesto)["rol_normalizado_id"] == rol_id
        assert rol["cantidad_puestos"] == 1
