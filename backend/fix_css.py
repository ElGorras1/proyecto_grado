import os

filepath = r"c:\Users\LENOVO\Desktop\proyecto-activos-scaffold\proyecto-activos\frontend\src\views\InventarioActualView.vue"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

styles_to_insert = """
.fila-anulada { opacity: 0.6; background-color: #fee2e2 !important; text-decoration: line-through; }
.fila-anulada td.saldo { background: transparent; text-decoration: none; }
.badge-anulado { font-size: 0.7rem; background: #dc2626; color: white; padding: 2px 6px; border-radius: 4px; margin-left: 8px; vertical-align: middle;}
.btn-icon { background: none; border: none; cursor: pointer; font-size: 1.1rem; padding: 0.2rem; filter: grayscale(100%); transition: filter 0.2s; }
.btn-icon:hover { filter: grayscale(0%); }
"""

if ".fila-anulada" not in content:
    content = content.replace("</style>", styles_to_insert + "\n</style>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("CSS updated")
else:
    print("CSS already there")
