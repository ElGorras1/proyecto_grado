# Sistema de Gestión y Trazabilidad de Activos Operativos
**Caso: Fundación Simón I. Patiño**

Estructura de entorno de desarrollo lista para el Sprint 1 (Login + RBAC + JWT).

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Vue 3 + TypeScript + Vite + Pinia + PrimeVue |
| Backend | Python + FastAPI |
| Persistencia | PostgreSQL + SQLAlchemy |
| Seguridad | Argon2 (hash) + JWT + RBAC |

## Estructura de carpetas

```
proyecto-activos/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── core/        # config.py, security.py (Argon2 + JWT)
│   │   ├── db/          # sesión SQLAlchemy
│   │   ├── models/      # ORM: rol, permiso, rol_permiso, area, usuario
│   │   ├── schemas/     # Pydantic
│   │   ├── crud/        # acceso a datos
│   │   └── api/v1/      # endpoints + deps.py (get_current_user, require_roles)
│   ├── init_db/initial_schema.sql   # tu esquema de 19 tablas
│   └── scripts/seed_admin.py        # crea el primer usuario Administrador
└── frontend/
    └── src/
        ├── router/      # guard de autenticación + RBAC
        ├── stores/auth.ts
        ├── services/api.ts   # axios + interceptor 401
        └── views/       # LoginView, DashboardView, AdminView, ForbiddenView
```

## Opción A: levantar todo con Docker (recomendado)

Requiere Docker y Docker Compose instalados.

```bash
cd proyecto-activos
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

Esto levanta:
- PostgreSQL en `localhost:5432` (ya con `initial_schema.sql` aplicado automáticamente la primera vez)
- Backend FastAPI en `http://localhost:8000` (docs en `http://localhost:8000/docs`)
- Frontend Vue en `http://localhost:5173`

Luego, crea el usuario administrador (una sola vez):

```bash
docker compose exec backend python -m scripts.seed_admin
```

Credenciales de prueba: `admin@simonpatino.test` / `CambiarPassword123!`

## Opción B: manual (sin Docker)

### 1. Base de datos
Crea la BD y usuario en tu PostgreSQL local, y aplica el esquema:

```bash
createdb activos_db
psql -d activos_db -f backend/init_db/initial_schema.sql
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # ajusta DATABASE_URL y JWT_SECRET_KEY
python -m scripts.seed_admin
uvicorn app.main:app --reload
```

Backend en `http://localhost:8000`, documentación interactiva en `/docs`.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend en `http://localhost:5173`.

## Verificación de RBAC (Sprint 1)

1. Inicia sesión con el usuario Administrador → deberías ver el enlace "Ir al panel de administración".
2. Crea un usuario con rol Operador o Auditor directamente en la BD (o cuando implementes el CRUD de usuarios) e inicia sesión con él.
3. Intenta navegar manualmente a `/admin` con ese usuario → debe redirigir a `/403` (frontend) porque el rol no está permitido.
4. Llama directamente a `GET /api/v1/auth/admin/ping` con el token de ese usuario (por ejemplo desde `/docs`) → el backend debe responder **403 Forbidden**, no solo esconder el botón.
5. Llama al mismo endpoint sin token → debe responder **401 Unauthorized**.

## Calidad de código

**Backend** (Ruff + Black + PyTest, configurados en `pyproject.toml`):
```bash
cd backend
ruff check .
black .
pytest -v          # corre los tests de auth/RBAC (usan SQLite en memoria, no requieren Postgres)
```

**Frontend** (ESLint + Prettier + Vitest):
```bash
cd frontend
npm run lint
npm run format
npm run test       # corre GrafoTrazabilidad.spec.ts, ejemplo de test con Cytoscape mockeado
```

## Migraciones de esquema (Alembic)

Tu BD ya existe (creada con `initial_schema.sql`). Para que Alembic no intente
"deshacer" ese esquema la primera vez, márcalo como punto de partida:

```bash
cd backend
alembic stamp head
```

De ahí en adelante, cada cambio de esquema (por ejemplo cuando definan
"devoluciones, ajustes y bajas" en el módulo de Kardex) se hace así:

```bash
alembic revision --autogenerate -m "agrega tabla X"
alembic upgrade head
```

## Control de versiones (Git)

Si el repositorio aún no existe:

```bash
cd proyecto-activos
git init
git add .
git commit -m "Entorno de desarrollo inicial: backend + frontend + BD"
```

Sugerencia de ramas simple para el trabajo por sprints:
- `main`: siempre desplegable/estable.
- `develop`: integración de los sprints en curso.
- `feature/sprint1-login-rbac`, `feature/sprint2-activos`, etc.: una rama por tarea del cronograma.

## Extensiones recomendadas (VS Code)

Están en `.vscode/extensions.json` — VS Code te ofrecerá instalarlas automáticamente al abrir la carpeta.



- Sprint 1 (actual): CRUD de usuarios y áreas + reportes de acceso (tabla `auditoria_sistema`, ya en el esquema).
- Sprint 2: CRUD de artículos/activos y existencias.
- Sprint 3: Registro de movimientos (entradas, salidas, transferencias) y Kardex digital.
- Sprint 4: Trazabilidad, grafos (NetworkX) y visualización (Cytoscape.js).
- Sprint 5: Alertas, Isolation Forest y gestión de casos de auditoría.

Genera una clave segura para `JWT_SECRET_KEY` con:
```bash
openssl rand -hex 32
```
