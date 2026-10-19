"""Valida un informe de auditoría según docs/formato-informe.md (formato 1.0).

Uso:
    python -I scripts/validar_informe.py <ruta-al-informe.md> [...]

Solo usa la biblioteca estándar. Devuelve 0 si todos los informes son válidos y 1 si alguno no lo es.
"""

import re
import sys
from pathlib import Path

CAMPOS_OBLIGATORIOS = [
    "id",
    "repositorio",
    "rama",
    "commit_auditado",
    "fecha_utc",
    "auditor",
    "alcance",
    "auditoria_previa",
    "veredicto",
    "conteo_hallazgos",
]
CAMPOS_AUDITOR = ["repositorio", "commit_auditor", "version_criterios", "agente", "plataforma_ejecucion"]
CAMPOS_CONTEO = ["critico", "alto", "medio", "bajo", "informativo"]

VEREDICTOS = {"PASS", "PASS_WITH_NA", "FAIL"}
PLATAFORMAS = {"ChatGPT", "Claude", "Antigravity"}
ESTADOS_HALLAZGO = {"NUEVO", "ABIERTO", "CERRADO", "SIN_CAMBIO"}
RESULTADOS_CONTROL = {"PASS", "FAIL", "N/A", "NO_EJECUTADO"}
ESTADOS_PROVEEDOR = {"CUMPLE", "NO_CUMPLE", "NO_APLICA", "NO_VERIFICADO"}

SECCIONES = [
    "Resumen",
    "Entradas leídas",
    "Comandos ejecutados",
    "Controles",
    "Cumplimiento por proveedor",
    "Hallazgos",
    "Contradicciones",
    "Seguimiento",
    "Limitaciones",
]

RE_ID = re.compile(r"^AUD-\d{4}-\d{2}-\d{2}-\d{3}$")
RE_SHA = re.compile(r"^[0-9a-f]{40}$")
RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
RE_HALLAZGO = re.compile(r"^HALL-([a-z]+(?:-[a-z]+)*)-([0-9a-f]{6,12})$")
RE_NOMBRE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
RE_ENCABEZADO = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)


class ErrorFormato(Exception):
    pass


def _limpiar(valor):
    valor = re.sub(r"\s+#.*$", "", valor).strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        valor = valor[1:-1]
    if valor == "null":
        return None
    return valor


def parsear_frontmatter(texto):
    """Lee el subconjunto de YAML usado por el formato: pares clave-valor y un nivel de mapa anidado."""
    lineas = texto.splitlines()
    if not lineas or lineas[0].strip() != "---":
        raise ErrorFormato("el informe no empieza con un bloque YAML delimitado por ---")
    try:
        fin = lineas.index("---", 1)
    except ValueError:
        raise ErrorFormato("el bloque YAML no se cierra con ---")

    datos = {}
    anidado = None
    for linea in lineas[1:fin]:
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        if linea.startswith("  "):
            if anidado is None:
                raise ErrorFormato(f"sangría sin mapa padre: {linea.strip()!r}")
            clave, _, valor = linea.strip().partition(":")
            datos[anidado][clave.strip()] = _limpiar(valor)
            continue
        clave, _, valor = linea.partition(":")
        clave = clave.strip()
        valor = _limpiar(valor)
        if valor == "" and clave in ("auditor", "conteo_hallazgos"):
            datos[clave] = {}
            anidado = clave
        else:
            datos[clave] = valor
            anidado = None
    return datos, lineas[fin + 1 :]


def _secciones(cuerpo):
    """Devuelve la lista (número, nombre, texto) de cada sección de nivel 2 del cuerpo."""
    texto = "\n".join(cuerpo)
    encabezados = list(RE_ENCABEZADO.finditer(texto))
    secciones = []
    for i, m in enumerate(encabezados):
        fin = encabezados[i + 1].start() if i + 1 < len(encabezados) else len(texto)
        secciones.append((int(m.group(1)), m.group(2).strip(), texto[m.end() : fin]))
    return secciones


