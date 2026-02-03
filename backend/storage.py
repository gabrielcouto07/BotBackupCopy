# storage.py

import os


STATE_FILE = "state_last_seen.txt"


def get_last_seen(group_name: str) -> str:
    """
    Carrega o último ID de mensagem visto de um grupo específico.
    Retorna: ID da última mensagem ou string vazia se não existir.
    """
    if not os.path.exists(STATE_FILE):
        return ""

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            if "|" in line:
                parts = line.strip().split("|")
                if len(parts) >= 2:
                    saved_group = parts[0]
                    msg_id = parts[1]
                    if saved_group == group_name:
                        return msg_id
        return ""
    except Exception as e:
        print(f"⚠️ Erro ao carregar última mensagem de {group_name}: {e}")
        return ""


def save_last_seen(msg_id: str, group_name: str, message_preview: str = ""):
    """
    Salva o ID da última mensagem processada de um grupo.

    Args:
        msg_id: Hash SHA256 da mensagem (texto + URLs)
        group_name: Nome do grupo source
        message_preview: Primeiros 50 chars da mensagem (opcional)
    """
    existing_data = {}

    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                if "|" in line:
                    parts = line.strip().split("|", 2)
                    if len(parts) >= 2:
                        saved_group = parts[0]
                        saved_id = parts[1]
                        existing_data[saved_group] = saved_id
        except Exception as e:
            print(f"⚠️ Erro ao ler estado anterior: {e}")

    existing_data[group_name] = msg_id

    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            for grp, mid in existing_data.items():
                f.write(f"{grp}|{mid}\n")

        if message_preview:
            preview = message_preview[:50].replace("\n", " ")
            print(f" 💾 Salvou ID: {msg_id[:16]}... ('{preview}...')")
        else:
            print(f" 💾 Salvou ID: {msg_id[:16]}...")
    except Exception as e:
        print(f"⚠️ Erro ao salvar estado: {e}")