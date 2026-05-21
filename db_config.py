import pymssql

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE CONEXIÓN
# ══════════════════════════════════════════════════════════════════════════════

def get_db_connection():
    try:
        return pymssql.connect(
            server='MonitoreoParamos.mssql.somee.com',
            user='JuanDa697_SQLLogin_1',
            password='s2pqdtcny5',
            database='MonitoreoParamos',
            tds_version='7.0',
            timeout=30
        )
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
        cursor.callproc('sp_InsertarLectura',
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
        cursor = conn.cursor(as_dict=True)
        if codigo_estacion:
            cursor.execute("""
                SELECT TOP 1
                    la.Temperatura, la.HumedadAire, la.HumedadSuelo, la.FechaHora,
                    e.NombreEstacion, e.CodigoEstacion
                FROM LecturasAmbientales la
                JOIN Estaciones e ON la.IdEstacion = e.IdEstacion
                WHERE e.CodigoEstacion = %s
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
                'temperatura':     float(row['Temperatura']) if row['Temperatura'] is not None else None,
                'humedad_aire':    float(row['HumedadAire']) if row['HumedadAire'] is not None else None,
                'humedad_suelo':   int(row['HumedadSuelo'])  if row['HumedadSuelo'] is not None else None,
                'fecha':           row['FechaHora'].isoformat() if row['FechaHora'] else None,
                'estacion_nombre': row['NombreEstacion'],
                'estacion_codigo': row['CodigoEstacion'],
            }
        return None
    finally:
        conn.close()

def obtener_historico(codigo_estacion, limite=100):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(f"""
            SELECT TOP {int(limite)}
                la.FechaHora, la.Temperatura, la.HumedadAire, la.HumedadSuelo
            FROM LecturasAmbientales la
            JOIN Estaciones e ON la.IdEstacion = e.IdEstacion
            WHERE e.CodigoEstacion = %s
            ORDER BY la.FechaHora DESC
        """, (codigo_estacion,))
        rows = cursor.fetchall()
        lecturas = [{
            'fecha':         r['FechaHora'].isoformat(),
            'temperatura':   float(r['Temperatura'])  if r['Temperatura']  is not None else None,
            'humedad_aire':  float(r['HumedadAire'])  if r['HumedadAire']  is not None else None,
            'humedad_suelo': int(r['HumedadSuelo'])   if r['HumedadSuelo'] is not None else None,
        } for r in rows]
        return lecturas[::-1]
    finally:
        conn.close()

def obtener_estadisticas(codigo_estacion):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT
                AVG(Temperatura)                 AS TempProm,
                MIN(Temperatura)                 AS TempMin,
                MAX(Temperatura)                 AS TempMax,
                AVG(HumedadAire)                 AS HumProm,
                AVG(CAST(HumedadSuelo AS FLOAT)) AS SueloProm,
                MIN(HumedadSuelo)                AS SueloMin,
                MAX(HumedadSuelo)                AS SueloMax,
                COUNT(*)                         AS TotalLecturas
            FROM LecturasAmbientales la
            JOIN Estaciones e ON la.IdEstacion = e.IdEstacion
            WHERE e.CodigoEstacion = %s
              AND CAST(la.FechaHora AS DATE) = CAST(GETDATE() AS DATE)
        """, (codigo_estacion,))
        row = cursor.fetchone()
        if row and row['TempProm'] is not None:
            return {
                'temperatura_promedio': round(float(row['TempProm']), 2),
                'temperatura_minima':   round(float(row['TempMin']), 2) if row['TempMin'] else 0,
                'temperatura_maxima':   round(float(row['TempMax']), 2) if row['TempMax'] else 0,
                'humedad_promedio':     round(float(row['HumProm']), 2) if row['HumProm'] else 0,
                'suelo_promedio':       round(float(row['SueloProm']), 1) if row['SueloProm'] else 0,
                'suelo_minimo':         int(row['SueloMin']) if row['SueloMin'] else 0,
                'suelo_maximo':         int(row['SueloMax']) if row['SueloMax'] else 0,
                'total_lecturas':       int(row['TotalLecturas']) if row['TotalLecturas'] else 0,
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
        cursor = conn.cursor(as_dict=True)
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
            'id':                r['IdEstacion'],
            'nombre':            r['NombreEstacion'],
            'codigo':            r['CodigoEstacion'],
            'ubicacion':         r['Ubicacion'] or 'No especificada',
            'latitud':           float(r['Latitud'])  if r['Latitud']  else 0,
            'longitud':          float(r['Longitud']) if r['Longitud'] else 0,
            'altitud':           float(r['Altitud'])  if r['Altitud']  else 0,
            'estado':            r['Estado'],
            'fecha_instalacion': r['FechaInstalacion'].strftime('%d/%m/%Y') if r['FechaInstalacion'] else '',
            'en_linea':          r['LectRecientes'] > 0,
        } for r in cursor.fetchall()]
    finally:
        conn.close()

