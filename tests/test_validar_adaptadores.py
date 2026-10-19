import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import validar_adaptadores  # noqa: E402


class AdaptadoresTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        origen = self.raiz / "skills" / "auditor"
        origen.mkdir(parents=True)
        (origen / "SKILL.md").write_text("---\nname: auditor\n---\ncontenido\n", encoding="utf-8")
        (origen / "references").mkdir()
        (origen / "references" / "CRITERIOS.md").write_text("criterios\n", encoding="utf-8")
        for plataforma in validar_adaptadores.ADAPTADORES:
            (self.raiz / "plataformas" / plataforma).mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_regenerar_deja_todo_sincronizado(self):
        validar_adaptadores.verificar(raiz=self.raiz, regenerar=True)
        self.assertEqual(validar_adaptadores.verificar(raiz=self.raiz), [])

    def test_adaptador_faltante_se_reporta(self):
        validar_adaptadores.verificar(raiz=self.raiz, regenerar=True)
        shutil.rmtree(self.raiz / "plataformas" / "claude" / "skills")
        problemas = validar_adaptadores.verificar(raiz=self.raiz)
        self.assertTrue(any("falta el adaptador claude" in p for p in problemas), problemas)

    def test_adaptador_editado_a_mano_se_reporta(self):
        validar_adaptadores.verificar(raiz=self.raiz, regenerar=True)
        ruta = self.raiz / "plataformas" / "antigravity" / ".agents" / "skills" / "auditor" / "SKILL.md"
        ruta.write_text("cambio no sincronizado\n", encoding="utf-8")
        problemas = validar_adaptadores.verificar(raiz=self.raiz)
        self.assertTrue(any("antigravity" in p and "no coincide" in p for p in problemas), problemas)

    def test_adaptador_sin_references_se_reporta(self):
        validar_adaptadores.verificar(raiz=self.raiz, regenerar=True)
        ruta = self.raiz / "plataformas" / "claude" / "skills" / "auditor" / "references" / "CRITERIOS.md"
        ruta.unlink()
        problemas = validar_adaptadores.verificar(raiz=self.raiz)
        self.assertTrue(
            any("falta en el adaptador claude" in p and "CRITERIOS.md" in p for p in problemas), problemas
        )

    def test_adaptador_huerfano_se_reporta(self):
        validar_adaptadores.verificar(raiz=self.raiz, regenerar=True)
        huerfano = self.raiz / "plataformas" / "chatgpt" / "skills" / "otra-skill"
        huerfano.mkdir(parents=True)
        (huerfano / "SKILL.md").write_text("x", encoding="utf-8")
        problemas = validar_adaptadores.verificar(raiz=self.raiz)
        self.assertTrue(any("sin origen" in p and "otra-skill" in p for p in problemas), problemas)


if __name__ == "__main__":
    unittest.main()
