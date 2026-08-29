"""
Tests de servicios: invitaciones (visibilidad + estados) y auditor_fit.
"""

import pytest

from services.invitaciones import (
    TransicionInvalidaError,
    enviar_invitacion,
    es_empresa_visible,
    filtrar_campos_visibles,
    procesar_respuesta,
)
from agents.auditor_fit import calcular_score_y_roadmap
from models.match import EstadoMatch
from models.perfil import Perfil
from services.firestore_client import crear, obtener


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
    from models.puesto import Puesto
    p = Puesto(empresa_id=empresa_id, titulo=titulo, descripcion=desc)
    pid = crear("puestos", p.model_dump(mode="python", exclude_none=True))
    # Indexar
    from pipeline.matching_pipeline import ejecutar_pipeline_indexado
    ejecutar_pipeline_indexado(pid)
    return pid


def _crear_empresa_test():
    from models.empresa import Empresa
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
        from pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        assert matches
        mid = matches[0]

        match = enviar_invitacion(mid)
        assert match["estado"] == EstadoMatch.NOTIFICADO.value

    def test_enviar_invitacion_no_pendiente_falla(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend", "Python")
        from pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]

        enviar_invitacion(mid)  # primera vez ok
        with pytest.raises(TransicionInvalidaError):
            enviar_invitacion(mid)  # segunda vez falla

    def test_procesar_respuesta_aceptar(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend", "Python")
        from pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]

        enviar_invitacion(mid)
        match = procesar_respuesta(mid, aceptar=True)
        assert match["estado"] == EstadoMatch.CONFIRMADO.value

    def test_procesar_respuesta_rechazar(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend", "Python")
        from pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]

        enviar_invitacion(mid)
        match = procesar_respuesta(mid, aceptar=False)
        assert match["estado"] == EstadoMatch.RECHAZADO.value

    def test_procesar_respuesta_sin_invitar_falla(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        pid_puesto = _crear_puesto_test(eid, "Backend", "Python")
        from pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]

        with pytest.raises(TransicionInvalidaError):
            procesar_respuesta(mid, aceptar=True)


class TestAuditorFit:
    def test_score_alto_cumple_requisitos(self):
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        # Perfil con Python y FastAPI
        # Puesto con requisitos claros que coincidan con el perfil
        pid_puesto = _crear_puesto_test(eid, "Backend Python", "Python FastAPI APIs REST Docker")
        from pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        assert matches
        mid = matches[0]
        match = obtener("matches", mid)
        assert match["score"] >= 75

    def test_score_bajo_no_cumple(self):
        eid = _crear_empresa_test()
        # Perfil con algunas habilidades que solapen parcialmente
        from models.perfil import Perfil
        p = Perfil(
            nombre="Juan",
            apellido="Perez",
            email="juan@test.com",
            cv_data={"experiencia": [], "formacion": [], "habilidades": ["Python", "C++"], "proyectos": []},
        )
        pid = crear("perfiles", p.model_dump(mode="python", exclude_none=True))

        # Puesto con Python (match) y Django (no match)
        pid_puesto = _crear_puesto_test(eid, "Backend Python", "Python Django APIs")
        from pipeline.matching_pipeline import ejecutar_pipeline_matching
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
        from pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        mid = matches[0]
        match = obtener("matches", mid)
        roadmap = match["roadmap"]
        # Terraform no está en perfil -> sugerencia
        tf_items = [r for r in roadmap if "terraform" in r["nombre"].lower()]
        assert tf_items
        assert tf_items[0]["cumplido"] is False
        assert tf_items[0]["sugerencia"] is not None

    def test_roadmap_especifico_empresa_true_si_no_en_frecuencias(self):
        # El extractor crea requisitos nuevos si no están en catálogo
        # Esos requisitos no tendrán frecuencia en el rol -> especifico=True
        eid = _crear_empresa_test()
        pid = _crear_perfil_test()
        # Puesto con términos poco comunes -> requisitos nuevos
        pid_puesto = _crear_puesto_test(eid, "Backend Python", "Python QuasarFramework VitePress")
        from pipeline.matching_pipeline import ejecutar_pipeline_matching
        matches = ejecutar_pipeline_matching(pid)
        assert matches
        mid = matches[0]
        match = obtener("matches", mid)
        roadmap = match["roadmap"]
        # Los requisitos de QuasarFramework/VitePress son nuevos -> especifico=True
        assert any(r["especifico_de_esta_empresa"] for r in roadmap)