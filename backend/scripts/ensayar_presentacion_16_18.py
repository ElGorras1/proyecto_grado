"""Ensayo en PostgreSQL clonado y navegador; conserva la base institucional."""
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from jose import jwt
from sqlalchemy import create_engine, text

from app.db.session import engine, SessionLocal
from app.models.usuario import Usuario
from app.models.rol import Rol
from scripts.verificar_respaldo_actual import snapshot_db

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent


def main():
    for port in (8018, 5188):
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError(f'Puerto {port} ocupado; no sustituir otro servidor.')
    marca = datetime.now(UTC).strftime('%Y%m%dT%H%M%S').lower()
    nombre = 'activos_presentacion_qa_' + marca
    salida = BACKEND / 'backups' / ('presentacion_16_18_' + marca)
    salida.mkdir(parents=True, exist_ok=False)
    original = snapshot_db(engine)
    (salida / 'institucional_antes.json').write_text(json.dumps(original), encoding='utf-8')
    with SessionLocal() as db:
        admin_usuario = db.query(Usuario).join(Rol).filter(
            Usuario.estado == 'activo', Rol.nombre == 'Administrador', Rol.estado == 'activo').first()
        if admin_usuario is None:
            raise RuntimeError('No hay administrador activo para el ensayo local.')
        usuario_id = admin_usuario.id
    url = engine.url
    pg_bin = Path(os.environ.get('POSTGRES_BIN', r'C:\Program Files\PostgreSQL\18\bin'))
    conexion = ['-h', url.host or 'localhost', '-p', str(url.port or 5432), '-U', url.username or 'postgres']
    pg_env = os.environ.copy()
    if url.password:
        pg_env['PGPASSWORD'] = url.password
    dump = salida / 'base.dump'
    subprocess.run([str(pg_bin / 'pg_dump.exe'), *conexion, '-Fc', '-f', str(dump), url.database],
                   env=pg_env, check=True, stdout=subprocess.DEVNULL)
    admin_engine = create_engine(url.set(database='postgres'), isolation_level='AUTOCOMMIT')
    with admin_engine.connect() as db:
        db.execute(text(f'CREATE DATABASE "{nombre}"'))
        db.execute(text(f'COMMENT ON DATABASE "{nombre}" IS :marca'),
                   {'marca': 'ENSAYO AISLADO TAREAS 16-18; datos copiados, operaciones ficticias.'})
    admin_engine.dispose()
    subprocess.run([str(pg_bin / 'pg_restore.exe'), *conexion, '--exit-on-error', '-d', nombre, str(dump)],
                   env=pg_env, check=True, stdout=subprocess.DEVNULL)
    if snapshot_db(engine) != original:
        raise RuntimeError('La base institucional cambió durante la copia.')
    env = os.environ.copy()
    clave_qa = secrets.token_urlsafe(48)
    env.update(DATABASE_URL=url.set(database=nombre).render_as_string(hide_password=False),
               JWT_SECRET_KEY=clave_qa, GEMINI_API_KEY='',
               BACKEND_CORS_ORIGINS=json.dumps(['http://127.0.0.1:5188']),
               VITE_API_BASE_URL='http://127.0.0.1:8018/api/v1')
    node = r'C:\Program Files\nodejs\node.exe'
    backend_log = (salida / 'api.log').open('w', encoding='utf-8')
    frontend_log = (salida / 'frontend.log').open('w', encoding='utf-8')
    # --lifespan off evita iniciar entrenamiento automático en la copia de ensayo.
    api = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                            '--port', '8018', '--lifespan', 'off'], cwd=BACKEND, env=env,
                           stdout=backend_log, stderr=subprocess.STDOUT,
                           creationflags=subprocess.CREATE_NO_WINDOW)
    web = subprocess.Popen([node, str(ROOT / 'frontend/node_modules/vite/bin/vite.js'),
                            '--host', '127.0.0.1', '--port', '5188', '--strictPort'],
                           cwd=ROOT / 'frontend', env=env, stdout=frontend_log, stderr=subprocess.STDOUT,
                           creationflags=subprocess.CREATE_NO_WINDOW)
    (salida / 'servidores.json').write_text(json.dumps({
        'base_qa': nombre, 'backend_pid': api.pid, 'frontend_pid': web.pid,
        'url_ensayo': 'http://127.0.0.1:5188', 'solo_datos_de_ensayo': True}, indent=2), encoding='utf-8')
    for _ in range(80):
        if api.poll() is not None or web.poll() is not None:
            raise RuntimeError('Un servidor de ensayo terminó; revisar sus logs.')
        try:
            if httpx.get('http://127.0.0.1:8018/health', timeout=2).status_code == 200 and httpx.get(
                    'http://127.0.0.1:5188', timeout=2).status_code == 200:
                break
        except httpx.RequestError:
            pass
        time.sleep(.25)
    else:
        raise RuntimeError('Los servidores no quedaron disponibles.')
    env.update(QA_ACCESS_TOKEN=jwt.encode({'sub': str(usuario_id), 'rol': 'Administrador',
               'exp': datetime.now(UTC) + timedelta(hours=2)}, clave_qa, algorithm='HS256'),
               QA_OUTPUT=str(salida),
               PLAYWRIGHT_MODULE=r'C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright')
    ensayo = subprocess.run([node, str(ROOT / 'frontend/qa/presentacion16-18.cjs')],
                            env=env, cwd=ROOT / 'frontend', check=False)
    intacta = snapshot_db(engine) == original
    reporte = {'base_institucional_intacta': intacta, 'codigo_salida_navegador': ensayo.returncode,
               'base_qa': nombre, 'carpeta': str(salida), 'url_ensayo': 'http://127.0.0.1:5188',
               'limite': 'Operaciones ficticias; no acreditan una transacción institucional real.'}
    (salida / 'verificacion.json').write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(reporte, ensure_ascii=False))
    if ensayo.returncode or not intacta:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
