"""
Agente 3 — Auditor de fit.

Compara el `cv_data` de un perfil contra la descripción de un puesto y contra
`requisitos_frecuencia` del rol, y devuelve el score más el roadmap cuantitativo.

Corre una vez por cada puesto candidato que devolvió el retrieval.

Backlog: tareas 2.9 y 2.6
"""


def calcular_score_y_roadmap(perfil_id: str, puesto_id: str) -> dict:
    """
    Audita el fit entre un perfil y un puesto.

    Returns:
        {
            "score": int,               # 0-100
            "justificacion": str,
            "roadmap": [                # ver esquema de BD para la subestructura
                {
                    "requisito_id": str,
                    "nombre": str,
                    "cumplido": bool,
                    "porcentaje_mercado": int,
                    "especifico_de_esta_empresa": bool,
                    "sugerencia": str | None,
                },
                ...
            ],
        }
    """
    raise NotImplementedError
