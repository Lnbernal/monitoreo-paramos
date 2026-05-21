from functools import wraps
from flask import session, redirect, url_for, flash
import hashlib
from db_config import get_db_connection

ROL_ADMIN     = 'Administrador'
ROL_OPERADOR  = 'Operador'
ROL_VISITANTE = 'Visitante'

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verificar_usuario(correo: str, password: str):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(as_dict=True)
        pw_hash = hash_password(password)
        cursor.execute("""
            SELECT u.IdUsuario, u.Nombre, u.Correo, u.Estado,
                   r.NombreRol, r.IdRol
            FROM Usuarios u
            JOIN Roles r ON u.IdRol = r.IdRol
            WHERE u.Correo = %s AND u.PasswordHash = %s AND u.Estado = 'Activo'
        """, (correo, pw_hash))
        row = cursor.fetchone()
        if row:
            return {
                'id':     row['IdUsuario'],
                'nombre': row['Nombre'],
                'correo': row['Correo'],
                'estado': row['Estado'],
                'rol':    row['NombreRol'],
                'rol_id': row['IdRol'],
            }
        return None
    except Exception as e:
        print(f"[Auth] Error en verificar_usuario: {e}")
        return None
    finally:
        conn.close()

def registrar_evento(id_usuario: int, evento: str):
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO BitacoraEventos (IdUsuario, Evento) VALUES (%s, %s)",
            (id_usuario, evento))
        conn.commit()
    except Exception as e:
        print(f"[Auth] Error registrando evento: {e}")
    finally:
        conn.close()

def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para acceder.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def rol_requerido(*roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'usuario_id' not in session:
                flash('Debes iniciar sesión.', 'warning')
                return redirect(url_for('login'))
            if session.get('rol') not in roles_permitidos:
                flash('No tienes permisos para esta acción.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def crear_usuario(nombre, correo, password, id_rol):
    conn = get_db_connection()
    if not conn:
        return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        pw_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO Usuarios (IdRol, Nombre, Correo, PasswordHash)
            VALUES (%s, %s, %s, %s)
        """, (id_rol, nombre, correo, pw_hash))
        conn.commit()
        return True, "Usuario creado correctamente"
    except Exception as e:
        if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
            return False, "El correo ya está registrado"
        return False, str(e)
    finally:
        conn.close()

def obtener_usuarios():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT u.IdUsuario, u.Nombre, u.Correo, u.Estado,
                   u.FechaCreacion, r.NombreRol
            FROM Usuarios u
            JOIN Roles r ON u.IdRol = r.IdRol
            ORDER BY u.FechaCreacion DESC
        """)
        return [{
            'id':     r['IdUsuario'],
            'nombre': r['Nombre'],
            'correo': r['Correo'],
            'estado': r['Estado'],
            'fecha':  r['FechaCreacion'].strftime('%d/%m/%Y') if r['FechaCreacion'] else '',
            'rol':    r['NombreRol'],
        } for r in cursor.fetchall()]
    finally:
        conn.close()

def obtener_roles():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT IdRol, NombreRol FROM Roles ORDER BY IdRol")
        return [{'id': r['IdRol'], 'nombre': r['NombreRol']} for r in cursor.fetchall()]
    finally:
        conn.close()

def cambiar_estado_usuario(id_usuario, nuevo_estado):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Usuarios SET Estado = %s WHERE IdUsuario = %s",
            (nuevo_estado, id_usuario))
        conn.commit()
        return True
    except Exception as e:
        print(f"[Auth] Error cambiando estado: {e}")
        return False
    finally:
        conn.close()