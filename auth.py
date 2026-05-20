from functools import wraps
from flask import session, redirect, url_for, flash
import hashlib
import pyodbc
from db_config import get_db_connection

# ─── Roles ────────────────────────────────────────────────────────────────────
ROL_ADMIN     = 'Administrador'
ROL_OPERADOR  = 'Operador'
ROL_VISITANTE = 'Visitante'

ROLES_JERARQUIA = {ROL_VISITANTE: 1, ROL_OPERADOR: 2, ROL_ADMIN: 3}

# ─── Hashing ──────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# ─── Verificar credenciales ───────────────────────────────────────────────────
def verificar_usuario(correo: str, password: str):
    """Retorna dict del usuario si las credenciales son válidas, None si no."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        pw_hash = hash_password(password)
        cursor.execute("""
            SELECT u.IdUsuario, u.Nombre, u.Correo, u.Estado,
                   r.NombreRol, r.IdRol
            FROM Usuarios u
            JOIN Roles r ON u.IdRol = r.IdRol
            WHERE u.Correo = ? AND u.PasswordHash = ? AND u.Estado = 'Activo'
        """, (correo, pw_hash))
        row = cursor.fetchone()
        if row:
            return {
                'id':     row[0],
                'nombre': row[1],
                'correo': row[2],
                'estado': row[3],
                'rol':    row[4],
                'rol_id': row[5],
            }
        return None
    except Exception as e:
        print(f"Error en verificar_usuario: {e}")
        return None
    finally:
        conn.close()

# ─── Bitácora ─────────────────────────────────────────────────────────────────
def registrar_evento(id_usuario: int, evento: str):
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO BitacoraEventos (IdUsuario, Evento)
            VALUES (?, ?)
        """, (id_usuario, evento))
        conn.commit()
    except Exception as e:
        print(f"Error registrando evento: {e}")
    finally:
        conn.close()

# ─── Decoradores de acceso ────────────────────────────────────────────────────
def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para acceder.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def rol_requerido(*roles_permitidos):
    """Uso: @rol_requerido('Administrador', 'Operador')"""
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

# ─── Gestión de usuarios (solo Admin) ────────────────────────────────────────
def crear_usuario(nombre, correo, password, id_rol):
    conn = get_db_connection()
    if not conn:
        return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        pw_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO Usuarios (IdRol, Nombre, Correo, PasswordHash)
            VALUES (?, ?, ?, ?)
        """, (id_rol, nombre, correo, pw_hash))
        conn.commit()
        return True, "Usuario creado correctamente"
    except pyodbc.IntegrityError:
        return False, "El correo ya está registrado"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def obtener_usuarios():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.IdUsuario, u.Nombre, u.Correo, u.Estado,
                   u.FechaCreacion, r.NombreRol
            FROM Usuarios u
            JOIN Roles r ON u.IdRol = r.IdRol
            ORDER BY u.FechaCreacion DESC
        """)
        return [{
            'id':     row[0],
            'nombre': row[1],
            'correo': row[2],
            'estado': row[3],
            'fecha':  row[4].strftime('%d/%m/%Y') if row[4] else '',
            'rol':    row[5],
        } for row in cursor.fetchall()]
    finally:
        conn.close()

def obtener_roles():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT IdRol, NombreRol FROM Roles ORDER BY IdRol")
        return [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    finally:
        conn.close()

def cambiar_estado_usuario(id_usuario, nuevo_estado):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Usuarios SET Estado = ? WHERE IdUsuario = ?",
            (nuevo_estado, id_usuario)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error cambiando estado: {e}")
        return False
    finally:
        conn.close()