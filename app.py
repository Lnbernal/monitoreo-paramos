from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from db_config import (
    obtener_estaciones, 
    obtener_ultima_lectura, 
    obtener_historico, 
    obtener_alertas,
    obtener_estadisticas
)
import os

app = Flask(__name__)
CORS(app)

# Obtener la ruta absoluta de la carpeta frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

@app.route('/')
def index():
    """Servir el dashboard HTML"""
    return send_from_directory(FRONTEND_DIR, 'dashboard.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Servir archivos estaticos (CSS, JS)"""
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/api/estaciones', methods=['GET'])
def get_estaciones():
    estaciones = obtener_estaciones()
    return jsonify(estaciones)

@app.route('/api/ultima-lectura', methods=['GET'])
def get_ultima_lectura():
    codigo_estacion = request.args.get('estacion')
    lectura = obtener_ultima_lectura(codigo_estacion)
    
    if lectura:
        return jsonify(lectura)
    return jsonify({'error': 'No hay lecturas disponibles'}), 404

@app.route('/api/historico/<codigo_estacion>', methods=['GET'])
def get_historico(codigo_estacion):
    limite = request.args.get('limite', 100, type=int)
    historico = obtener_historico(codigo_estacion, limite)
    return jsonify(historico)

@app.route('/api/alertas', methods=['GET'])
def get_alertas():
    codigo_estacion = request.args.get('estacion')
    alertas = obtener_alertas(codigo_estacion)
    return jsonify(alertas)

@app.route('/api/estadisticas/<codigo_estacion>', methods=['GET'])
def get_estadisticas(codigo_estacion):
    stats = obtener_estadisticas(codigo_estacion)
    if stats:
        return jsonify(stats)
    return jsonify({'error': 'No hay datos para esta estacion'}), 404

if __name__ == '__main__':
    print("=" * 50)
    print("SERVICIO DE MONITOREO DE PARAMOS")
    print("=" * 50)
    print(f"Directorio base: {BASE_DIR}")
    print(f"Directorio frontend: {FRONTEND_DIR}")
    print(f"Dashboard disponible en: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)