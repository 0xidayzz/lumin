import httpx
import re
from db import SessionLocal, engine, Base
from models import Depute

Base.metadata.create_all(bind=engine)

NOS_DEPUTES_URL = "https://www.nosdeputes.fr/deputes/json"

def fetch_and_store():
    print("Récupération depuis nosdeputes.fr…")
    with httpx.Client(timeout=30) as client:
        r = client.get(NOS_DEPUTES_URL)
        r.raise_for_status()
        data = r.json()

    deputes_raw = data.get("deputes", [])
    db = SessionLocal()
    nb = 0

    for item in deputes_raw:
        d = item.get("depute", item)

        # nosdeputes.fr fournit l'ID AN sous forme "PA..." dans le champ id_an
        an_id = d.get("id_an", "")
        if an_id and not an_id.startswith("PA"):
            an_id = f"PA{an_id}"

        slug     = d.get("slug", "")
        prenom   = d.get("prenom", "")
        nom      = d.get("nom", "")
        groupe   = d.get("groupe_sigle", d.get("groupe", {}).get("sigle", "NI"))
        circ     = d.get("nom_circo", "")
        num_circ = d.get("num_circo", "")
        dept     = d.get("num_deptmt", "")

        if circ and num_circ:
            circonscription = f"{circ} ({dept}) - {num_circ}e"
        else:
            circonscription = circ

        if not an_id or not prenom or not nom:
            continue

        existing = db.query(Depute).filter(Depute.id == an_id).first()
        if existing:
            existing.groupe         = groupe
            existing.circonscription= circonscription
            existing.slug           = slug
            existing.url_nosdeputes = f"https://www.nosdeputes.fr/{slug}" if slug else None
        else:
            db.add(Depute(
                id=an_id,
                prenom=prenom,
                nom=nom,
                groupe=groupe,
                circonscription=circonscription,
                slug=slug,
                url_nosdeputes=f"https://www.nosdeputes.fr/{slug}" if slug else None,
            ))
            nb += 1

    db.commit()
    total = db.query(Depute).count()
    db.close()
    print(f"✓ {nb} nouveaux députés insérés — total : {total}")

if __name__ == "__main__":
    fetch_and_store()