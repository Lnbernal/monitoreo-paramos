import pyodbc
from datetime import datetime
'''
DB_CONFIG = {
    'server': 'DESKTOP-CFO78OP',
    'database': 'MonitoreoParamos',
    'trusted_connection': 'yes'
}

def get_connection_string():
    return (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection=yes;"
    )

'''
DB_CONFIG = {
    'server':   'MonitoreoParamos.mssql.somee.com',
    'database': 'MonitoreoParamos',
    'username': 'JuanDa697_SQLLogin_1',
    'password': 's2pqdtcny5'
}

def get_connection_string():
    return (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={DB_CONFIG['server']};"
    f"DATABASE={DB_CONFIG['database']};"
    f"UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};"
     )

def get_db_connection():
    try:
        return pyodbc.connect(get_connection_string())
    except Exception as e:
        print(f"[DB] Error de conexión: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════════
#  LECTURAS
# ══════════════════════════════════════════════════════════════════════════════
def insertar_lectura(codigo_estacion, temperatura, humedad_aire, humedad_suelo):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_InsertarLectura ?, ?, ?, ?",
                       (codigo_estacion, temperatura, humedad_aire, humedad_suelo))
        conn.commit()
        print(f"[DB] Lectura guardada — estación: {codigo_estacion}")
        return True
    except Exception as e:
        print(f"[DB] Error insertando lectura: {e}")
        return False
    finally:
        conn.close()

def obtener_ultima_lectura(codigo_estacion=None):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        if codigo_estacion:
            cursor.execute("""
                SELECT TOP 1
                    la.Temperatura, la.HumedadAire, la.HumedadSuelo, la.FechaHora,
                    e.NombreEstacion, e.CodigoEstacion
                FROM LecturasAmbientales la
                JOIN Estaciones e ON la.IdEstacion = e.IdEstacion
                WHERE e.CodigoEstacion = ?
                ORDER BY la.FechaHora DESC
            """, (codigo_estacion,))
        else:
            cursor.execute("""
                SELECT TOP 1
                    la.Temperatura, la.HumedadAire, la.HumedadSuelo, la.FechaHora,
                    e.NombreEstacion, e.CodigoEstacion
                FROM LecturasAmbientales la
                JOIN Estaciones e ON la.IdEstacion = e.IdEstacion
                ORDER BY la.FechaHora DESC
            """)
        row = cursor.fetchone()
        if row:
            return {
                'temperatura':    float(row[0]) if row[0] is not None else None,
                'humedad_aire':   float(row[1]) if row[1] is not None else None,
                'humedad_suelo':  int(row[2])   if row[2] is not None else None,
                'fecha':          row[3].isoformat() if row[3] else None,
                'estacion_nombre': row[4],
                'estacion_codigo': row[5],
            }
        return None
    finally:
        conn.close()

def obtener_historico(codigo_estacion, limite=100):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT TOP {int(limite)}
                la.FechaHora, la.Temperatura, la.HumedadAire, la.HumedadSuelo
            FROM LecturasAmbientales la
            JOIN Estaciones e ON la.IdEstacion = e.IdEstacion
            WHERE e.CodigoEstacion = ?
            ORDER BY la.FechaHora DESC
        """, (codigo_estacion,))
        rows = cursor.fetchall()
        lecturas = [{
            'fecha':        r[0].isoformat(),
            'temperatura':  float(r[1]) if r[1] is not None else None,
            'humedad_aire': float(r[2]) if r[2] is not None else None,
            'humedad_suelo': int(r[3]) if r[3] is not None else None,
        } for r in rows]
        return lecturas[::-1]
    finally:
        conn.close()

def obtener_estadisticas(codigo_estacion):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                AVG(Temperatura)  AS TempProm,
                MIN(Temperatura)  AS TempMin,
                MAX(Temperatura)  AS TempMax,
                AVG(HumedadAire)  AS HumProm,
                AVG(CAST(HumedadSuelo AS FLOAT)) AS SueloProm,
                MIN(HumedadSuelo) AS SueloMin,
                MAX(HumedadSuelo) AS SueloMax,
                COUNT(*)          AS TotalLecturas
            FROM LecturasAmbientales la
            JOIN Estaciones e ON la.IdEstacion = e.IdEstacion
            WHERE e.CodigoEstacion = ?
              AND CAST(la.FechaHora AS DATE) = CAST(GETDATE() AS DATE)
        """, (codigo_estacion,))
        row = cursor.fetchone()
        if row and row[0] is not None:
            return {
                'temperatura_promedio': round(float(row[0]), 2),
                'temperatura_minima':  round(float(row[1]), 2) if row[1] else 0,
                'temperatura_maxima':  round(float(row[2]), 2) if row[2] else 0,
                'humedad_promedio':    round(float(row[3]), 2) if row[3] else 0,
                'suelo_promedio':      round(float(row[4]), 1) if row[4] else 0,
                'suelo_minimo':        int(row[5]) if row[5] else 0,
                'suelo_maximo':        int(row[6]) if row[6] else 0,
                'total_lecturas':      int(row[7]) if row[7] else 0,
            }
        return None
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  ESTACIONES
# ══════════════════════════════════════════════════════════════════════════════
def obtener_estaciones():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.IdEstacion, e.NombreEstacion, e.CodigoEstacion,
                   e.Ubicacion, e.Latitud, e.Longitud, e.Altitud, e.Estado,
                   e.FechaInstalacion,
                   (SELECT COUNT(*) FROM LecturasAmbientales la
                    WHERE la.IdEstacion = e.IdEstacion
                      AND la.FechaHora >= DATEADD(MINUTE,-5,GETDATE())) AS LectRecientes
            FROM Estaciones e
            ORDER BY e.NombreEstacion
        """)
        return [{
            'id':        r[0],
            'nombre':    r[1],
            'codigo':    r[2],
            'ubicacion': r[3] or 'No especificada',
            'latitud':   float(r[4]) if r[4] else 0,
            'longitud':  float(r[5]) if r[5] else 0,
            'altitud':   float(r[6]) if r[6] else 0,
            'estado':    r[7],
            'fecha_instalacion': r[8].strftime('%d/%m/%Y') if r[8] else '',
            'en_linea':  r[9] > 0,
        } for r in cursor.fetchall()]
    finally:
        conn.close()

def obtener_estacion_detalle(id_estacion):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT IdEstacion, NombreEstacion, CodigoEstacion,
                   Ubicacion, Latitud, Longitud, Altitud, Estado, FechaInstalacion
            FROM Estaciones WHERE IdEstacion = ?
        """, (id_estacion,))
        r = cursor.fetchone()
        if r:
            return {
                'id': r[0], 'nombre': r[1], 'codigo': r[2],
                'ubicacion': r[3], 'latitud': float(r[4]) if r[4] else 0,
                'longitud': float(r[5]) if r[5] else 0,
                'altitud': float(r[6]) if r[6] else 0,
                'estado': r[7],
                'fecha_instalacion': r[8].strftime('%d/%m/%Y') if r[8] else '',
            }
        return None
    finally:
        conn.close()

