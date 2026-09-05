"""
Instancia compartida del rate limiter (slowapi).

Se mantiene en un módulo separado para evitar importaciones circulares
entre app.main y los endpoints que necesitan decorar funciones con
@limiter.limit(...).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
