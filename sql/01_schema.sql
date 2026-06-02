-- ============================================================
--  REPROCESOS — Schema SQL para Supabase (PostgreSQL 15)
--  Ejecutar en: Supabase Dashboard → SQL Editor
-- ============================================================

-- Habilitar extensión UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ============================================================
-- 1. TABLA VEHICULOS (sincronizada del REPORTE_UBICACION)
-- ============================================================
CREATE TABLE IF NOT EXISTS vehiculos (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin                   TEXT UNIQUE NOT NULL,
    taller                TEXT,
    color                 TEXT,
    fecha_planificada     DATE,
    fecha_ingreso_flujo   DATE,
    dias_transcurridos    INTEGER,
    modelo                TEXT,
    marca                 TEXT,
    proceso               TEXT,       -- Zona actual del vehículo (19 zonas)
    estado                TEXT,       -- EN PROCESO | PENDIENTE
    concesionario         TEXT,
    observaciones         TEXT,
    sincronizado_en       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vehiculos_proceso ON vehiculos(proceso);
CREATE INDEX IF NOT EXISTS idx_vehiculos_estado ON vehiculos(estado);


-- ============================================================
-- 2. TABLA DAÑOS PINTURA (sincronizada del REPORTE_PINTURA)
-- ============================================================
CREATE TABLE IF NOT EXISTS danos_pintura (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin              TEXT NOT NULL,
    fecha_hora       TIMESTAMPTZ,
    marca            TEXT,
    modelo           TEXT,
    procedencia      TEXT,        -- RECEPCIÓN | BOCAMAZA
    seccion          TEXT,        -- Parte del vehículo afectada
    diagnostico_esum TEXT,        -- Código eSUM (Ryd, etc.)
    validacion       TEXT,        -- PASA | PAÑOS | PULIR | REVISAR
    num_panos        NUMERIC,
    comentario       TEXT,
    colaborador      TEXT,
    sincronizado_en  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_danos_pintura_vin ON danos_pintura(vin);
CREATE INDEX IF NOT EXISTS idx_danos_pintura_fecha ON danos_pintura(fecha_hora);


-- ============================================================
-- 3. TABLA DAÑOS REPUESTO (sincronizada del REPORTE_REPUESTO)
-- ============================================================
CREATE TABLE IF NOT EXISTS danos_repuesto (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin                    TEXT NOT NULL,
    taller                 TEXT,
    marca                  TEXT,
    modelo                 TEXT,
    anio                   TEXT,
    color                  TEXT,
    procedencia            TEXT,
    seccion                TEXT,
    diagnostico            TEXT,
    num_pedido             TEXT,
    fecha_registro         DATE,
    validado_por           TEXT,
    validacion_cliente     TEXT,
    fecha_val_cliente      DATE,
    comentario_val_cliente TEXT,
    fecha_termino          DATE,
    link_evidencia_1       TEXT,
    link_evidencia_2       TEXT,
    link_evidencia_3       TEXT,
    link_evidencia_4       TEXT,
    link_evidencia_5       TEXT,
    link_evidencia_6       TEXT,
    link_evidencia_7       TEXT,
    sincronizado_en        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_danos_repuesto_vin ON danos_repuesto(vin);
CREATE INDEX IF NOT EXISTS idx_danos_repuesto_fecha ON danos_repuesto(fecha_registro);


-- ============================================================
-- 4. TABLA USUARIOS (de la app, no de eSUM)
-- ============================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre        TEXT NOT NULL,
    usuario       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,          -- bcrypt hash
    rol           TEXT NOT NULL,          -- control_calidad | operario_pintura | operario_repuesto
    activo        BOOLEAN DEFAULT TRUE,
    creado_en     TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT rol_valido CHECK (rol IN ('control_calidad', 'operario_pintura', 'operario_repuesto'))
);


-- ============================================================
-- 5. TABLA REPROCESOS (creados por Control de Calidad)
-- ============================================================
CREATE TABLE IF NOT EXISTS reprocesos (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin              TEXT NOT NULL REFERENCES vehiculos(vin) ON DELETE CASCADE,
    creado_por       UUID NOT NULL REFERENCES usuarios(id),
    estado           TEXT DEFAULT 'pendiente',
    notas_cc         TEXT,
    foto_inicial_url TEXT,
    creado_en        TIMESTAMPTZ DEFAULT NOW(),
    cerrado_en       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_reprocesos_vin ON reprocesos(vin);
CREATE INDEX IF NOT EXISTS idx_reprocesos_estado ON reprocesos(estado);
CREATE INDEX IF NOT EXISTS idx_reprocesos_creado_por ON reprocesos(creado_por);


-- ============================================================
-- 6. TABLA ITEMS REPROCESO PINTURA (ítems que CC agregó)
-- ============================================================
CREATE TABLE IF NOT EXISTS items_reproceso_pintura (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reproceso_id  UUID NOT NULL REFERENCES reprocesos(id) ON DELETE CASCADE,
    seccion       TEXT,
    observacion   TEXT NOT NULL,
    estado        TEXT DEFAULT 'pendiente',
    foto_url      TEXT,
    creado_en     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_items_pintura_reproceso ON items_reproceso_pintura(reproceso_id);
CREATE INDEX IF NOT EXISTS idx_items_pintura_estado ON items_reproceso_pintura(estado);


-- ============================================================
-- 7. TABLA ITEMS REPROCESO REPUESTO (ítems que CC agregó)
-- ============================================================
CREATE TABLE IF NOT EXISTS items_reproceso_repuesto (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reproceso_id  UUID NOT NULL REFERENCES reprocesos(id) ON DELETE CASCADE,
    seccion       TEXT,
    observacion   TEXT NOT NULL,
    estado        TEXT DEFAULT 'pendiente',
    foto_url      TEXT,
    creado_en     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_items_repuesto_reproceso ON items_reproceso_repuesto(reproceso_id);
CREATE INDEX IF NOT EXISTS idx_items_repuesto_estado ON items_reproceso_repuesto(estado);


-- ============================================================
-- 8. TABLA TRABAJOS PINTURA (registro del operario de pintura)
-- ============================================================
CREATE TABLE IF NOT EXISTS trabajos_pintura (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id      UUID NOT NULL REFERENCES items_reproceso_pintura(id) ON DELETE CASCADE,
    operario_id  UUID NOT NULL REFERENCES usuarios(id),
    estado       TEXT NOT NULL DEFAULT 'abierto', -- abierto | cerrado
    abierto_en   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cerrado_en   TIMESTAMPTZ,
    foto_url     TEXT,          -- URL Google Drive (WebP)
    notas        TEXT
);

CREATE INDEX IF NOT EXISTS idx_trabajos_pintura_item ON trabajos_pintura(item_id);
CREATE INDEX IF NOT EXISTS idx_trabajos_pintura_operario ON trabajos_pintura(operario_id);
CREATE INDEX IF NOT EXISTS idx_trabajos_pintura_estado ON trabajos_pintura(estado);


-- ============================================================
-- 9. TABLA TRABAJOS REPUESTO (registro del operario de repuesto)
-- ============================================================
CREATE TABLE IF NOT EXISTS trabajos_repuesto (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id      UUID NOT NULL REFERENCES items_reproceso_repuesto(id) ON DELETE CASCADE,
    operario_id  UUID NOT NULL REFERENCES usuarios(id),
    estado       TEXT NOT NULL DEFAULT 'abierto', -- abierto | cerrado
    abierto_en   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cerrado_en   TIMESTAMPTZ,
    foto_url     TEXT,
    notas        TEXT
);

CREATE INDEX IF NOT EXISTS idx_trabajos_repuesto_item ON trabajos_repuesto(item_id);
CREATE INDEX IF NOT EXISTS idx_trabajos_repuesto_operario ON trabajos_repuesto(operario_id);
CREATE INDEX IF NOT EXISTS idx_trabajos_repuesto_estado ON trabajos_repuesto(estado);


-- ============================================================
-- 10. TABLA SYNC LOG (historial de sincronizaciones)
-- ============================================================
CREATE TABLE IF NOT EXISTS sync_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporte         TEXT NOT NULL,    -- ubicacion | pintura | repuesto
    estado          TEXT NOT NULL,    -- success | error
    filas_procesadas INTEGER,
    mensaje         TEXT,
    ejecutado_en    TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================
-- DATOS INICIALES — Usuario administrador / Control de Calidad
-- Nota: El password 'admin123' hasheado con bcrypt (lo cambia el admin)
-- El backend se encargará de hashear con bcrypt al crear usuarios.
-- Este INSERT usa una nota para que el admin lo cree vía API.
-- ============================================================

-- Insertar usuario CC de ejemplo (contraseña: admin123)
-- IMPORTANTE: Cambiar la contraseña en el primer login
INSERT INTO usuarios (nombre, usuario, password_hash, rol)
VALUES (
    'Administrador CC',
    'admin',
    -- bcrypt hash de 'admin123' con cost=12
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMaWkalqrsL.9yX2sDnuVdZq7a',
    'control_calidad'
)
ON CONFLICT (usuario) DO NOTHING;


-- ============================================================
-- VIEWS ÚTILES
-- ============================================================

-- Vista: vehículos con conteo de daños y reprocesos activos
CREATE OR REPLACE VIEW vista_vehiculos_resumen AS
SELECT
    v.vin,
    v.taller,
    v.modelo,
    v.marca,
    v.color,
    v.proceso,
    v.estado,
    v.fecha_ingreso_flujo,
    v.dias_transcurridos,
    v.concesionario,
    COUNT(DISTINCT dp.id) AS total_danos_pintura,
    COUNT(DISTINCT dr.id) AS total_danos_repuesto,
    COUNT(DISTINCT r.id) FILTER (WHERE r.estado != 'cerrado') AS reprocesos_activos
FROM vehiculos v
LEFT JOIN danos_pintura dp ON dp.vin = v.vin
LEFT JOIN danos_repuesto dr ON dr.vin = v.vin
LEFT JOIN reprocesos r ON r.vin = v.vin
GROUP BY v.vin, v.taller, v.modelo, v.marca, v.color, v.proceso, v.estado,
         v.fecha_ingreso_flujo, v.dias_transcurridos, v.concesionario;


-- Vista: items pendientes de pintura con info del reproceso y vehículo
CREATE OR REPLACE VIEW vista_items_pintura_pendientes AS
SELECT
    ip.id AS item_id,
    ip.seccion,
    ip.observacion,
    ip.estado,
    ip.creado_en,
    r.id AS reproceso_id,
    r.vin,
    r.notas_cc,
    v.modelo,
    v.marca,
    v.color,
    v.proceso AS proceso_vehiculo,
    u.nombre AS creado_por_nombre
FROM items_reproceso_pintura ip
JOIN reprocesos r ON r.id = ip.reproceso_id
LEFT JOIN vehiculos v ON v.vin = r.vin
JOIN usuarios u ON u.id = r.creado_por
WHERE ip.estado = 'pendiente';


-- Vista: items pendientes de repuesto con info del reproceso y vehículo
CREATE OR REPLACE VIEW vista_items_repuesto_pendientes AS
SELECT
    ir.id AS item_id,
    ir.seccion,
    ir.observacion,
    ir.estado,
    ir.creado_en,
    r.id AS reproceso_id,
    r.vin,
    r.notas_cc,
    v.modelo,
    v.marca,
    v.color,
    v.proceso AS proceso_vehiculo,
    u.nombre AS creado_por_nombre
FROM items_reproceso_repuesto ir
JOIN reprocesos r ON r.id = ir.reproceso_id
LEFT JOIN vehiculos v ON v.vin = r.vin
JOIN usuarios u ON u.id = r.creado_por
WHERE ir.estado = 'pendiente';
