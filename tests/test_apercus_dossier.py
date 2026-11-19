"""Adresse à usage unique de l'aperçu du dossier Word (étape 6). Lancement :

    venv/bin/python -m unittest discover -s tests
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from nicegui import app  # noqa: E402

from gui import apercus_dossier, theme  # noqa: E402,F401  (theme monte les images de l'accueil)


class AdresseApercu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Hors serveur, NiceGUI n'a pas de configuration : sa page d'erreur 404
        # en a besoin. Celle-ci n'est utilisée que par ces tests.
        if not hasattr(app.config, "title"):
            app.config.add_run_config(
                reload=False, title="Credaura", viewport="width=device-width", favicon=None, dark=None,
                language="fr", binding_refresh_interval=0.1, reconnect_timeout=3.0, message_history_length=1000,
                tailwind=True, prod_js=True, show_welcome_message=False,
            )

    def setUp(self):
        self.client = TestClient(app)

    def test_usage_unique(self):
        url = apercus_dossier.publier(b"x")
        reponse = self.client.get(url)
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.headers["content-type"], apercus_dossier.TYPE_DOCX)
        self.assertEqual(reponse.content, b"x")
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_images_de_l_accueil_toujours_servies(self):
        for nom in ("1-garde", "2-marche", "3-financement", "4-synthese"):
            reponse = self.client.get(f"/apercu-dossier/{nom}.webp")
            self.assertEqual(reponse.status_code, 200, nom)


if __name__ == "__main__":
    unittest.main()
