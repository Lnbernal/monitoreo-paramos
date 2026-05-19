-- =========================================================
-- CREAR BASE DE DATOS
-- =========================================================
CREATE DATABASE MonitoreoParamos;
GO

USE MonitoreoParamos;
GO

-- =========================================================
-- TABLA ROLES
-- =========================================================
CREATE TABLE Roles (
    IdRol INT PRIMARY KEY IDENTITY(1,1),
    NombreRol VARCHAR(50) NOT NULL,
    Descripcion VARCHAR(200)
);
GO

-- =========================================================
-- TABLA USUARIOS
-- =========================================================
CREATE TABLE Usuarios (
    IdUsuario INT PRIMARY KEY IDENTITY(1,1),
    IdRol INT NOT NULL,
    Nombre VARCHAR(100) NOT NULL,
    Correo VARCHAR(150) UNIQUE NOT NULL,
    PasswordHash VARCHAR(300) NOT NULL,
    Estado VARCHAR(50) DEFAULT 'Activo',
    FechaCreacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Usuarios_Roles FOREIGN KEY (IdRol) REFERENCES Roles(IdRol)
);
GO

-- =========================================================
-- TABLA ESTACIONES (con código único para identificar cada ESP32)
-- =========================================================
CREATE TABLE Estaciones (
    IdEstacion INT PRIMARY KEY IDENTITY(1,1),
    IdUsuario INT NOT NULL,
    NombreEstacion VARCHAR(100) NOT NULL,
    CodigoEstacion VARCHAR(50) UNIQUE NOT NULL,  -- Identificador único del ESP32
    Ubicacion VARCHAR(200),
    Latitud DECIMAL(10,6),
    Longitud DECIMAL(10,6),
    Altitud DECIMAL(6,2),
    Estado VARCHAR(50) DEFAULT 'Activa',
    FechaInstalacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Estaciones_Usuarios FOREIGN KEY (IdUsuario) REFERENCES Usuarios(IdUsuario)
);
GO

-- =========================================================
-- TABLA TIPOS SENSORES
-- =========================================================
CREATE TABLE TiposSensores (
    IdTipoSensor INT PRIMARY KEY IDENTITY(1,1),
    NombreSensor VARCHAR(100) NOT NULL,
    UnidadMedida VARCHAR(50),
    Descripcion VARCHAR(200)
);
GO

-- =========================================================
-- TABLA SENSORES (instancias físicas en cada estación)
-- =========================================================
CREATE TABLE Sensores (
    IdSensor INT PRIMARY KEY IDENTITY(1,1),
    IdEstacion INT NOT NULL,
    IdTipoSensor INT NOT NULL,
    CodigoSensor VARCHAR(100),
    Estado VARCHAR(50) DEFAULT 'Activo',
    FechaRegistro DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Sensores_Estaciones FOREIGN KEY (IdEstacion) REFERENCES Estaciones(IdEstacion),
    CONSTRAINT FK_Sensores_TiposSensores FOREIGN KEY (IdTipoSensor) REFERENCES TiposSensores(IdTipoSensor),
    CONSTRAINT UQ_Sensor_Estacion_Tipo UNIQUE (IdEstacion, IdTipoSensor)
);
GO

-- =========================================================
-- TABLA LECTURAS AMBIENTALES
-- =========================================================
CREATE TABLE LecturasAmbientales (
    IdLectura BIGINT PRIMARY KEY IDENTITY(1,1),
    IdEstacion INT NOT NULL,
    Temperatura DECIMAL(5,2),
    HumedadAire DECIMAL(5,2),
    HumedadSuelo INT,
    FechaHora DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Lecturas_Estaciones FOREIGN KEY (IdEstacion) REFERENCES Estaciones(IdEstacion),
    CONSTRAINT CK_Temperatura CHECK (Temperatura BETWEEN -20 AND 50),
    CONSTRAINT CK_HumedadAire CHECK (HumedadAire BETWEEN 0 AND 100),
    CONSTRAINT CK_HumedadSuelo CHECK (HumedadSuelo BETWEEN 0 AND 100)
);
GO

-- =========================================================
-- TABLA ALERTAS
-- =========================================================
CREATE TABLE Alertas (
    IdAlerta BIGINT PRIMARY KEY IDENTITY(1,1),
    IdEstacion INT NOT NULL,
    TipoAlerta VARCHAR(100),
    Descripcion VARCHAR(300),
    Nivel VARCHAR(50),
    FechaHora DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Alertas_Estaciones FOREIGN KEY (IdEstacion) REFERENCES Estaciones(IdEstacion)
);
GO

-- =========================================================
-- TABLA BITACORA EVENTOS
-- =========================================================
CREATE TABLE BitacoraEventos (
    IdEvento BIGINT PRIMARY KEY IDENTITY(1,1),
    IdUsuario INT NOT NULL,
    Evento VARCHAR(300),
    FechaEvento DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_Bitacora_Usuarios FOREIGN KEY (IdUsuario) REFERENCES Usuarios(IdUsuario)
);
GO

