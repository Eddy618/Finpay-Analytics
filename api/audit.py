import json
from typing import Any

from sqlalchemy import text

from api.database import engine


def write_audit_log(
    *,
    action: str,
    actor_id: str = "anonymous",
    actor_type: str = "anonymous",
    resource_type: str | None = None,
    resource_id: str | None = None,
    http_method: str | None = None,
    endpoint: str | None = None,
    ip_address: str | None = None,
    status_code: int | None = None,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Write an auditable application event.

    Audit failures must not break the main application flow.
    """

    query = text("""
        INSERT INTO public.audit_logs (
            actor_id,
            actor_type,
            action,
            resource_type,
            resource_id,
            http_method,
            endpoint,
            ip_address,
            status_code,
            old_value,
            new_value,
            details
        )
        VALUES (
            :actor_id,
            :actor_type,
            :action,
            :resource_type,
            :resource_id,
            :http_method,
            :endpoint,
            :ip_address,
            :status_code,
            CAST(:old_value AS JSONB),
            CAST(:new_value AS JSONB),
            CAST(:details AS JSONB)
        );
    """)

    try:
        with engine.begin() as connection:
            connection.execute(
                query,
                {
                    "actor_id": actor_id,
                    "actor_type": actor_type,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "http_method": http_method,
                    "endpoint": endpoint,
                    "ip_address": ip_address,
                    "status_code": status_code,
                    "old_value": json.dumps(
                        old_value
                    ) if old_value is not None else None,
                    "new_value": json.dumps(
                        new_value
                    ) if new_value is not None else None,
                    "details": json.dumps(
                        details
                    ) if details is not None else None,
                },
            )

    except Exception as error:
        # Do not let audit logging take down the application.
        print(
            f"WARNING: Audit logging failed: {error}"
        )