# api_config.py - API Flask para gerenciar configurações

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import re
import subprocess
import sys
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Permite requisições do React

CONFIG_FILE = Path(__file__).parent / "config.py"
bot_process = None  # Rastreia o processo do bot


def parse_config_file():
    """Lê o arquivo config.py e extrai as configurações"""
    if not CONFIG_FILE.exists():
        return {}
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    config = {}
    
    # Extrai valores simples
    patterns = {
        'CHROME_USER_DATA_DIR': r'CHROME_USER_DATA_DIR\s*=\s*["\'](.+?)["\']',
        'CHROME_PROFILE_DIR_NAME': r'CHROME_PROFILE_DIR_NAME\s*=\s*["\'](.+?)["\']',
        'HEADLESS': r'HEADLESS\s*=\s*(True|False)',
        'DOWNLOAD_DIR': r'DOWNLOAD_DIR\s*=\s*["\'](.+?)["\']',
        'MELI_AFFILIATE_TAG': r'MELI_AFFILIATE_TAG\s*=\s*["\'](.+?)["\']',
        'SUPERHERO_EMOJI': r'SUPERHERO_EMOJI\s*=\s*["\'](.+?)["\']',
        'GATILHO_CHANCE': r'GATILHO_CHANCE\s*=\s*([\d.]+)',
        'BUBBLE_REFRESH_DELAY': r'BUBBLE_REFRESH_DELAY\s*=\s*(\d+)',
        'POLL_SECONDS': r'POLL_SECONDS\s*=\s*(\d+)',
        'RESTART_EVERY_CYCLES': r'RESTART_EVERY_CYCLES\s*=\s*(\d+)',
        'CYCLE_TIMEOUT_SECONDS': r'CYCLE_TIMEOUT_SECONDS\s*=\s*(\d+)',
        'SLEEP_GRANULARITY_SECONDS': r'SLEEP_GRANULARITY_SECONDS\s*=\s*(\d+)',
        'NIGHT_MODE_ENABLED': r'NIGHT_MODE_ENABLED\s*=\s*(True|False)',
        'NIGHT_START_HOUR': r'NIGHT_START_HOUR\s*=\s*(\d+)',
        'NIGHT_END_HOUR': r'NIGHT_END_HOUR\s*=\s*(\d+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            value = match.group(1)
            # Converte tipos
            if value in ('True', 'False'):
                config[key] = value == 'True'
            elif key in ('GATILHO_CHANCE',):
                config[key] = float(value)
            elif key in ('BUBBLE_REFRESH_DELAY', 'POLL_SECONDS', 'RESTART_EVERY_CYCLES', 
                        'CYCLE_TIMEOUT_SECONDS', 'SLEEP_GRANULARITY_SECONDS', 
                        'NIGHT_START_HOUR', 'NIGHT_END_HOUR'):
                config[key] = int(value)
            else:
                config[key] = value
    
    # Extrai GATILHOS (lista)
    gatilhos_match = re.search(r'GATILHOS\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if gatilhos_match:
        gatilhos_str = gatilhos_match.group(1)
        gatilhos = re.findall(r'["\'](.+?)["\']', gatilhos_str)
        config['GATILHOS'] = gatilhos
    
    # Extrai CHANNEL_PAIRS - suporta strings vazias e caracteres especiais
    channel_pairs_match = re.search(r'CHANNEL_PAIRS\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if channel_pairs_match:
        pairs_str = channel_pairs_match.group(1)
        # Regex melhorada para capturar strings com emojis, espaços, colchetes, etc
        # Captura cada string entre aspas (simples ou duplas), incluindo strings vazias
        pairs = re.findall(r'\(\s*["\']([^"\']*?)["\'],\s*["\']([^"\']*?)["\'],\s*["\']([^"\']*?)["\']\s*\)', pairs_str)
        config['CHANNEL_PAIRS'] = [{'source': p[0], 'target': p[1], 'description': p[2]} for p in pairs]
        print(f"   DEBUG: Encontrados {len(pairs)} pares de canais")
    
    # Extrai GROUP_LINKS - melhorado para suportar caracteres especiais
    group_links_match = re.search(r'GROUP_LINKS\s*=\s*\{(.*?)\}', content, re.DOTALL)
    if group_links_match:
        links_str = group_links_match.group(1)
        # Captura strings com colchetes, hífens, emojis, etc
        links = re.findall(r'["\']([^"\']+?)["\']\s*:\s*["\']([^"\']+?)["\']', links_str)
        config['GROUP_LINKS'] = {k: v for k, v in links}
        print(f"   DEBUG: Encontrados {len(links)} links de grupos")
    
    return config


def write_config_file(config):
    """Escreve as configurações de volta no config.py"""
    lines = [
        "import os",
        "",
        f'CHROME_USER_DATA_DIR = "{config.get("CHROME_USER_DATA_DIR", "C:\\\\BotChromeProfile")}"',
        f'CHROME_PROFILE_DIR_NAME = "{config.get("CHROME_PROFILE_DIR_NAME", "Default")}"',
        f'HEADLESS = {config.get("HEADLESS", True)}',
        "",
        f'DOWNLOAD_DIR = "{config.get("DOWNLOAD_DIR", "./tmp")}"',
        "os.makedirs(DOWNLOAD_DIR, exist_ok=True)",
        "",
        f'MELI_AFFILIATE_TAG = "{config.get("MELI_AFFILIATE_TAG", "")}"',
        "",
        f'SUPERHERO_EMOJI = "{config.get("SUPERHERO_EMOJI", "🦸")}"',
        "",
        "GATILHOS = [",
    ]
    
    # Adiciona gatilhos
    for gatilho in config.get('GATILHOS', []):
        lines.append(f'    "{gatilho}",')
    
    lines.extend([
        "]",
        f'GATILHO_CHANCE = {config.get("GATILHO_CHANCE", 0.20)}',
        "",
        f'BUBBLE_REFRESH_DELAY = {config.get("BUBBLE_REFRESH_DELAY", 2)}',
        "",
        f'POLL_SECONDS = {config.get("POLL_SECONDS", 180)}',
        "",
        f'RESTART_EVERY_CYCLES = {config.get("RESTART_EVERY_CYCLES", 40)}',
        "",
        f'CYCLE_TIMEOUT_SECONDS = {config.get("CYCLE_TIMEOUT_SECONDS", 240)}',
        "",
        f'SLEEP_GRANULARITY_SECONDS = {config.get("SLEEP_GRANULARITY_SECONDS", 5)}',
        "",
        f'NIGHT_MODE_ENABLED = {config.get("NIGHT_MODE_ENABLED", True)}',
        f'NIGHT_START_HOUR = {config.get("NIGHT_START_HOUR", 21)}',
        f'NIGHT_END_HOUR = {config.get("NIGHT_END_HOUR", 9)}',
        "",
        "CHANNEL_PAIRS = [",
    ])
    
    # Adiciona channel pairs
    for pair in config.get('CHANNEL_PAIRS', []):
        source = pair.get('source', '')
        target = pair.get('target', '')
        description = pair.get('description', '')
        lines.append(f'    ("{source}", "{target}", "{description}"),')
    
    lines.append("]")
    lines.append("")
    lines.append("GROUP_LINKS = {")
    
    # Adiciona group links
    for group_name, link in config.get('GROUP_LINKS', {}).items():
        lines.append(f'    "{group_name}": "{link}",')
    
    lines.append("}")
    
    content = "\n".join(lines)
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


@app.route('/api/config', methods=['GET'])
def get_config():
    """Retorna as configurações atuais"""
    try:
        config = parse_config_file()
        print(f"\n✅ Configurações carregadas do config.py:")
        print(f"   - GATILHOS: {len(config.get('GATILHOS', []))} itens")
        print(f"   - CHANNEL_PAIRS: {len(config.get('CHANNEL_PAIRS', []))} pares")
        print(f"   - GROUP_LINKS: {len(config.get('GROUP_LINKS', {}))} links")
        print(f"   - Tag afiliado: {config.get('MELI_AFFILIATE_TAG', 'N/A')}\n")
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        print(f"\n❌ Erro ao carregar configurações: {str(e)}\n")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config', methods=['POST'])
def update_config():
    """Atualiza as configurações"""
    try:
        new_config = request.json
        write_config_file(new_config)
        return jsonify({'success': True, 'message': 'Configurações salvas com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Verifica se a API está funcionando"""
    return jsonify({'status': 'ok'})


@app.route('/api/start-bot', methods=['POST'])
def start_bot():
    """Inicia a execução do bot"""
    global bot_process
    try:
        # Verifica se já existe um bot rodando
        if bot_process and bot_process.poll() is None:
            return jsonify({'success': False, 'error': 'Bot já está rodando. Pare-o antes de iniciar novamente.'}), 400
        
        # Caminho para o arquivo principal do bot
        bot_file = Path(__file__).parent / "run_bot.pyw"
        
        if not bot_file.exists():
            return jsonify({'success': False, 'error': 'Arquivo run_bot.pyw não encontrado'}), 404
        
        # Inicia o bot em um processo separado
        if sys.platform == 'win32':
            # Windows: usa pythonw para não abrir console
            CREATE_NO_WINDOW = 0x08000000
            bot_process = subprocess.Popen(['pythonw', str(bot_file)], 
                            cwd=str(bot_file.parent),
                            creationflags=CREATE_NO_WINDOW)
        else:
            # Linux/Mac: usa python normal em background
            bot_process = subprocess.Popen(['python3', str(bot_file)], 
                            cwd=str(bot_file.parent))
        
        return jsonify({'success': True, 'message': 'Bot iniciado com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stop-bot', methods=['POST'])
def stop_bot():
    """Para a execução do bot"""
    global bot_process
    try:
        if bot_process is None:
            return jsonify({'success': False, 'error': 'Nenhum bot está rodando.'}), 400
        
        # Verifica se o processo ainda está ativo
        if bot_process.poll() is not None:
            bot_process = None
            return jsonify({'success': False, 'error': 'O bot já foi encerrado.'}), 400
        
        # Termina o processo
        bot_process.terminate()
        
        # Aguarda até 5 segundos para finalizar graciosamente
        try:
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Se não finalizar, força o encerramento
            bot_process.kill()
            bot_process.wait()
        
        bot_process = None
        return jsonify({'success': True, 'message': 'Bot parado com sucesso!'})
    except Exception as e:
        bot_process = None
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bot-status', methods=['GET'])
def bot_status():
    """Retorna o status atual do bot"""
    global bot_process
    try:
        if bot_process is None:
            return jsonify({'running': False})
        
        # Verifica se o processo ainda está ativo
        if bot_process.poll() is None:
            return jsonify({'running': True})
        else:
            bot_process = None
            return jsonify({'running': False})
    except Exception as e:
        return jsonify({'running': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
