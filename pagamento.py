import os
import uuid
import logging
import requests
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

MP_ACCESS_TOKEN = os.getenv(
    "MP_ACCESS_TOKEN",
    "TEST-5008369931656244-051318-c946150c8e44a1551c000b261ac10fa2-824224954"
)


def criar_pix(valor: float, descricao: str, drama_id: str, user_id: int) -> dict | None:
    """
    Cria uma cobrança Pix no Mercado Pago via requests direto na API.
    """
    idempotency_key = str(uuid.uuid4())
    expira = (datetime.now(timezone.utc) + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000-03:00")

    payload = {
        "transaction_amount": round(valor, 2),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": f"cliente_{user_id}@dramacerto.com",
        },
        "external_reference": f"{drama_id}|{user_id}",
        "date_of_expiration": expira,
    }

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": idempotency_key,
    }

    try:
        response = requests.post(
            "https://api.mercadopago.com/v1/payments",
            json=payload,
            headers=headers,
            timeout=15
        )
        data = response.json()

        if response.status_code in (200, 201):
            pix_info = data.get("point_of_interaction", {}).get("transaction_data", {})
            return {
                "id": data["id"],
                "pix_copia_cola": pix_info.get("qr_code", "Erro ao gerar código Pix"),
                "status": data["status"],
            }
        else:
            logger.error(f"Erro Mercado Pago {response.status_code}: {data}")
            return None

    except Exception as e:
        logger.error(f"Exceção ao criar Pix: {e}")
        return None


def verificar_pagamento(payment_id: int) -> str:
    """Verifica o status de um pagamento."""
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    try:
        response = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers=headers,
            timeout=15
        )
        if response.status_code == 200:
            return response.json().get("status", "error")
        return "error"
    except Exception as e:
        logger.error(f"Erro ao verificar pagamento {payment_id}: {e}")
        return "error"
