"""Isolation Forest retrospectivo. Todo ajuste utiliza únicamente entrenamiento."""

import sys
from collections import Counter, defaultdict

import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest

from app.services.datos_analitica import huella

VARIABLES = [
    "log_cantidad",
    "log_relacion_mediana",
    "desviacion_robusta",
    "rareza_nodo",
    "rareza_articulo_nodo",
    "sin_nodo_documental",
    "es_salida",
]


def cantidad(f):
    return (f["ingresos"] or 0) + (f["salidas"] or 0)


def direccion(f):
    return "ingreso" if (f["ingresos"] or 0) > 0 else "salida"


def particionar(filas, semilla):
    # Lotes indivisibles; duplicados exactos entre lotes se mantienen juntos.
    padres = {f["lote_id"]: f["lote_id"] for f in filas}

    def raiz(x):
        while padres[x] != x:
            padres[x] = padres[padres[x]]
            x = padres[x]
        return x

    firmas = {}
    for f in filas:
        firma = huella(
            {
                k: f[k]
                for k in (
                    "articulo_id",
                    "fecha",
                    "detalle",
                    "referencia",
                    "area",
                    "ingresos",
                    "salidas",
                    "saldo_registrado",
                )
            }
        )
        anterior = firmas.setdefault(firma, f["lote_id"])
        padres[raiz(f["lote_id"])] = raiz(anterior)
    grupos = sorted({raiz(f["lote_id"]) for f in filas})
    if len(grupos) < 5:
        raise ValueError(
            "Datos insuficientes: se necesitan al menos cinco grupos de lotes independientes."
        )
    rng = np.random.default_rng(semilla)
    rng.shuffle(grupos)
    n = max(1, int(len(grupos) * 0.2))
    calibracion, evaluacion = set(grupos[:n]), set(grupos[n : 2 * n])
    partes = [
        (
            "calibracion"
            if raiz(f["lote_id"]) in calibracion
            else "evaluacion" if raiz(f["lote_id"]) in evaluacion else "entrenamiento"
        )
        for f in filas
    ]
    cuentas = Counter(partes)
    if cuentas["entrenamiento"] < 50 or cuentas["calibracion"] < 20 or cuentas["evaluacion"] < 20:
        raise ValueError(
            "Datos insuficientes tras agrupar lotes: mínimo 50 de "
            "entrenamiento, 20 de calibración y 20 de evaluación."
        )
    return partes


class Contexto:
    def fit(self, filas):
        self.cantidades = defaultdict(list)
        self.globales = defaultdict(list)
        self.nodos = Counter()
        self.pares = Counter()
        self.totales = Counter()
        self.total = len(filas)
        for f in filas:
            clave = (f["articulo_id"], direccion(f))
            self.cantidades[clave].append(cantidad(f))
            self.globales[direccion(f)].append(cantidad(f))
            self.nodos[f["nodo_grafo"]] += 1
            self.pares[(clave, f["nodo_grafo"])] += 1
            self.totales[clave] += 1
        self.estadisticas = {k: self._stats(v) for k, v in self.cantidades.items()}
        self.respaldo = {k: self._stats(v) for k, v in self.globales.items()}
        return self

    @staticmethod
    def _stats(valores):
        mediana = float(np.median(valores))
        return mediana, max(1.0, float(np.median(np.abs(np.asarray(valores) - mediana))))

    def transformar(self, filas):
        matriz, contextos = [], []
        for f in filas:
            clave = (f["articulo_id"], direccion(f))
            n = self.totales[clave]
            mediana, mad = self.estadisticas.get(clave, self.respaldo.get(direccion(f), (1.0, 1.0)))
            valor = cantidad(f)
            fn = (self.nodos[f["nodo_grafo"]] + 1) / (self.total + len(self.nodos) + 1)
            fp = (self.pares[(clave, f["nodo_grafo"])] + 1) / (n + len(self.nodos) + 1)
            ausente = not f["nodo_grafo"] or f["nodo_grafo"] in (
                "Origen no especificado",
                "Destino no especificado",
            )
            matriz.append(
                [
                    np.log1p(valor),
                    np.log((valor + 1) / (mediana + 1)),
                    np.log1p(abs(valor - mediana) / mad),
                    -np.log(fn),
                    -np.log(fp),
                    int(ausente),
                    int(direccion(f) == "salida"),
                ]
            )
            indicadores = []
            if n and valor > mediana * 3:
                indicadores.append("Cantidad mayor a tres veces la mediana de referencia")
            if self.nodos[f["nodo_grafo"]] == 0:
                indicadores.append("Nodo no observado en entrenamiento")
            if n == 0:
                indicadores.append("Artículo/dirección sin referencia propia; comparación global")
            if ausente:
                indicadores.append("Ausencia documental de nodo; no implica irregularidad")
            contextos.append(
                {
                    "cantidad": valor,
                    "direccion": direccion(f),
                    "mediana": mediana,
                    "referencias": n,
                    "frecuencia_nodo": fn,
                    "indicadores": indicadores,
                    "regla_magnitud": bool(n and valor > mediana * 3),
                    "score_regla": float(valor / max(mediana, 1)) if n else 0.0,
                }
            )
        return np.asarray(matriz), contextos