def obtener_estacion_detalle(id_estacion):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT IdEstacion, NombreEstacion, CodigoEstacion,
                   Ubicacion, Latitud, Longitud, Altitud, Estado, FechaInstalacion
            FROM Estaciones WHERE IdEstacion = %s
        """, (id_estacion,))
        r = cursor.fetchone()
        if r:
            return {
                'id':                r['IdEstacion'],
                'nombre':            r['NombreEstacion'],
                'codigo':            r['CodigoEstacion'],
                'ubicacion':         r['Ubicacion'],
                'latitud':           float(r['Latitud'])  if r['Latitud']  else 0,
                'longitud':          float(r['Longitud']) if r['Longitud'] else 0,
                'altitud':           float(r['Altitud'])  if r['Altitud']  else 0,
                'estado':            r['Estado'],
                'fecha_instalacion': r['FechaInstalacion'].strftime('%d/%m/%Y') if r['FechaInstalacion'] else '',
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
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (id_usuario, datos['nombre'], datos['codigo'], datos['ubicacion'],
              datos['latitud'], datos['longitud'], datos['altitud']))
        conn.commit()
        return True, f"Estación '{datos['nombre']}' creada correctamente"
    except Exception as e:
        if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
            return False, "Ya existe una estación con ese código"
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
            SET NombreEstacion = %s, Ubicacion = %s,
                Latitud = %s, Longitud = %s, Altitud = %s, Estado = %s
            WHERE IdEstacion = %s
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
        cursor.execute(
            "UPDATE Estaciones SET Estado='Inactiva' WHERE IdEstacion=%s",
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
        cursor = conn.cursor(as_dict=True)
        if codigo_estacion:
            cursor.execute(f"""
                SELECT TOP {int(limite)}
                    a.FechaHora, a.TipoAlerta, a.Descripcion, a.Nivel,
                    e.NombreEstacion, e.CodigoEstacion
                FROM Alertas a
                JOIN Estaciones e ON a.IdEstacion = e.IdEstacion
                WHERE e.CodigoEstacion = %s
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
            'fecha':           r['FechaHora'].isoformat(),
            'tipo':            r['TipoAlerta'],
            'descripcion':     r['Descripcion'],
            'nivel':           r['Nivel'],
            'estacion_nombre': r['NombreEstacion'],
            'estacion_codigo': r['CodigoEstacion'],
        } for r in cursor.fetchall()]
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  RESUMEN GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
def obtener_resumen_global():
    conn = get_db_connection()
    if not conn:
        return {'estaciones_activas':0,'estaciones_en_linea':0,
                'lecturas_hoy':0,'alertas_hoy':0,'criticas_hoy':0}
    try:
        cursor = conn.cursor(as_dict=True)
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
            'estaciones_activas':  r['Activas']    or 0,
            'estaciones_en_linea': r['EnLinea']    or 0,
            'lecturas_hoy':        r['LectHoy']    or 0,
            'alertas_hoy':         r['AlertasHoy'] or 0,
            'criticas_hoy':        r['CriticasHoy']or 0,
        }
    finally:
        conn.close()