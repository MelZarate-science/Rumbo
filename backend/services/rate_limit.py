"""
Rate limiting en memoria para endpoints sensibles del MVP.

Alcanza para frenar abuso básico en una sola instancia. En producción real,
Cloud Run necesitaría complementar esto con controles en edge o un store
compartido para múltiples réplicas.
"""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_LOCK = Lock()


def _key(scope: str, request: Request, *, actor: str | None = None) -> str:
    client_host = request.client.host if request.client else "unknown"
    if actor:
        return f"{scope}:{client_host}:{actor}"
    return f"{scope}:{client_host}"


def _consume(
    bucket_key: str,
    *,
    now: float,
    max_requests: int,
    window_seconds: int,
) -> None:
    bucket = _BUCKETS[bucket_key]
    while bucket and now - bucket[0] >= window_seconds:
        bucket.popleft()

    if len(bucket) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": True,
                "mensaje": "Demasiadas solicitudes. Probá de nuevo en unos minutos.",
                "codigo": "RATE_LIMIT_EXCEDIDO",
            },
        )

    bucket.append(now)


def enforce_rate_limit(
    request: Request,
    *,
    scope: str,
    max_requests: int,
    window_seconds: int,
    actor: str | None = None,
) -> None:
    now = monotonic()
    client_key = _key(scope, request)
    actor_key = _key(scope, request, actor=actor) if actor else None

    with _LOCK:
        _consume(
            client_key,
            now=now,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )
        if actor_key is not None:
            _consume(
                actor_key,
                now=now,
                max_requests=max_requests,
                window_seconds=window_seconds,
            )


def reset_rate_limits() -> None:
    with _LOCK:
        _BUCKETS.clear()
