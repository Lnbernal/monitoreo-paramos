from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from datetime import timedelta
import os
import threading

from db_config import (
    obtener_estaciones,
    obtener_ultima_lectura,
    obtener_historico,
    obtener_alertas,
    obtener_estadisticas,
    obtener_estacion_detalle,
    crear_estacion,
    actualizar_estacion,
    eliminar_estacion,
    obtener_resumen_global,
)
from auth import (
    verificar_usuario, registrar_evento, login_requerido, rol_requerido,
    crear_usuario, obtener_usuarios, obtener_roles, cambiar_estado_usuario,
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'paramos-secret-2026-monitoreo')
app.permanent_session_lifetime = timedelta(hours=8)
CORS(app)

# ══════════════════════════════════════════════════════════════════════════════
#  MQTT en hilo de fondo
# ══════════════════════════════════════════════════════════════════════════════
def iniciar_mqtt():
    """Arranca el listener MQTT en un thread daemon (muere con el proceso)."""
    try:
        from mqtt_listener import start_listener
        print("[MQTT] Iniciando listener en hilo de fondo...")
        start_listener()
    except Exception as e:
        print(f"[MQTT] Error al iniciar listener: {e}")

def arrancar_mqtt_thread():
    t = threading.Thread(target=iniciar_mqtt, daemon=True, name="mqtt-listener")
    t.start()
    print("[MQTT] Thread iniciado")

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        correo   = request.form.get('correo', '').strip()
        password = request.form.get('password', '')
        usuario  = verificar_usuario(correo, password)
        if usuario:
            session.permanent = True
            session['usuario_id'] = usuario['id']
            session['nombre']     = usuario['nombre']
            session['correo']     = usuario['correo']
            session['rol']        = usuario['rol']
            registrar_evento(usuario['id'], f"Inicio de sesión desde {request.remote_addr}")
            flash(f"Bienvenido, {usuario['nombre']}", 'success')
            return redirect(url_for('dashboard'))
        flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_requerido
def logout():
    registrar_evento(session['usuario_id'], "Cierre de sesión")
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/dashboard')
@login_requerido
def dashboard():
    estaciones = obtener_estaciones()
    resumen    = obtener_resumen_global()
    alertas    = obtener_alertas(limite=10)
    return render_template('dashboard.html',
                           estaciones=estaciones,
                           resumen=resumen,
                           alertas=alertas)

# ══════════════════════════════════════════════════════════════════════════════
#  ESTACIONES
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/estaciones')
@login_requerido
def estaciones():
    lista = obtener_estaciones()
    return render_template('estaciones.html', estaciones=lista)

@app.route('/estaciones/nueva', methods=['GET', 'POST'])
@rol_requerido('Administrador', 'Operador')
def nueva_estacion():
    if request.method == 'POST':
        datos = {
            'nombre':    request.form.get('nombre'),
            'codigo':    request.form.get('codigo'),
            'ubicacion': request.form.get('ubicacion'),
            'latitud':   request.form.get('latitud') or None,
            'longitud':  request.form.get('longitud') or None,
            'altitud':   request.form.get('altitud') or None,
        }
        ok, msg = crear_estacion(session['usuario_id'], datos)
        if ok:
            registrar_evento(session['usuario_id'], f"Creó estación: {datos['codigo']}")
            flash(msg, 'success')
            return redirect(url_for('estaciones'))
        flash(msg, 'danger')
    return render_template('estaciones.html', modo='nueva')

@app.route('/estaciones/editar/<int:id_estacion>', methods=['POST'])
@rol_requerido('Administrador', 'Operador')
def editar_estacion(id_estacion):
    datos = {
        'nombre':    request.form.get('nombre'),
        'ubicacion': request.form.get('ubicacion'),
        'latitud':   request.form.get('latitud') or None,
        'longitud':  request.form.get('longitud') or None,
        'altitud':   request.form.get('altitud') or None,
        'estado':    request.form.get('estado'),
    }
    ok, msg = actualizar_estacion(id_estacion, datos)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('estaciones'))

@app.route('/estaciones/eliminar/<int:id_estacion>', methods=['POST'])
@rol_requerido('Administrador')
def eliminar_estacion_route(id_estacion):
    ok, msg = eliminar_estacion(id_estacion)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('estaciones'))

# ══════════════════════════════════════════════════════════════════════════════
#  USUARIOS (solo Admin)
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/usuarios')
@rol_requerido('Administrador')
def usuarios():
    lista = obtener_usuarios()
    roles = obtener_roles()
    return render_template('usuarios.html', usuarios=lista, roles=roles)

@app.route('/usuarios/crear', methods=['POST'])
@rol_requerido('Administrador')
def crear_usuario_route():
    nombre   = request.form.get('nombre')
    correo   = request.form.get('correo')
    password = request.form.get('password')
    id_rol   = request.form.get('id_rol')
    ok, msg  = crear_usuario(nombre, correo, password, id_rol)
    registrar_evento(session['usuario_id'], f"Creó usuario: {correo}")
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('usuarios'))

@app.route('/usuarios/estado/<int:id_usuario>', methods=['POST'])
@rol_requerido('Administrador')
def cambiar_estado_route(id_usuario):
    estado = request.form.get('estado')
    ok = cambiar_estado_usuario(id_usuario, estado)
    registrar_evento(session['usuario_id'], f"Cambió estado de usuario {id_usuario} a {estado}")
    flash('Estado actualizado.' if ok else 'Error al actualizar.',
          'success' if ok else 'danger')
    return redirect(url_for('usuarios'))

@app.route('/test-db')
def test_db():
    try:
        from db_config import get_db_connection
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Usuarios")
            count = cursor.fetchone()[0]
            conn.close()
            return f"✓ Conexión OK — {count} usuarios en BD"
        else:
            return "✗ get_db_connection() retornó None", 500
    except Exception as e:
        return f"✗ Error: {str(e)}", 500
# ══════════════════════════════════════════════════════════════════════════════
#  API JSON
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/api/estaciones')
@login_requerido
def api_estaciones():
    return jsonify(obtener_estaciones())

@app.route('/api/ultima-lectura')
@login_requerido
def api_ultima_lectura():
    codigo = request.args.get('estacion')
    lectura = obtener_ultima_lectura(codigo)
    return jsonify(lectura) if lectura else (jsonify({'error': 'Sin datos'}), 404)

@app.route('/api/historico/<codigo_estacion>')
@login_requerido
def api_historico(codigo_estacion):
    limite = request.args.get('limite', 100, type=int)
    return jsonify(obtener_historico(codigo_estacion, limite))

@app.route('/api/alertas')
@login_requerido
def api_alertas():
    codigo = request.args.get('estacion')
    return jsonify(obtener_alertas(codigo))

@app.route('/api/estadisticas/<codigo_estacion>')
@login_requerido
def api_estadisticas(codigo_estacion):
    stats = obtener_estadisticas(codigo_estacion)
    return jsonify(stats) if stats else (jsonify({'error': 'Sin datos'}), 404)

@app.route('/api/resumen')
@login_requerido
def api_resumen():
    return jsonify(obtener_resumen_global())

# ══════════════════════════════════════════════════════════════════════════════
#  ARRANQUE
# ══════════════════════════════════════════════════════════════════════════════
# Iniciamos MQTT una sola vez (evita doble arranque del reloader de Flask)
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    arrancar_mqtt_thread()

if __name__ == '__main__':
    print("=" * 55)
    print("  SISTEMA DE MONITOREO DE PÁRAMOS")
    print("=" * 55)
    print("  Dashboard: http://localhost:5000")
    print("=" * 55)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)