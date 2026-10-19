import copy
import csv
import io
from datetime import date

import pytest

from app.models.kardex import LoteCarga, MovimientoKardex
from app.services.reglas_historicas import evaluar, filtrar
from test_kardex import activos_prueba, auth_headers, crear_movimiento


def fila(id, **cambios):
    return {'id': id, 'articulo_id': 1, 'articulo': 'Libro', 'codigo': 'LIB-1',
            'lote_id': 1, 'numero_pagina': 1, 'orden_fila': id,
            'fecha': '2025-01-01', 'gestion': 2025, 'fecha_estado': 'SIN_ALERTA',
            'ingresos': 1, 'salidas': None, 'saldo_vigente': id, 'detalle': f'Fila {id}',
            'nodo': 'Ventas', 'referencia': None, **cambios}


def codigos(f):
    return {a['codigo'] for a in f['avisos']}


def test_gestion_conserva_saldo_del_anio_anterior_y_no_cambia_la_fuente():
    source = [fila(1, fecha='2024-12-31', gestion=2024, ingresos=100, saldo_vigente=100),
              fila(2, ingresos=None, salidas=80, saldo_vigente=20)]
    copia = copy.deepcopy(source)
    r = filtrar(evaluar(source), gestion=2025, seleccion='todos')
    assert r[0]['saldo_previo'] == 100
    assert r[0]['saldo_esperado_reglas'] == 20
    assert codigos(r[0]) == {'SALIDA_MAYORITARIA'}
    assert source == copia


def test_distingue_correccion_vigente_de_error_documental_conservado():
    r = evaluar([fila(1, ingresos=100, saldo_vigente=100),
                 fila(2, ingresos=None, salidas=10, saldo_vigente=90,
                      revision_documental={'saldo_documental': 99, 'origen_saldo': 'RECONSTRUIDO'})])
    assert codigos(r[1]) == {'DESCUADRE_DOCUMENTAL'}
    assert r[1]['saldo_esperado_reglas'] == 90
    r = evaluar([fila(1, ingresos=100, saldo_vigente=100),
                 fila(2, ingresos=None, salidas=10, saldo_vigente=91)])
    assert codigos(r[1]) == {'SALDO_INCONSISTENTE'}


@pytest.mark.parametrize('saldo,salida,codigo', [(50, 50, 'AGOTA_STOCK'), (50, 60, 'SALIDA_SUPERA_SALDO')])
def test_salida_total_o_imposible_se_senala_sin_bloquear_la_consulta(saldo, salida, codigo):
    r = evaluar([fila(1, ingresos=saldo, saldo_vigente=saldo),
                 fila(2, ingresos=None, salidas=salida, saldo_vigente=saldo-salida)])
    assert codigo in codigos(r[1])


@pytest.mark.parametrize('revision,error', [({'origen_saldo': 'HIPOTESIS'}, False), ({}, True)])
def test_saldo_previo_dudoso_no_inventa_alerta_de_retiro(revision, error):
    r = evaluar([fila(1, ingresos=10, saldo_vigente=10, revision_documental=revision, error_saldo=error),
                 fila(2, ingresos=None, salidas=10, saldo_vigente=0)])
    assert not r[1]['base_utilizable']
    assert not codigos(r[1])
    assert r[1]['saldo_esperado_reglas'] is None


def test_primera_salida_sin_base_y_base_hipotetica_son_no_evaluables():
    r = evaluar([fila(1, ingresos=None, salidas=10, saldo_vigente=0)])
    assert not r[0]['base_utilizable'] and 'AGOTA_STOCK' not in codigos(r[0])


