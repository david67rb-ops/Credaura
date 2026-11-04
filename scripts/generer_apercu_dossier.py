"""Images de l'aperçu du dossier sur l'accueil : 4 vraies pages du PDF de
l'exemple fictif, rendues en WebP dans app/data/exemple-dossier/apercu/, plus
apercu.json (nombre de pages, pour la légende). Appelé par
generer_exemple_dossier.py ; à relancer seul pour refaire les images :

    venv/bin/python scripts/generer_apercu_dossier.py

Outils de développement uniquement, le serveur ne fait que servir les images
(rien dans requirements-server.txt). Sur un Mac Intel, PyMuPDF s'installe par
son paquet précompilé :

    venv/bin/python -m pip install --only-binary=:all: pymupdf
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "app" / "data" / "exemple-dossier"
PDF_EXEMPLE = DOSSIER / "Exemple de dossier de financement.pdf"
APERCU = DOSSIER / "apercu"

GARDE = "1-garde.webp"
# Repérées par le titre du chapitre : les numéros de page peuvent bouger.
CHAPITRES = (
    ("2-marche.webp", "Étude de marché"),
    ("3-financement.webp", "Plan de financement"),
    ("4-synthese.webp", "Synthèse du projet"),
)
LARGEUR_PX = 760
QUALITE = 82
QUALITE_MINI = 60  # en dessous, le texte des pages devient baveux
POIDS_MAX = 45_000  # octets par image


def _pymupdf():
    try:
        import pymupdf
    except ImportError:
        sys.exit("PyMuPDF manque : venv/bin/python -m pip install --only-binary=:all: pymupdf")
    return pymupdf


def titre_de_page(page) -> str:
    """Le titre d'un chapitre est le plus grand texte de sa page. Les mêmes
    mots au sommaire, plus petits, ne comptent donc pas."""
    lignes = [
        (max(span["size"] for span in ligne["spans"]), "".join(span["text"] for span in ligne["spans"]).strip())
        for bloc in page.get_text("dict")["blocks"]
        for ligne in bloc.get("lines", [])
    ]
    lignes = [ligne for ligne in lignes if ligne[1]]
    return max(lignes)[1] if lignes else ""


def pages_apercu(pdf: Path = PDF_EXEMPLE) -> dict[str, int]:
    """{fichier image: numéro de page}, page de garde comprise. Arrête le
    script si un chapitre manque : jamais d'aperçu incomplet."""
    with _pymupdf().open(pdf) as doc:
        titres = [titre_de_page(page) for page in doc]
    pages = {GARDE: 1}
    for fichier, titre in CHAPITRES:
        if titre not in titres:
            sys.exit(f"Aperçu non généré : page « {titre} » introuvable dans {pdf.name}.")
        pages[fichier] = titres.index(titre) + 1
    return pages


def _webp(page) -> bytes:
    from PIL import Image

    pymupdf = _pymupdf()
    zoom = LARGEUR_PX / page.rect.width
    rendu = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    image = Image.frombytes("RGB", (rendu.width, rendu.height), rendu.samples)
    for qualite in range(QUALITE, QUALITE_MINI - 1, -4):
        tampon = io.BytesIO()
        image.save(tampon, "WEBP", quality=qualite, method=6)
        if tampon.tell() <= POIDS_MAX:
            return tampon.getvalue()
    sys.exit(f"Aperçu non généré : page {page.number + 1} au-dessus de {POIDS_MAX // 1000} Ko, même en qualité {QUALITE_MINI}.")


def generer_apercu(pdf: Path = PDF_EXEMPLE) -> None:
    pages = pages_apercu(pdf)
    APERCU.mkdir(parents=True, exist_ok=True)
    with _pymupdf().open(pdf) as doc:
        for fichier, numero in pages.items():
            contenu = _webp(doc[numero - 1])
            (APERCU / fichier).write_bytes(contenu)
            print(f"Aperçu : {fichier} (page {numero}, {len(contenu) / 1000:.0f} Ko)")
        (APERCU / "apercu.json").write_text(json.dumps({"nb_pages": doc.page_count}) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generer_apercu()
