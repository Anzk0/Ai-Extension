from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from indexer import index_vault
from retriever import retrieve_chunks
from claude_client import ask_claude

app = Flask(__name__)
CORS(app)  # TODO: restrict origins to extension ID before release


def load_config(path='config.json'):
    """Load configuration from a JSON file. Raises SystemExit with a clear message if file is missing or malformed."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"Config file not found: {path}. Copy config.example.json to config.json and fill in your values.")
    except json.JSONDecodeError as e:
        raise SystemExit(f"Config file is not valid JSON: {path} — {e}")


@app.route('/status')
def status():
    return jsonify({'status': 'ok'})


@app.route('/topics')
def topics():
    config = load_config()
    vault_path = config['vault_path']
    try:
        topic_list = [
            d for d in os.listdir(vault_path)
            if os.path.isdir(os.path.join(vault_path, d))
        ]
        return jsonify({'topics': topic_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask():
    config = load_config()
    data = request.get_json()
    question = data.get('question')
    topic = data.get('topic')

    if not question or not topic:
        return jsonify({'error': 'question and topic are required'}), 400

    chunks = retrieve_chunks(question, topic, config['chroma_db_path'])
    result = ask_claude(question, chunks, config['claude_api_key'])
    return jsonify(result)


@app.route('/index', methods=['POST'])
def index():
    config = load_config()
    result = index_vault(config['vault_path'], config['chroma_db_path'])
    return jsonify(result)


if __name__ == '__main__':
    import threading
    import pystray
    from PIL import Image as PILImage

    def create_tray():
        try:
            icon_img = PILImage.open('../extension/icons/icon48.png')
        except Exception:
            icon_img = PILImage.new('RGB', (48, 48), (167, 139, 250))

        def on_quit(icon, item):
            icon.stop()
            os._exit(0)

        tray = pystray.Icon(
            'StudyAI',
            icon_img,
            'Study AI Server — Running',
            menu=pystray.Menu(pystray.MenuItem('Quit', on_quit))
        )
        tray.run()

    tray_thread = threading.Thread(target=create_tray, daemon=True)
    tray_thread.start()
    print("Study AI server running on http://localhost:5000")
    app.run(port=5000, debug=False)