def test_cantidad_hipotetica_no_genera_extremos_ni_contamina_comparables():
    source=[*[fila(i) for i in range(1,6)],
            fila(6,ingresos=1000,saldo_vigente=1005,revision_documental={'origen_cantidades':'HIPOTESIS'}),
            fila(7,ingresos=None,salidas=1005,saldo_vigente=0),fila(8,ingresos=1,saldo_vigente=1)]
    r=evaluar(source)
    assert not r[5]['base_utilizable'] and not codigos(r[5])
    assert any('CANTIDAD_EXTREMA' in n['reglas'] for n in r[5]['no_evaluables'])
    assert not r[6]['base_utilizable'] and 'AGOTA_STOCK' not in codigos(r[6])
    assert r[7]['comparables_previos']==5 and r[7]['mediana_previa']==1


def test_no_encadena_lotes_por_su_id_y_admite_base_documental_explicita():
    source = [fila(1, ingresos=10, saldo_vigente=10),
              fila(2, lote_id=2, ingresos=None, salidas=10, saldo_vigente=0)]
    r = evaluar(source)
    assert not r[1]['base_utilizable'] and 'AGOTA_STOCK' not in codigos(r[1])
    source[1]['revision_documental'] = {'saldo_base':10,'origen_saldo_base':'DOCUMENTO'}
    r = evaluar(source)
    assert r[1]['base_utilizable'] and 'AGOTA_STOCK' in codigos(r[1])
    r = evaluar([fila(1, ingresos=None, salidas=10, saldo_vigente=0,
                      revision_documental={'saldo_base': 10, 'origen_saldo_base': 'HIPOTESIS'})])
    assert not r[0]['base_utilizable'] and 'AGOTA_STOCK' not in codigos(r[0])


def test_recuento_documental_y_ajuste_no_se_inventan_como_salidas():
    r = evaluar([fila(1, ingresos=21, saldo_vigente=21),
                 fila(2, ingresos=None, saldo_vigente=3,
                      revision_documental={'tipo_fila': 'RECUENTO', 'diferencia_con_cadena_previa': -18}),
                 fila(3, ingresos=None, salidas=2, saldo_vigente=1)])
    assert codigos(r[1]) == {'CAMBIO_BASE_DOCUMENTAL'}
    assert r[2]['saldo_esperado_reglas'] == 1
    r = evaluar([fila(1, ingresos=9, saldo_vigente=9),
                 fila(2, ingresos=8, saldo_vigente=14, revision_documental={'ajuste_disponibilidad': -3})])
    assert 'SALDO_INCONSISTENTE' not in codigos(r[1])


def test_extrema_independiente_de_base_y_comparacion_solo_con_antecedentes():
    r = evaluar([fila(1, ingresos=1000, saldo_vigente=1000)])
    assert 'CANTIDAD_EXTREMA' in codigos(r[0])
    r = evaluar([*[fila(i) for i in range(1, 6)], fila(6, ingresos=30, saldo_vigente=35),
                 fila(7, ingresos=1000, saldo_vigente=1035)])
    assert r[5]['mediana_previa'] == 1 and r[5]['comparables_previos'] == 5
    assert 'CANTIDAD_ATIPICA' in codigos(r[5])
    assert r[4]['mediana_previa'] is None


def test_cantidades_ambiguas_y_posiciones_repetidas_no_alimentan_comparaciones():
    r = evaluar([fila(1, ingresos=-1), fila(2, ingresos=2, salidas=1),
                 fila(3, orden_fila=4), fila(4)])
    assert 'CANTIDADES_INVALIDAS' in codigos(r[0])
    assert 'CANTIDADES_INVALIDAS' in codigos(r[1])
    assert 'POSICION_REPETIDA' in codigos(r[2])
    assert not r[3]['base_utilizable']


