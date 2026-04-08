from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)


def load_config():
    with open('config.json') as f:
        return json.load(f)


@app.route('/status')
def status():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(port=5000, debug=False)
