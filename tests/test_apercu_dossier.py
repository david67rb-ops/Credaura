"""Pages de l'aperçu du dossier sur l'accueil. PyMuPDF est un outil de
développement : sans lui, ces tests sont ignorés.

    venv/bin/python -m unittest discover -s tests
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts"))

import generer_apercu_dossier as apercu  # noqa: E402

try:
    import pymupdf  # noqa: F401
except ImportError:
    pymupdf = None


@unittest.skipIf(pymupdf is None, "PyMuPDF n'est pas installé")
class ReperagePages(unittest.TestCase):
    def test_quatre_pages_distinctes_dans_l_ordre(self):
        pages = apercu.pages_apercu()
        numeros = [
            pages[apercu.GARDE],
            pages["2-marche.webp"],
            pages["3-financement.webp"],
            pages["4-synthese.webp"],
        ]
        self.assertEqual(numeros, sorted(set(numeros)))
        self.assertEqual(len(numeros), 4)

    def test_le_sommaire_ne_compte_pas_comme_un_chapitre(self):
        with pymupdf.open(apercu.PDF_EXEMPLE) as doc:
            self.assertEqual(apercu.titre_de_page(doc[1]), "Sommaire")
        self.assertGreater(apercu.pages_apercu()["2-marche.webp"], 2)

    def test_page_manquante_arrete_le_script(self):
        titres = apercu.CHAPITRES
        apercu.CHAPITRES = (("x.webp", "Chapitre absent"),)
        try:
            with self.assertRaises(SystemExit) as arret:
                apercu.pages_apercu()
        finally:
            apercu.CHAPITRES = titres
        self.assertIn("Chapitre absent", str(arret.exception))


class PoidsImages(unittest.TestCase):
    def test_images_legeres(self):
        tailles = [f.stat().st_size for f in apercu.APERCU.glob("*.webp")]
        self.assertEqual(len(tailles), 4)
        self.assertLessEqual(max(tailles), apercu.POIDS_MAX)
        self.assertLessEqual(sum(tailles), 180_000)


if __name__ == "__main__":
    unittest.main()