def test_repeticiones_no_mezclan_articulos_ni_fechas_estimadas():
    a = fila(1, detalle='FIL', referencia='F-1', ingresos=2, saldo_vigente=2)
    b = fila(2, detalle='FIL', referencia='F-1', ingresos=2, saldo_vigente=4)
    c = fila(3, detalle='FIL', referencia='F-1', ingresos=2, articulo_id=2)
    d = fila(4, detalle='FIL', referencia='F-1', ingresos=2, fecha_estado='ESTIMADA_HIL')
    r = evaluar([a, b, c, d])
    assert 'POSIBLE_REPETICION' in codigos(r[0])
    assert next(x for x in r[0]['avisos'] if x['codigo']=='POSIBLE_REPETICION')['datos']['otros_movimientos'] == [2]
    assert 'POSIBLE_REPETICION' not in codigos(r[2])
    assert 'POSIBLE_REPETICION' not in codigos(r[3])


def test_api_filtros_csv_evidencia_y_exclusion_de_modernos_y_anulados(
    client, db_session, usuario_admin, activos_prueba,
):
    art, _ = activos_prueba
    lote = LoteCarga(total_imagenes=1, tanda=1)
    db_session.add(lote); db_session.commit()
    primero = crear_movimiento(db_session, articulo_id=art.id, lote_id=lote.id,
        fecha=date(2024, 12, 31), ingresos=100, saldo=100, numero_pagina=1, orden_fila=1)
    segundo = crear_movimiento(db_session, articulo_id=art.id, lote_id=lote.id,
        fecha=date(2025, 1, 1), salidas=80, saldo=20, numero_pagina=1, orden_fila=2)
    segundo.detalle = '=texto no confiable'
    tercero = crear_movimiento(db_session, articulo_id=art.id, lote_id=lote.id,
        fecha=date(2025, 1, 2), ingresos=1000, saldo=1020, numero_pagina=1, orden_fila=3)
    moderno = crear_movimiento(db_session, articulo_id=art.id, fecha=date(2026, 1, 1), ingresos=10000, saldo=10000)
    anulado = crear_movimiento(db_session, articulo_id=art.id, lote_id=lote.id,
        fecha=date(2025, 1, 3), ingresos=10000, saldo=10000, numero_pagina=1, orden_fila=4)
    anulado.estado='ANULADO_DOCUMENTO'; db_session.commit()
    headers = auth_headers(usuario_admin)
    url = '/api/v1/analitica/reglas-historicas'
    assert client.get(url).status_code == 401
    response = client.get(url, headers=headers, params={'gestion':2025,'limite':1}).json()
    assert response['total'] == 2
    assert response['filas'][0]['saldo_previo'] == 100
    ids = [f['id'] for f in client.get(url, headers=headers, params={'seleccion':'todos'}).json()['filas']]
    assert moderno.id not in ids and anulado.id not in ids
    filtrado = client.get(url, headers=headers, params={'gestion':2025,'regla':'SALIDA_MAYORITARIA'}).json()
    assert filtrado['total'] == 1 and filtrado['filas'][0]['id'] == segundo.id
    assert client.get(url, headers=headers, params={'regla':'INVENTADA'}).status_code == 422
    detail = client.get(f'{url}/{segundo.id}', headers=headers).json()
    assert [f['id'] for f in detail['vecinos']] == [primero.id, segundo.id, tercero.id]
    assert client.get(f'{url}/{moderno.id}', headers=headers).status_code == 404
    archivo = client.get(url+'.csv', headers=headers, params={'gestion':2025})
    rows = list(csv.DictReader(io.StringIO(archivo.text.lstrip('\ufeff')), delimiter=';'))
    assert len(rows) == 2
    assert 'SALIDA_MAYORITARIA' in rows[0]['Reglas']
    assert [f.saldo_registrado for f in (primero, segundo, tercero)] == [100,20,1020]
    assert not db_session.dirty


def test_roles_pueden_consultar_pero_no_hay_mutaciones_de_reglas(client, usuario_operador):
    headers = auth_headers(usuario_operador)
    assert client.get('/api/v1/analitica/reglas-historicas/opciones', headers=headers).status_code == 200
    assert client.post('/api/v1/analitica/reglas-historicas', headers=headers, json={}).status_code == 405
