import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import validar_informe  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
NOMBRE_VALIDO = "2026-10-19-001-apex-skills.md"


def _texto(nombre):
    return (FIXTURES / nombre).read_text(encoding="utf-8")


class InformeValidoTest(unittest.TestCase):
    def test_informe_valido_no_tiene_errores(self):
        errores = validar_informe.validar_texto(_texto("informe_valido.md"), NOMBRE_VALIDO)
        self.assertEqual(errores, [])

    def test_veredicto_pass_con_hallazgo_alto_abierto_se_rechaza(self):
        texto = _texto("informe_valido.md").replace("veredicto: FAIL", "veredicto: PASS")
        errores = validar_informe.validar_texto(texto, NOMBRE_VALIDO)
        self.assertTrue(any("debe ser FAIL" in e for e in errores), errores)

    def test_hallazgo_cerrado_no_obliga_a_fail(self):
        texto = _texto("informe_valido.md").replace("**Estado:** NUEVO", "**Estado:** CERRADO")
        texto = texto.replace("NO_CUMPLE", "CUMPLE")
        texto = texto.replace("veredicto: FAIL", "veredicto: PASS")
        errores = validar_informe.validar_texto(texto, NOMBRE_VALIDO)
        self.assertEqual(errores, [])


class InformeMalFormadoTest(unittest.TestCase):
    def setUp(self):
        self.errores = validar_informe.validar_texto(_texto("informe_mal_formado.md"), "2026-10-19-001-x.md")

    def _contiene(self, fragmento):
        return any(fragmento in e for e in self.errores)

    def test_detecta_campo_obligatorio_faltante(self):
        self.assertTrue(self._contiene("falta el campo obligatorio 'rama'"), self.errores)

    def test_detecta_sha_invalido(self):
        self.assertTrue(self._contiene("commit_auditado debe ser un SHA"), self.errores)

    def test_detecta_fecha_invalida(self):
        self.assertTrue(self._contiene("fecha_utc debe tener la forma"), self.errores)

    def test_detecta_plataforma_fuera_de_lista(self):
        self.assertTrue(self._contiene("plataforma_ejecucion debe ser uno de"), self.errores)

    def test_detecta_conteo_que_no_coincide(self):
        self.assertTrue(self._contiene("conteo_hallazgos.alto=0 no coincide"), self.errores)

    def test_detecta_veredicto_pass_con_alto_abierto(self):
        self.assertTrue(self._contiene("el veredicto debe ser FAIL"), self.errores)

    def test_detecta_proveedor_no_verificado_con_pass(self):
        self.assertTrue(self._contiene("PASS no admite requisitos NO_VERIFICADO"), self.errores)

    def test_detecta_nombre_que_no_coincide_con_id(self):
        texto = _texto("informe_valido.md")
        errores = validar_informe.validar_texto(texto, "2026-10-20-001-x.md")
        self.assertTrue(any("no coincide con el nombre del archivo" in e for e in errores), errores)


class EstructuraTest(unittest.TestCase):
    def test_sin_bloque_yaml_falla(self):
        errores = validar_informe.validar_texto("# Sin encabezado\n", NOMBRE_VALIDO)
        self.assertEqual(len(errores), 1)
        self.assertIn("no empieza con un bloque YAML", errores[0])

    def test_secciones_fuera_de_orden_fallan(self):
        texto = _texto("informe_valido.md")
        texto = texto.replace("## 3. Comandos ejecutados", "## 3. Temporal")
        texto = texto.replace("## 4. Controles", "## 3. Comandos ejecutados")
        texto = texto.replace("## 3. Temporal", "## 4. Controles")
        errores = validar_informe.validar_texto(texto, NOMBRE_VALIDO)
        self.assertTrue(any("deben aparecer en este orden" in e for e in errores), errores)

    def test_id_de_hallazgo_invalido(self):
        texto = _texto("informe_valido.md").replace("HALL-cumplimiento-3f9a21", "HALL-cumplimiento-XYZ")
        errores = validar_informe.validar_texto(texto, NOMBRE_VALIDO)
        self.assertTrue(any("ID de hallazgo inválido" in e for e in errores), errores)


if __name__ == "__main__":
    unittest.main()