def calcular(filas, config, partes=None):
    if partes is None:
        if config.get('modo') == 'POR_ARTICULO':
            from app.services.particiones_articulo import particionar_por_articulo
            partes = particionar_por_articulo(filas, config['semilla'])
        else:
            partes = particionar(filas, config['semilla'])
    cuentas = Counter(partes)
    if len(partes) != len(filas) or set(partes) - {"entrenamiento", "calibracion", "evaluacion"}:
        raise ValueError("La asignación de particiones es inválida.")
    if cuentas["entrenamiento"] < 50 or cuentas["calibracion"] < 20 or cuentas["evaluacion"] < 20:
        raise ValueError("Datos insuficientes: mínimo 50 de entrenamiento, 20 de calibración y 20 de evaluación.")
    train = [f for f, p in zip(filas, partes) if p == "entrenamiento"]
    contexto = Contexto().fit(train)
    x, explicaciones = contexto.transformar(filas)
    indices = {
        p: np.array([i for i, q in enumerate(partes) if p == q])
        for p in ("entrenamiento", "calibracion", "evaluacion")
    }
    parametros = dict(
        n_estimators=config["arboles"],
        max_samples=min(256, len(train)),
        contamination="auto",
        n_jobs=1,
    )
    modelo = IsolationForest(random_state=config["semilla"], **parametros).fit(
        x[indices["entrenamiento"]]
    )
    if np.unique(x[indices["entrenamiento"]], axis=0).shape[0] < 2:
        raise ValueError("Datos insuficientes: las variables de entrenamiento no tienen variación.")
    scores = -modelo.score_samples(x)  # Mayor puntuación = mayor rareza; no probabilidad.
    umbral = float(
        np.quantile(scores[indices["calibracion"]], 1 - config["porcentaje_revision"] / 100)
    )
    alertas = scores > umbral
    evaluacion = indices["evaluacion"]
    k = min(20, len(evaluacion))

    def top(valores):
        return set(
            sorted(evaluacion.tolist(), key=lambda i: (-float(valores[i]), filas[i]["id"]))[:k]
        )

    primero = top(scores)
    estable = []
    for seed in (config["semilla"] + 1, config["semilla"] + 2):
        otro = IsolationForest(random_state=seed, **parametros).fit(x[indices["entrenamiento"]])
        t = top(-otro.score_samples(x))
        estable.append(len(primero & t) / len(primero | t))
    reglas = top([c["score_regla"] for c in explicaciones])
    controles = [int(i) for i in evaluacion if not alertas[i]]
    np.random.default_rng(config["semilla"]).shuffle(controles)
    control_ids = set(controles[:20])
    metricas = {
        "modo": config.get("modo", "RETROSPECTIVO"),
        "particiones": {p: len(v) for p, v in indices.items()},
        "estrategia": (
            "Lotes agrupados; duplicados exactos unidos; 60/20/20 aproximado. "
            "Auditoría retrospectiva."
        ),
        "variables": VARIABLES,
        "version_variables": 1,
        "dependencias": {
            "python": sys.version.split()[0],
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
        },
        "k": k,
        "top_evaluacion": [
            filas[i]["id"] for i in sorted(primero, key=lambda i: (-scores[i], filas[i]["id"]))
        ],
        "top_regla": [
            filas[i]["id"]
            for i in sorted(
                reglas, key=lambda i: (-explicaciones[i]["score_regla"], filas[i]["id"])
            )
        ],
        "jaccard_top_entre_semillas": estable,
        "solapamiento_top_regla": len(primero & reglas) / k,
        "alertas": int(alertas.sum()),
        "muestra_control": len(control_ids),
        "sin_referencia_propia_evaluacion": sum(
            explicaciones[i]["referencias"] == 0 for i in evaluacion
        ),
        "precision_at_k": None,
        "evaluacion_humana": "Pendiente. Estabilidad y solapamiento no miden precisión ni fraude.",
        "umbral": (
            "Cuantil de calibración según capacidad de revisión; provisional "
            "hasta revisión humana."
        ),
    }
    if config.get("modo") == "TEMPORAL":
        metricas["gestion_evaluacion"] = config["gestion_evaluacion"]
        metricas["estrategia"] = (
            "Comparación cronológica; entrenamiento anterior a calibración; "
            "año posterior reservado. Lotes indivisibles y duplicados agrupados; "
            "grupos que cruzan fronteras excluidos."
        )
    if config.get('modo') == 'POR_ARTICULO':
        from app.services.particiones_articulo import auditar_particiones
        control = auditar_particiones(filas, partes)
        if not control['sin_cruces']:
            raise ValueError('La separación por artículo conserva relaciones entre particiones.')
        metricas['estrategia'] = 'Componentes indivisibles de artículo, lote y fotografía; grupos 60/20/20 aproximados. Evaluación de artículos no vistos; no es validación prospectiva.'
        metricas['control_por_articulo'] = control
    resultados = [
        dict(
            snapshot=f,
            score=float(scores[i]),
            alerta=bool(alertas[i]),
            particion=partes[i],
            muestra_control=i in control_ids,
            contexto=explicaciones[i],
        )
        for i, f in enumerate(filas)
    ]
    return modelo, contexto, umbral, metricas, resultados
