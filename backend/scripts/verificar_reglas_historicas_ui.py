"""Activa servidores locales libres y verifica la interfaz mediante GET únicamente."""
import json
import os
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.core.security import create_access_token
from app.db.session import SessionLocal, engine
from app.models.auditoria_historica import ModeloHistorico
from app.models.rol import Rol
from app.models.usuario import Usuario
from scripts.verificar_respaldo_actual import snapshot_db


def libre(port):
    for host, family in [('127.0.0.1', socket.AF_INET), ('::1', socket.AF_INET6)]:
        with socket.socket(family) as sock:
            if sock.connect_ex((host, port)) == 0:
                return False
    return True


def main():
    backend = Path(__file__).resolve().parents[1]
    root = backend.parent
    salida = backend/'backups'/('reglas_historicas_'+datetime.now(UTC).strftime('%Y%m%dT%H%M%S'))
    salida.mkdir(parents=True, exist_ok=False)
    antes = snapshot_db(engine)
    (salida/'institucional_antes.json').write_text(json.dumps(antes), encoding='utf-8')
    with SessionLocal() as db:
        if db.query(ModeloHistorico).filter(ModeloHistorico.estado.in_(['PENDIENTE','EN_EJECUCION'])).count():
            raise RuntimeError('Hay entrenamiento en curso; no iniciar otro trabajador local.')
        admin = db.query(Usuario).join(Rol).filter(Usuario.estado=='activo',Rol.nombre=='Administrador',Rol.estado=='activo').first()
        token = create_access_token(admin.id, {'rol':'Administrador'})
    env = os.environ.copy()
    env['VITE_API_BASE_URL']='http://localhost:8000/api/v1'
    servidores = {}
    if libre(8000):
        log = (salida/'api.log').open('w', encoding='utf-8')
        proc = subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000'],
            cwd=backend,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        servidores['backend_pid']=proc.pid
    if libre(5173):
        log = (salida/'frontend.log').open('w', encoding='utf-8')
        proc = subprocess.Popen([r'C:\Program Files\nodejs\node.exe',str(root/'frontend/node_modules/vite/bin/vite.js'),
            '--host','localhost','--port','5173','--strictPort'],cwd=root/'frontend',env=env,
            stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        servidores['frontend_pid']=proc.pid
    (salida/'servidores.json').write_text(json.dumps(servidores), encoding='utf-8')
    for _ in range(120):
        try:
            if httpx.get('http://localhost:8000/health',timeout=2).status_code==200 and httpx.get('http://localhost:5173',timeout=2).status_code==200:
                break
        except httpx.RequestError:
            pass
        time.sleep(.25)
    else:
        raise RuntimeError('Los servidores no respondieron; revisar los logs del ensayo.')
    env.update(QA_ACCESS_TOKEN=token, QA_OUTPUT=str(salida),
        PLAYWRIGHT_MODULE=r'C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright')
    result = subprocess.run([r'C:\Program Files\nodejs\node.exe',str(root/'frontend/qa/reglas-historicas.cjs')],cwd=root/'frontend',env=env)
    intacta = snapshot_db(engine)==antes
    reporte={'resultado':'CORRECTO' if result.returncode==0 and intacta else 'FALLO',
        'base_institucional_intacta':intacta,'codigo_navegador':result.returncode,'carpeta':str(salida)}
    (salida/'verificacion.json').write_text(json.dumps(reporte,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(reporte,ensure_ascii=False))
    if result.returncode or not intacta:raise SystemExit(1)


if __name__=='__main__':main()
