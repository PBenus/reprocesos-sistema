# 🚗 Sistema de Control de Reprocesos — VARI OVALO

Sistema web para gestionar los reprocesos internos de pintura y repuestos, integrando datos en tiempo real del sistema eSUM.

---

## 📁 Estructura del Proyecto

```
C:\SUM_2025\REPROCESOS\
│
├── .env                     ← 🔑 Credenciales (CONFIGURAR ANTES DE ARRANCAR)
├── .gitignore
├── sql/
│   └── 01_schema.sql        ← Ejecutar en Supabase SQL Editor
│
├── ingestion/               ← Módulo 1: Descarga automática desde eSUM
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── dags/                ← DAG de Airflow (cada 10 min)
│   └── tasks/               ← Descarga + parseo + sync a Supabase
│
├── backend/                 ← Módulo 2: API REST con FastAPI
│   ├── main.py
│   ├── auth/
│   ├── routers/
│   └── schemas/
│
└── frontend/                ← Módulo 3: App React
    └── src/
        ├── pages/
        └── components/
```

---

## ⚡ Inicio Rápido

### Prerrequisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- [Node.js 18+](https://nodejs.org/) instalado
- [Python 3.11+](https://www.python.org/) instalado
- Proyecto en [Supabase](https://supabase.com/) creado

### 1. Configurar variables de entorno

Edita el archivo `.env` en la raíz y completa:
```env
SUPABASE_ANON_KEY=tu_anon_key_de_supabase
SUPABASE_SERVICE_KEY=tu_service_role_key_de_supabase
```

### 2. Crear tablas en Supabase

Ve a **Supabase → SQL Editor** y ejecuta el contenido de `sql/01_schema.sql`.

### 3. Arrancar el Módulo 1 (Ingestion + Airflow)

```powershell
cd C:\SUM_2025\REPROCESOS\ingestion
docker-compose up --build -d
```

Espera ~2 minutos y accede a **http://localhost:8080** (usuario: `admin`, contraseña: `admin`).

### 4. Arrancar el Módulo 2 (Backend API)

```powershell
cd C:\SUM_2025\REPROCESOS\backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API disponible en **http://localhost:8000** · Documentación en **http://localhost:8000/docs**

### 5. Arrancar el Módulo 3 (Frontend)

```powershell
cd C:\SUM_2025\REPROCESOS\frontend
npm install
npm run dev
```

App disponible en **http://localhost:5173**

---

## 👥 Roles de Usuario

| Rol | Lo que puede hacer |
|---|---|
| `control_calidad` | Ver dashboard Kanban, ficha de vehículos, crear reprocesos, gestionar usuarios |
| `operario_pintura` | Ver reprocesos pendientes de PINTURA, iniciar/cerrar trabajos con foto |
| `operario_repuesto` | Ver reprocesos pendientes de REPUESTO, iniciar/cerrar trabajos con foto |

**Usuario inicial:** `admin` / `admin123` (cambiar en primer login)

---

## 🔄 Cómo funciona la sincronización

El DAG de Airflow descarga los 3 reportes de eSUM **cada 10 minutos**:

```
eSUM (usuario: 72413102)
  │
  ├── ReporteFlujoTrabajoUbicacionAuto.php → CSV → tabla vehiculos (UPSERT)
  ├── ReportePintura.php (mes actual)      → HTML → tabla danos_pintura (DELETE + INSERT)
  └── ListaReportesRepuestosGen.php        → HTML → tabla danos_repuesto (DELETE + INSERT)
```

Puedes monitorear el estado en **http://localhost:8080** (Airflow UI).

---

## 📸 Fotos

Las fotos se convierten automáticamente a **WebP (calidad 75%)** en el servidor, reduciendo el tamaño en ~70%. Se almacenan en Google Drive (a configurar en el Módulo de fotos).

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Scheduler | Apache Airflow 2.9 |
| Contenedores | Docker + Docker Compose |
| Base de datos | Supabase (PostgreSQL 15) |
| Backend | FastAPI 0.111 + Python 3.11 |
| Autenticación | JWT (python-jose) + bcrypt |
| Frontend | React 18 + Vite + TailwindCSS |
| Fotos | Pillow + Google Drive API |

---

## 📞 Soporte

Para dudas sobre la configuración, revisar los logs de Airflow en **http://localhost:8080**.
