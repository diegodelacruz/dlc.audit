"""Verifica que cada adaptador de plataforma coincida, archivo por archivo, con su skill en skills/.

Cada skill es una carpeta completa (SKILL.md y references/). Un adaptador debe contener exactamente
los mismos archivos, con el mismo contenido, para que la skill instalada sea autocontenida.

Uso:
    python -I scripts/validar_adaptadores.py              # solo verifica
    python -I scripts/validar_adaptadores.py --regenerar  # copia cada skill completa a los adaptadores

Solo usa la biblioteca estándar. Devuelve 0 si todo está sincronizado y 1 si no.
"""

import hashlib
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Carpeta base de las skills dentro de plataformas/<plataforma>/.
ADAPTADORES = {
    "claude": "skills",
    "chatgpt": "skills",
    "antigravity": ".agents/skills",
}


def _sha256(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def skills_origen(origen):
    """Nombres de las skills del origen: carpetas que contienen SKILL.md."""
    return sorted(p.parent.name for p in origen.glob("*/SKILL.md"))


def _archivos(carpeta):
    """Rutas relativas de todos los archivos de una carpeta de skill."""
    return {p.relative_to(carpeta) for p in carpeta.rglob("*") if p.is_file()}


def verificar(raiz=RAIZ, regenerar=False):
    """Devuelve la lista de problemas. Con regenerar=True, copia primero cada skill a sus adaptadores."""
    origen = raiz / "skills"
    plataformas = raiz / "plataformas"
    problemas = []
    nombres = skills_origen(origen)
    if not nombres:
        return [f"no hay skills en {origen}"]

    for nombre in nombres:
        carpeta_origen = origen / nombre
        for plataforma, base in ADAPTADORES.items():
            carpeta_adaptador = plataformas / plataforma / base / nombre
            if regenerar:
                if carpeta_adaptador.exists():
                    shutil.rmtree(carpeta_adaptador)
                shutil.copytree(carpeta_origen, carpeta_adaptador)
                continue
            if not carpeta_adaptador.exists():
                problemas.append(f"falta el adaptador {plataforma} de la skill '{nombre}': {carpeta_adaptador}")
                continue
            esperados = _archivos(carpeta_origen)
            reales = _archivos(carpeta_adaptador)
            for rel in sorted(esperados - reales):
                problemas.append(f"falta en el adaptador {plataforma} de '{nombre}': {rel}")
            for rel in sorted(reales - esperados):
                problemas.append(f"sobra en el adaptador {plataforma} de '{nombre}': {rel}")
            for rel in sorted(esperados & reales):
                if _sha256(carpeta_adaptador / rel) != _sha256(carpeta_origen / rel):
                    problemas.append(f"el archivo {rel} del adaptador {plataforma} de '{nombre}' no coincide con el origen")

    if not regenerar:
        for plataforma, base in ADAPTADORES.items():
            carpeta_base = plataformas / plataforma / base
            if not carpeta_base.exists():
                continue
            for carpeta in sorted(carpeta_base.iterdir()):
                if carpeta.is_dir() and carpeta.name not in nombres:
                    problemas.append(f"adaptador {plataforma} sin origen en skills/: '{carpeta.name}'")

    return problemas


def main(argumentos):
    regenerar = "--regenerar" in argumentos
    problemas = verificar(regenerar=regenerar)
    if regenerar:
        print("Adaptadores regenerados desde skills/")
        return 0
    if problemas:
        for p in problemas:
            print(f"ERROR: {p}")
        return 1
    print("OK: adaptadores sincronizados con skills/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
