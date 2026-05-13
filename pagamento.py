import os
import uuid
import logging
import mercadopago

logger = logging.getLogger(__name__)

MP_ACCESS_TOKEN = os.getenv(
    "MP_ACCESS_TOKEN",
    "TEST-5008369931656244-051318-c946150c8e44a1551c000b261ac10fa2-824224954"
)

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)


def criar_pix(valor: float, descricao: str, drama_id: str, user_id: int) -> dict | None:
    """
    Cria uma cobrança Pix no Mercado Pago.
    Retorna dicionário com 'id' e 'pix_copia_cola', ou None em caso de erro.
    """
    idempotency_key = str(uuid.uuid4())

    payment_data = {
        "transaction_amount": round(valor, 2),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": f"cliente_{user_id}@dramacerto.com",
        },
        "external_reference": f"{drama_id}|{user_id}",
        "date_of_expiration": _expiracao_30min(),
    }

    try:
        result = sdk.payment().create(payment_data, {"X-Idempotency-Key": idempotency_key})
        response = result["response"]

        if result["status"] in (200, 201):
            pix_info = response.get("point_of_interaction", {}).get("transaction_data", {})
            return {
                "id": response["id"],
                "pix_copia_cola": pix_info.get("qr_code", "Erro ao gerar código Pix"),
                "status": response["status"],
            }
        else:
            logger.error(f"Erro Mercado Pago: {response}")
            return None

    except Exception as e:
        logger.error(f"Exceção ao criar Pix: {e}")
        return None


def verificar_pagamento(payment_id: int) -> str:
    """
    Verifica o status de um pagamento.
    Retorna: 'approved', 'pending', 'rejected' ou 'error'
    """
    try:
        result = sdk.payment().get(payment_id)
        if result["status"] == 200:
            return result["response"].get("status", "error")
        return "error"
    except Exception as e:
        logger.error(f"Erro ao verificar pagamento {payment_id}: {e}")
        return "error"


def _expiracao_30min() -> str:
    """Retorna timestamp de expiração com 30 minutos a partir de agora."""
    from datetime import datetime, timedelta, timezone
    expira = datetime.now(timezone.utc) + timedelta(minutes=30)
    return expira.strftime("%Y-%m-%dT%H:%M:%S.000-03:00")
