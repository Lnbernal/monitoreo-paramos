import pyodbc
from datetime import datetime

DB_CONFIG = {
    'server': 'MonitoreoParamos.mssql.somee.com',      # El servidor que te da Somee
    'database': 'MonitoreoParamos',   # El nombre de tu BD en Somee
    'username': 'JuanDa697_SQLLogin_1',   # Tu usuario de Somee
    'password': 's2pqdtcny5'       # Tu contraseña de Somee
}

def get_connection_string():
    # Para Somee se usa UID y PWD, NO Trusted_Connection
    return f"""
        DRIVER={{ODBC Driver 17 for SQL Server}};
        SERVER={DB_CONFIG['server']};
        DATABASE={DB_CONFIG['database']};
        UID={DB_CONFIG['username']};
        PWD={DB_CONFIG['password']};
    """

def get_db_connection():
    try:
        conn = pyodbc.connect(get_connection_string())
        return conn
    except Exception as e:
        print(f"Error conectando a BD: {e}")
        return None

def insertar_lectura(codigo_estacion, temperatura, humedad_aire, humedad_suelo):
    """Inserta una lectura usando el stored procedure"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXEC sp_InsertarLectura ?, ?, ?, ?
        """, (codigo_estacion, temperatura, humedad_aire, humedad_suelo))
        
        conn.commit()
        print(f"Lectura guardada - Estacion: {codigo_estacion}")
        return True
    except Exception as e:
        print(f"Error insertando lectura: {e}")
        return False
    finally:
        conn.close()

def obtener_estaciones():
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT IdEstacion, NombreEstacion, CodigoEstacion, Ubicacion, 
               Latitud, Longitud, Altitud
        FROM Estaciones
        WHERE Estado = 'Activa'
        ORDER BY NombreEstacion
    """)
    
    estaciones = []
    for row in cursor:
        estaciones.append({
            'id': row[0],
            'nombre': row[1],
            'codigo': row[2],
            'ubicacion': row[3] or 'No especificada',
            'latitud': float(row[4]) if row[4] else 0,
            'longitud': float(row[5]) if row[5] else 0,
            'altitud': float(row[6]) if row[6] else 0
        })
    
    conn.close()
    return estaciones

def obtener_ultima_lectura(codigo_estacion=None):
    conn = get_db_connection()
    if not conn:
        return None
    
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
    conn.close()
    
    if row:
        return {
            'temperatura': float(row[0]) if row[0] else None,
            'humedad_aire': float(row[1]) if row[1] else None,
            'humedad_suelo': row[2] if row[2] else None,
            'fecha': row[3].isoformat() if row[3] else None,
            'estacion_nombre': row[4],
            'estacion_codigo': row[5]
        }
    return None

def obtener_historico(codigo_estacion, limite=100):
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT TOP {limite}
            la.FechaHora, la.Temperatura, la.HumedadAire, la.HumedadSuelo
        FROM LecturasAmbientales la
        JOIN Estaciones e ON la.IdEstacion = e.IdEstacion
        WHERE e.CodigoEstacion = ?
        ORDER BY la.FechaHora DESC
    """, (codigo_estacion,))
    
    lecturas = []
    for row in cursor:
        lecturas.append({
            'fecha': row[0].isoformat(),
            'temperatura': float(row[1]) if row[1] else None,
            'humedad_aire': float(row[2]) if row[2] else None,
            'humedad_suelo': row[3] if row[3] else None
        })
    
    conn.close()
    return lecturas[::-1]

def obtener_alertas(codigo_estacion=None, limite=50):
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    if codigo_estacion:
        cursor.execute(f"""
            SELECT TOP {limite}
                a.FechaHora, a.TipoAlerta, a.Descripcion, a.Nivel,
                e.NombreEstacion, e.CodigoEstacion
            FROM Alertas a
            JOIN Estaciones e ON a.IdEstacion = e.IdEstacion
            WHERE e.CodigoEstacion = ?
            ORDER BY a.FechaHora DESC
        """, (codigo_estacion,))
    else:
        cursor.execute(f"""
            SELECT TOP {limite}
                a.FechaHora, a.TipoAlerta, a.Descripcion, a.Nivel,
                e.NombreEstacion, e.CodigoEstacion
            FROM Alertas a
            JOIN Estaciones e ON a.IdEstacion = e.IdEstacion
            ORDER BY a.FechaHora DESC
        """)
    
    alertas = []
    for row in cursor:
        alertas.append({
            'fecha': row[0].isoformat(),
            'tipo': row[1],
            'descripcion': row[2],
            'nivel': row[3],
            'estacion_nombre': row[4],
            'estacion_codigo': row[5]
        })
    
    conn.close()
    return alertas

def obtener_estadisticas(codigo_estacion):
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            AVG(Temperatura) as TempProm,
            MIN(Temperatura) as TempMin,
            MAX(Temperatura) as TempMax,
            AVG(HumedadAire) as HumProm,
            AVG(HumedadSuelo) as SueloProm,
            MIN(HumedadSuelo) as SueloMin,
            MAX(HumedadSuelo) as SueloMax,
            COUNT(*) as TotalLecturas
        FROM LecturasAmbientales la
        JOIN Estaciones e ON la.IdEstacion = e.IdEstacion
        WHERE e.CodigoEstacion = ?
        AND CAST(la.FechaHora AS DATE) = CAST(GETDATE() AS DATE)
    """, (codigo_estacion,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] is not None:
        return {
            'temperatura_promedio': float(row[0]),
            'temperatura_minima': float(row[1]) if row[1] else 0,
            'temperatura_maxima': float(row[2]) if row[2] else 0,
            'humedad_promedio': float(row[3]) if row[3] else 0,
            'suelo_promedio': int(row[4]) if row[4] else 0,
            'suelo_minimo': int(row[5]) if row[5] else 0,
            'suelo_maximo': int(row[6]) if row[6] else 0,
            'total_lecturas': int(row[7]) if row[7] else 0
        }
    return None