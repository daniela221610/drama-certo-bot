import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
DB_PATH = "pedidos.db"


def inicializar_banco():
    """Cria a tabela de pedidos se não existir."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            drama_id TEXT NOT NULL,
            drama_nome TEXT NOT NULL,
            payment_id TEXT,
            valor REAL NOT NULL,
            status TEXT DEFAULT 'pendente',
            criado_em TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Banco de dados inicializado.")


def salvar_pedido(user_id: int, user_name: str, drama_id: str, drama_nome: str, payment_id: str, valor: float):
    """Salva um novo pedido pendente."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Remove pedidos pendentes antigos do mesmo usuário
    cursor.execute(
        "DELETE FROM pedidos WHERE user_id = ? AND status = 'pendente'",
        (user_id,)
    )

    cursor.execute("""
        INSERT INTO pedidos (user_id, user_name, drama_id, drama_nome, payment_id, valor, status, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, 'pendente', ?)
    """, (user_id, user_name, drama_id, drama_nome, payment_id, valor, datetime.now().strftime("%d/%m/%Y %H:%M")))

    conn.commit()
    conn.close()


def buscar_pedido_por_usuario(user_id: int) -> dict | None:
    """Busca o pedido pendente mais recente de um usuário."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM pedidos
        WHERE user_id = ? AND status = 'pendente'
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def marcar_entregue(user_id: int):
    """Marca o pedido como entregue."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE pedidos SET status = 'entregue'
        WHERE user_id = ? AND status = 'pendente'
    """, (user_id,))
    conn.commit()
    conn.close()


def listar_pedidos_pendentes() -> list:
    """Retorna todos os pedidos pendentes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE status = 'pendente' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Inicializa o banco ao importar
inicializar_banco()