def crear_estacion(id_usuario, datos):
    conn = get_db_connection()
    if not conn:
        return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Estaciones
                (IdUsuario, NombreEstacion, CodigoEstacion, Ubicacion,
                 Latitud, Longitud, Altitud)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id_usuario, datos['nombre'], datos['codigo'], datos['ubicacion'],
              datos['latitud'], datos['longitud'], datos['altitud']))
        conn.commit()
        return True, f"Estación '{datos['nombre']}' creada correctamente"
    except pyodbc.IntegrityError:
        return False, "Ya existe una estación con ese código"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def actualizar_estacion(id_estacion, datos):
    conn = get_db_connection()
    if not conn:
        return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Estaciones
            SET NombreEstacion = ?, Ubicacion = ?,
                Latitud = ?, Longitud = ?, Altitud = ?, Estado = ?
            WHERE IdEstacion = ?
        """, (datos['nombre'], datos['ubicacion'],
              datos['latitud'], datos['longitud'], datos['altitud'],
              datos['estado'], id_estacion))
        conn.commit()
        return True, "Estación actualizada correctamente"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def eliminar_estacion(id_estacion):
    conn = get_db_connection()
    if not conn:
        return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Estaciones SET Estado='Inactiva' WHERE IdEstacion=?",
                       (id_estacion,))
        conn.commit()
        return True, "Estación desactivada correctamente"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  ALERTAS
# ══════════════════════════════════════════════════════════════════════════════
def obtener_alertas(codigo_estacion=None, limite=50):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        if codigo_estacion:
            cursor.execute(f"""
                SELECT TOP {int(limite)}
                    a.FechaHora, a.TipoAlerta, a.Descripcion, a.Nivel,
                    e.NombreEstacion, e.CodigoEstacion
                FROM Alertas a
                JOIN Estaciones e ON a.IdEstacion = e.IdEstacion
                WHERE e.CodigoEstacion = ?
                ORDER BY a.FechaHora DESC
            """, (codigo_estacion,))
        else:
            cursor.execute(f"""
                SELECT TOP {int(limite)}
                    a.FechaHora, a.TipoAlerta, a.Descripcion, a.Nivel,
                    e.NombreEstacion, e.CodigoEstacion
                FROM Alertas a
                JOIN Estaciones e ON a.IdEstacion = e.IdEstacion
                ORDER BY a.FechaHora DESC
            """)
        return [{
            'fecha':           r[0].isoformat(),
            'tipo':            r[1],
            'descripcion':     r[2],
            'nivel':           r[3],
            'estacion_nombre': r[4],
            'estacion_codigo': r[5],
        } for r in cursor.fetchall()]
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  RESUMEN GLOBAL (para tarjetas del dashboard)
# ══════════════════════════════════════════════════════════════════════════════
def obtener_resumen_global():
    conn = get_db_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM Estaciones WHERE Estado='Activa') AS Activas,
                (SELECT COUNT(*) FROM Estaciones
                 WHERE IdEstacion IN (
                     SELECT DISTINCT IdEstacion FROM LecturasAmbientales
                     WHERE FechaHora >= DATEADD(MINUTE,-5,GETDATE())
                 )) AS EnLinea,
                (SELECT COUNT(*) FROM LecturasAmbientales
                 WHERE CAST(FechaHora AS DATE) = CAST(GETDATE() AS DATE)) AS LectHoy,
                (SELECT COUNT(*) FROM Alertas
                 WHERE CAST(FechaHora AS DATE) = CAST(GETDATE() AS DATE)) AS AlertasHoy,
                (SELECT COUNT(*) FROM Alertas
                 WHERE Nivel='CRITICA'
                   AND CAST(FechaHora AS DATE) = CAST(GETDATE() AS DATE)) AS CriticasHoy
        """)
        r = cursor.fetchone()
        return {
            'estaciones_activas': r[0] or 0,
            'estaciones_en_linea': r[1] or 0,
            'lecturas_hoy': r[2] or 0,
            'alertas_hoy': r[3] or 0,
            'criticas_hoy': r[4] or 0,
        }
    finally:
        conn.close()