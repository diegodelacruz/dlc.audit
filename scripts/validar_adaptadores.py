"""Verifica que cada adaptador de plataforma coincida byte a byte con su origen en skills/.

Uso:
    python -I scripts/validar_adaptadores.py              # solo verifica
    python -I scripts/validar_adaptadores.py --regenerar  # copia el origen a cada adaptador

Solo usa la biblioteca estándar. Devuelve 0 si todo está sincronizado y 1 si no.
"""

import hashlib
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "skills"

# Ruta del adaptador dentro de plataformas/<plataforma>/. {nombre} es la carpeta de la skill.
ADAPTADORES = {
    "claude": "skills/{nombre}/SKILL.md",
    "chatgpt": "skills/{nombre}/SKILL.md",
    "antigravity": ".agents/skills/{nombre}/SKILL.md",
}


def _sha256(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def skills_origen(origen=ORIGEN):
    """Nombres de las skills del origen: carpetas que contienen SKILL.md."""
    return sorted(p.parent.name for p in origen.glob("*/SKILL.md"))


def verificar(raiz=RAIZ, regenerar=False):
    """Devuelve la lista de problemas. Con regenerar=True, primero copia el origen a los adaptadores."""
    origen = raiz / "skills"
    plataformas = raiz / "plataformas"
    problemas = []
    nombres = skills_origen(origen)
    if not nombres:
        return [f"no hay skills en {origen}"]

    for nombre in nombres:
        ruta_origen = origen / nombre / "SKILL.md"
        for plataforma, patron in ADAPTADORES.items():
            ruta_adaptador = plataformas / plataforma / patron.format(nombre=nombre)
            if regenerar:
                ruta_adaptador.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ruta_origen, ruta_adaptador)
                continue
            if not ruta_adaptador.exists():
                problemas.append(f"falta el adaptador {plataforma} de la skill '{nombre}': {ruta_adaptador}")
            elif _sha256(ruta_adaptador) != _sha256(ruta_origen):
                problemas.append(f"el adaptador {plataforma} de '{nombre}' no coincide con el origen")

    if not regenerar:
        for plataforma in ADAPTADORES:
            carpeta = plataformas / plataforma
            if not carpeta.exists():
                problemas.append(f"falta la carpeta de plataforma: {carpeta}")
                continue
            for skill_md in carpeta.rglob("SKILL.md"):
                nombre = skill_md.parent.name
                if nombre not in nombres:
                    problemas.append(f"adaptador {plataforma} sin origen en skills/: '{nombre}'")

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