def _filas_tabla(texto):
    """Filas de datos de una tabla markdown, sin cabecera ni separador."""
    filas = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea.startswith("|"):
            continue
        celdas = [c.strip() for c in linea.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in celdas if c):
            continue
        filas.append(celdas)
    return filas[1:] if filas else []


def _bloques_hallazgo(texto):
    bloques = []
    partes = re.split(r"^### ", texto, flags=re.MULTILINE)
    for parte in partes[1:]:
        encabezado, _, cuerpo = parte.partition("\n")
        campos = {}
        for m in re.finditer(r"^- \*\*(.+?):\*\*\s*(.*)$", cuerpo, flags=re.MULTILINE):
            campos[m.group(1).strip()] = m.group(2).strip()
        bloques.append((encabezado.strip(), campos))
    return bloques


def validar_texto(texto, nombre_archivo=None):
    """Devuelve la lista de errores del informe. Lista vacía significa válido."""
    errores = []
    try:
        datos, cuerpo = parsear_frontmatter(texto)
    except ErrorFormato as e:
        return [str(e)]

    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in datos:
            errores.append(f"falta el campo obligatorio '{campo}'")

    if "id" in datos and not RE_ID.match(datos["id"] or ""):
        errores.append(f"id con formato inválido: {datos['id']!r}")
    if nombre_archivo:
        m = RE_NOMBRE.match(nombre_archivo)
        if not m:
            errores.append(f"nombre de archivo inválido: {nombre_archivo!r}")
        elif "id" in datos and datos["id"] != f"AUD-{m.group(1)}-{m.group(2)}":
            errores.append(f"el id {datos['id']!r} no coincide con el nombre del archivo")

    if "commit_auditado" in datos and not RE_SHA.match(datos["commit_auditado"] or ""):
        errores.append("commit_auditado debe ser un SHA completo de 40 caracteres hexadecimales")
    if "fecha_utc" in datos and not RE_FECHA.match(datos["fecha_utc"] or ""):
        errores.append("fecha_utc debe tener la forma AAAA-MM-DDTHH:MM:SSZ")

    auditor = datos.get("auditor")
    if isinstance(auditor, dict):
        for campo in CAMPOS_AUDITOR:
            if campo not in auditor:
                errores.append(f"falta auditor.{campo}")
        if "commit_auditor" in auditor and not RE_SHA.match(auditor["commit_auditor"] or ""):
            errores.append("auditor.commit_auditor debe ser un SHA completo de 40 caracteres")
        if auditor.get("plataforma_ejecucion") not in PLATAFORMAS:
            errores.append(f"auditor.plataforma_ejecucion debe ser uno de {sorted(PLATAFORMAS)}")
    elif "auditor" in datos:
        errores.append("auditor debe ser un mapa con sus campos")

    previa = datos.get("auditoria_previa")
    if previa is not None and not RE_ID.match(previa or ""):
        errores.append(f"auditoria_previa debe ser null o un id válido: {previa!r}")

    veredicto = datos.get("veredicto")
    if veredicto not in VEREDICTOS:
        errores.append(f"veredicto debe ser uno de {sorted(VEREDICTOS)}")

    conteo_declarado = datos.get("conteo_hallazgos")
    if not isinstance(conteo_declarado, dict):
        errores.append("conteo_hallazgos debe ser un mapa con los cinco conteos")
        conteo_declarado = {}
    for sev in CAMPOS_CONTEO:
        if sev not in conteo_declarado:
            errores.append(f"falta conteo_hallazgos.{sev}")
        elif not str(conteo_declarado[sev]).isdigit():
            errores.append(f"conteo_hallazgos.{sev} debe ser un entero no negativo")

    secciones = _secciones(cuerpo)
    nombres = [nombre for _, nombre, _ in secciones]
    numeros = [num for num, _, _ in secciones]
    if numeros != list(range(1, len(SECCIONES) + 1)) or nombres != SECCIONES:
        errores.append(f"las secciones deben aparecer en este orden: {', '.join(SECCIONES)}")
        return errores

    por_nombre = {nombre: texto for _, nombre, texto in secciones}

    controles = [f for f in _filas_tabla(por_nombre["Controles"]) if len(f) >= 4]
    proveedores = [f for f in _filas_tabla(por_nombre["Cumplimiento por proveedor"]) if len(f) >= 5]
    hallazgos = _bloques_hallazgo(por_nombre["Hallazgos"])

    resultados = {f[1] for f in controles}
    estados_prov = {f[3] for f in proveedores}

    conteo_real = {sev: 0 for sev in CAMPOS_CONTEO}
    no_cerrados = {sev: 0 for sev in CAMPOS_CONTEO}
    for encabezado, campos in hallazgos:
        partes = RE_HALLAZGO.match(encabezado)
        if not partes:
            errores.append(f"ID de hallazgo inválido: {encabezado!r}")
            continue
        sev = campos.get("Severidad", "")
        if sev not in CAMPOS_CONTEO:
            errores.append(f"{encabezado}: severidad inválida {sev!r}")
            continue
        if campos.get("Categoría") != partes.group(1):
            errores.append(f"{encabezado}: la categoría no coincide con el ID")
        estado = campos.get("Estado", "")
        if estado not in ESTADOS_HALLAZGO:
            errores.append(f"{encabezado}: estado inválido {estado!r}")
        conteo_real[sev] += 1
        if estado != "CERRADO":
            no_cerrados[sev] += 1

    for sev in CAMPOS_CONTEO:
        declarado = conteo_declarado.get(sev)
        if declarado is not None and str(declarado).isdigit() and int(declarado) != conteo_real[sev]:
            errores.append(
                f"conteo_hallazgos.{sev}={declarado} no coincide con los {conteo_real[sev]} bloques de hallazgo"
            )

    for f in controles:
        if f[1] not in RESULTADOS_CONTROL:
            errores.append(f"resultado de control inválido: {f[1]!r}")
    for f in proveedores:
        if f[3] not in ESTADOS_PROVEEDOR:
            errores.append(f"estado de proveedor inválido: {f[3]!r}")

    obligan_fail = []
    if no_cerrados["critico"] or no_cerrados["alto"]:
        obligan_fail.append("hallazgo crítico o alto sin cerrar")
    if "NO_CUMPLE" in estados_prov:
        obligan_fail.append("requisito de proveedor NO_CUMPLE")
    if "NO_EJECUTADO" in resultados:
        obligan_fail.append("control NO_EJECUTADO")
    if "FAIL" in resultados:
        obligan_fail.append("control FAIL")

    if veredicto in VEREDICTOS:
        if obligan_fail and veredicto != "FAIL":
            errores.append(f"el veredicto debe ser FAIL por: {', '.join(obligan_fail)}")
        if veredicto == "PASS":
            if no_cerrados["medio"]:
                errores.append("PASS no admite hallazgos medios sin cerrar")
            if "N/A" in resultados:
                errores.append("PASS no admite controles N/A; usar PASS_WITH_NA")
            if "NO_VERIFICADO" in estados_prov:
                errores.append("PASS no admite requisitos NO_VERIFICADO")
        if veredicto == "PASS_WITH_NA" and "N/A" not in resultados:
            errores.append("PASS_WITH_NA exige al menos un control N/A justificado")

    return errores


def validar_archivo(ruta):
    ruta = Path(ruta)
    texto = ruta.read_text(encoding="utf-8")
    return validar_texto(texto, ruta.name)


def main(argumentos):
    if not argumentos:
        print("Uso: python -I scripts/validar_informe.py <informe.md> [...]", file=sys.stderr)
        return 2
    codigo = 0
    for arg in argumentos:
        errores = validar_archivo(arg)
        if errores:
            codigo = 1
            for e in errores:
                print(f"ERROR {arg}: {e}")
        else:
            print(f"OK {arg}")
    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
