import hashlib
import pyodbc

password = "Admin123*"  # cambia esto
pw_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-CFO78OP;"
    "DATABASE=MonitoreoParamos;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

# Insertar roles si no existen
cursor.execute("IF NOT EXISTS (SELECT 1 FROM Roles WHERE NombreRol='Administrador') INSERT INTO Roles (NombreRol, Descripcion) VALUES ('Administrador','Acceso total')")
cursor.execute("IF NOT EXISTS (SELECT 1 FROM Roles WHERE NombreRol='Operador')      INSERT INTO Roles (NombreRol, Descripcion) VALUES ('Operador','Ver y gestionar estaciones')")
cursor.execute("IF NOT EXISTS (SELECT 1 FROM Roles WHERE NombreRol='Visitante')     INSERT INTO Roles (NombreRol, Descripcion) VALUES ('Visitante','Solo lectura')")

# Insertar usuario admin
cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM Usuarios WHERE Correo='admin@paramos.co')
    INSERT INTO Usuarios (IdRol, Nombre, Correo, PasswordHash)
    VALUES (1, 'Administrador', 'admin@paramos.co', ?)
""", (pw_hash,))

conn.commit()
conn.close()
print(f"✓ Admin creado")
print(f"  Correo:     admin@paramos.co")
print(f"  Contraseña: {password}")
print(f"  Hash:       {pw_hash}")