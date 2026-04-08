from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

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


if __name__ == '__main__':
    app.run(port=5000, debug=False)
