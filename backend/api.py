# api.py - API Flask para o painel de configuração

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import subprocess
import sys
import os
import signal
from pathlib import Path

app = Flask(__name__)
CORS(app)

SETTINGS_FILE = Path(__file__).parent / "settings.json"
BOT_PROCESS = None  # Guarda referência ao processo do bot


def load_settings() -> dict:
    """Carrega configurações do arquivo JSON"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar settings: {e}")
    return {}


def save_settings(settings: dict):
    """Salva configurações no arquivo JSON"""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Retorna todas as configurações"""
    settings = load_settings()
    return jsonify(settings)


@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Atualiza todas as configurações"""
    try:
        new_settings = request.json
        save_settings(new_settings)
        return jsonify({"success": True, "message": "Configurações salvas!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/settings/<section>", methods=["GET"])
def get_section(section: str):
    """Retorna uma seção específica das configurações"""
    settings = load_settings()
    if section in settings:
        return jsonify(settings[section])
    return jsonify({"error": "Seção não encontrada"}), 404


@app.route("/api/settings/<section>", methods=["PUT"])
def update_section(section: str):
    """Atualiza uma seção específica das configurações"""
    try:
        settings = load_settings()
        settings[section] = request.json
        save_settings(settings)
        return jsonify({"success": True, "message": f"Seção '{section}' atualizada!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/channel-pairs", methods=["GET"])
def get_channel_pairs():
    """Retorna os pares de canais"""
    settings = load_settings()
    return jsonify(settings.get("channel_pairs", []))


@app.route("/api/channel-pairs", methods=["POST"])
def add_channel_pair():
    """Adiciona um novo par de canal"""
    try:
        settings = load_settings()
        new_pair = request.json
        if "channel_pairs" not in settings:
            settings["channel_pairs"] = []
        settings["channel_pairs"].append(new_pair)
        save_settings(settings)
        return jsonify({"success": True, "message": "Canal adicionado!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/channel-pairs/<int:index>", methods=["PUT"])
def update_channel_pair(index: int):
    """Atualiza um par de canal específico"""
    try:
        settings = load_settings()
        if 0 <= index < len(settings.get("channel_pairs", [])):
            settings["channel_pairs"][index] = request.json
            save_settings(settings)
            return jsonify({"success": True, "message": "Canal atualizado!"})
        return jsonify({"success": False, "message": "Índice inválido"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/channel-pairs/<int:index>", methods=["DELETE"])
def delete_channel_pair(index: int):
    """Remove um par de canal"""
    try:
        settings = load_settings()
        if 0 <= index < len(settings.get("channel_pairs", [])):
            settings["channel_pairs"].pop(index)
            save_settings(settings)
            return jsonify({"success": True, "message": "Canal removido!"})
        return jsonify({"success": False, "message": "Índice inválido"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Verifica se a API está funcionando"""
    return jsonify({"status": "ok", "message": "API funcionando!"})


# ============================================================
# Controle do Bot
# ============================================================

@app.route("/api/bot/status", methods=["GET"])
def bot_status():
    """Retorna o status do bot"""
    global BOT_PROCESS
    running = BOT_PROCESS is not None and BOT_PROCESS.poll() is None
    pid = BOT_PROCESS.pid if BOT_PROCESS is not None and running else None
    return jsonify({
        "running": running,
        "pid": pid
    })


@app.route("/api/bot/start", methods=["POST"])
def start_bot():
    """Inicia o bot"""
    global BOT_PROCESS
    
    # Verifica se já está rodando
    if BOT_PROCESS is not None and BOT_PROCESS.poll() is None:
        return jsonify({"success": False, "message": "Bot já está rodando!"}), 400
    
    try:
        # Caminho do main.py
        bot_script = Path(__file__).parent / "main.py"
        
        if not bot_script.exists():
            return jsonify({"success": False, "message": "main.py não encontrado!"}), 404
        
        # Inicia o bot em um processo separado
        BOT_PROCESS = subprocess.Popen(
            [sys.executable, str(bot_script)],
            cwd=str(Path(__file__).parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        return jsonify({
            "success": True, 
            "message": "Bot iniciado!",
            "pid": BOT_PROCESS.pid
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/bot/stop", methods=["POST"])
def stop_bot():
    """Para o bot"""
    global BOT_PROCESS
    
    if BOT_PROCESS is None or BOT_PROCESS.poll() is not None:
        BOT_PROCESS = None
        return jsonify({"success": False, "message": "Bot não está rodando!"}), 400
    
    try:
        if os.name == 'nt':
            # Windows: envia CTRL+BREAK
            BOT_PROCESS.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            # Unix: envia SIGTERM
            BOT_PROCESS.terminate()
        
        # Aguarda até 5 segundos
        try:
            BOT_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            BOT_PROCESS.kill()
        
        BOT_PROCESS = None
        return jsonify({"success": True, "message": "Bot parado!"})
    except Exception as e:
        BOT_PROCESS = None
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/bot/restart", methods=["POST"])
def restart_bot():
    """Reinicia o bot"""
    global BOT_PROCESS
    
    # Para se estiver rodando
    if BOT_PROCESS is not None and BOT_PROCESS.poll() is None:
        try:
            if os.name == 'nt':
                BOT_PROCESS.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                BOT_PROCESS.terminate()
            BOT_PROCESS.wait(timeout=5)
        except:
            BOT_PROCESS.kill()
        BOT_PROCESS = None
    
    # Inicia novamente
    try:
        bot_script = Path(__file__).parent / "main.py"
        BOT_PROCESS = subprocess.Popen(
            [sys.executable, str(bot_script)],
            cwd=str(Path(__file__).parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        return jsonify({
            "success": True, 
            "message": "Bot reiniciado!",
            "pid": BOT_PROCESS.pid
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    print("🚀 API de configurações iniciada em http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