-- =========================================================
-- ÍNDICES PARA RENDIMIENTO
-- =========================================================
CREATE INDEX IX_Lecturas_FechaHora ON LecturasAmbientales(FechaHora DESC);
CREATE INDEX IX_Lecturas_IdEstacion_Fecha ON LecturasAmbientales(IdEstacion, FechaHora DESC);
CREATE INDEX IX_Alertas_FechaHora ON Alertas(FechaHora DESC);
CREATE INDEX IX_Alertas_IdEstacion ON Alertas(IdEstacion);
GO

-- =========================================================
-- PROCEDIMIENTO ALMACENADO PARA INSERTAR LECTURAS
-- =========================================================
CREATE OR ALTER PROCEDURE sp_InsertarLectura
    @CodigoEstacion VARCHAR(50),
    @Temperatura DECIMAL(5,2),
    @HumedadAire DECIMAL(5,2),
    @HumedadSuelo INT
AS
BEGIN
    DECLARE @IdEstacion INT;
    
    -- Obtener el IdEstacion por su código
    SELECT @IdEstacion = IdEstacion FROM Estaciones WHERE CodigoEstacion = @CodigoEstacion;
    
    IF @IdEstacion IS NULL
    BEGIN
        -- Si no existe, crear una nueva estación (requiere usuario admin)
        INSERT INTO Estaciones (IdUsuario, NombreEstacion, CodigoEstacion, Estado)
        VALUES (1, CONCAT('Estación ', @CodigoEstacion), @CodigoEstacion, 'Activa');
        
        SET @IdEstacion = SCOPE_IDENTITY();
    END
    
    -- Insertar la lectura
    INSERT INTO LecturasAmbientales (IdEstacion, Temperatura, HumedadAire, HumedadSuelo, FechaHora)
    VALUES (@IdEstacion, @Temperatura, @HumedadAire, @HumedadSuelo, GETDATE());
    
    -- Verificar alertas
    IF @HumedadSuelo < 30
    BEGIN
        INSERT INTO Alertas (IdEstacion, TipoAlerta, Descripcion, Nivel, FechaHora)
        VALUES (@IdEstacion, 'SUELO_SECO', 
                CONCAT('Humedad de suelo crítica: ', @HumedadSuelo, '%'), 
                'CRITICA', GETDATE());
    END
    ELSE IF @HumedadSuelo > 85
    BEGIN
        INSERT INTO Alertas (IdEstacion, TipoAlerta, Descripcion, Nivel, FechaHora)
        VALUES (@IdEstacion, 'SUELO_SATURADO', 
                CONCAT('Humedad de suelo excesiva: ', @HumedadSuelo, '%'), 
                'ADVERTENCIA', GETDATE());
    END
    
    SELECT @IdEstacion AS IdEstacion, SCOPE_IDENTITY() AS IdLectura;
END
GO

-- =========================================================
-- DATOS INICIALES
-- =========================================================

-- Roles
INSERT INTO Roles (NombreRol, Descripcion) VALUES
('Administrador', 'Control total del sistema'),
('Investigador', 'Consulta y análisis de datos'),
('Técnico', 'Mantenimiento de estaciones');
GO

-- Usuario admin (contraseña: Admin123*)
-- NOTA: En producción usar HASHBYTES con salt
INSERT INTO Usuarios (IdRol, Nombre, Correo, PasswordHash) VALUES
(1, 'Administrador Principal', 'admin@paramos.com', 'Admin123*');
GO

-- Tipos de sensores (ESP32)
INSERT INTO TiposSensores (NombreSensor, UnidadMedida, Descripcion) VALUES
('DHT11 Temperatura', '°C', 'Sensor de temperatura - ESP32'),
('DHT11 Humedad', '%', 'Sensor humedad relativa - ESP32'),
('Higrómetro', '%', 'Sensor humedad suelo - ESP32');
GO

-- Estación de ejemplo (Chingaza)
INSERT INTO Estaciones (IdUsuario, NombreEstacion, CodigoEstacion, Ubicacion, Latitud, Longitud, Altitud) VALUES
(1, 'Paramuno-Chingaza', 'PARAMO_001', 'Páramo de Chingaza', 4.528333, -73.742500, 3250.5);
GO

-- Sensores asignados a la estación
INSERT INTO Sensores (IdEstacion, IdTipoSensor, CodigoSensor) VALUES
(1, 1, 'CHINGAZA_DHT11_TEMP'),
(1, 2, 'CHINGAZA_DHT11_HUM'),
(1, 3, 'CHINGAZA_HIGRO');
GO

-- Verificar todo
SELECT '✅ Base de datos creada exitosamente' as Estado;
SELECT * FROM Roles;
SELECT * FROM Usuarios;
SELECT * FROM TiposSensores;
SELECT * FROM Estaciones;
SELECT * FROM Sensores;
GO