from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import httpx
from db import get_db
from models import Depute

app = FastAPI(title="Lumin API")
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"], allow_headers=["*"])

# ─────────────────────────────────────────────────────────────────────────────
# LOGOS — générés en SVG côté serveur (aucune dépendance externe)
# Chaque logo est un SVG stylisé avec les vraies couleurs et sigle du parti
# ─────────────────────────────────────────────────────────────────────────────

def make_logo_svg(sigle: str, nom: str, couleur: str, couleur2: str = None) -> str:
    """Génère un logo SVG propre pour un parti politique."""
    c2 = couleur2 or couleur
    lines = nom.split(" ")
    # On prend max 2 lignes pour l'affichage
    line1 = lines[0] if lines else sigle
    line2 = " ".join(lines[1:]) if len(lines) > 1 else ""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{couleur}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <clipPath id="clip"><rect rx="16" width="120" height="120"/></clipPath>
  </defs>
  <rect width="120" height="120" rx="16" fill="url(#g)"/>
  <rect width="120" height="120" rx="16" fill="white" fill-opacity="0.07"/>
  <text x="60" y="{48 if line2 else 68}"
    font-family="system-ui,-apple-system,sans-serif"
    font-size="{28 if len(sigle) <= 3 else 22}"
    font-weight="800"
    fill="white"
    text-anchor="middle"
    dominant-baseline="central"
    letter-spacing="-0.5">{sigle}</text>
  {f'<text x="60" y="82" font-family="system-ui,-apple-system,sans-serif" font-size="9" font-weight="500" fill="white" fill-opacity="0.85" text-anchor="middle">{nom[:20]}</text>' if line2 else ''}
</svg>"""

LOGOS_SVG: dict[str, tuple[str, str, str, str | None]] = {
    # (sigle, nom_court, couleur_principale, couleur_secondaire)
    "RN":    ("RN",    "Rassemblement National",   "#1A3C8C", "#0D2461"),
    "ENS":   ("ENS",   "Ensemble",                  "#E85D00", "#C24500"),
    "REN":   ("REN",   "Renaissance",               "#E85D00", "#C24500"),
    "NFP":   ("NFP",   "Nouveau Front Pop.",         "#8B0000", "#5C0000"),
    "DR":    ("DR",    "Droite Républicaine",        "#0D3B8C", "#071F4A"),
    "LR":    ("LR",    "Les Républicains",           "#0D3B8C", "#071F4A"),
    "MODEM": ("MoDem", "Mouvement Démocrate",        "#E07B00", "#B85F00"),
    "HOR":   ("HOR",   "Horizons",                  "#1565C0", "#0D47A1"),
    "SOC":   ("PS",    "Parti Socialiste",           "#C2185B", "#880E4F"),
    "ECO":   ("ÉCOS",  "Les Écologistes",            "#2E7D32", "#1B5E20"),
    "LFI":   ("LFI",   "France Insoumise",           "#B71C1C", "#7F0000"),
    "GDR":   ("GDR",   "Gauche Démocrate",           "#C62828", "#8B0000"),
    "LIOT":  ("LIOT",  "Libertés & Territoires",    "#6A1B9A", "#4A148C"),
    "NI":    ("NI",    "Non-Inscrits",               "#546E7A", "#37474F"),
}

@app.get("/proxy/logo/{parti_id}")
async def proxy_logo(parti_id: str):
    """Retourne un logo SVG généré côté serveur — aucune dépendance externe."""
    code = parti_id.upper()
    if code not in LOGOS_SVG:
        return JSONResponse(status_code=404, content={"detail": "Parti inconnu"})
    sigle, nom, c1, c2 = LOGOS_SVG[code]
    svg = make_logo_svg(sigle, nom, c1, c2)
    return Response(
        content=svg.encode(),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )

# ─────────────────────────────────────────────────────────────────────────────
# PHOTOS MINISTRES — Wikipedia REST API (autorisée, pas de hotlinking)
# ─────────────────────────────────────────────────────────────────────────────

# Titres exacts des pages Wikipedia pour chaque ministre
WIKI_PAGES: dict[str, str] = {
    "macron":    "Emmanuel_Macron",
    "lecornu":   "Sébastien_Lecornu",
    "nunez":     "Laurent_Nuñez",
    "vautrin":   "Catherine_Vautrin",
    "farandou":  "Jean-Pierre_Farandou",
    "barbut":    "Monique_Barbut",
    "darmanin":  "Gérald_Darmanin",
    "lescure":   "Roland_Lescure",
    "papin":     "Serge_Papin",
    "genevard":  "Annie_Genevard",
    "geffray":   "Édouard_Geffray",
    "barrot":    "Jean-Noël_Barrot",
    "rist":      "Stéphanie_Rist",
    "pegard":    "Catherine_Pégard",
    "gatel":     "Françoise_Gatel",
    "amiel":     "David_Amiel_(homme_politique)",
    "baptiste":  "Philippe_Baptiste_(scientifique)",
    "ferrari":   "Marina_Ferrari",
    "tabarot":   "Philippe_Tabarot",
    "jeanbrun":  "Vincent_Jeanbrun",
    "berge":     "Aurore_Bergé",
    "bregeon":   "Maud_Bregeon",
    "haddad":    "Benjamin_Haddad",
}

# Cache en mémoire : photo_key → URL image
_photo_cache: dict[str, str | None] = {}

async def get_wiki_photo_url(page_title: str) -> str | None:
    """Récupère l'URL de la photo principale d'une page Wikipedia via l'API REST."""
    # Utilise l'API Summary de Wikipedia — autorisée, pas de blocage
    encoded = page_title.replace(" ", "_")
    api_url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            r = await client.get(api_url, headers={
                "User-Agent": "LuminApp/1.0 (https://github.com/lumin; contact@lumin.fr)",
                "Accept": "application/json",
            })
            if r.status_code == 200:
                data = r.json()
                # thumbnail.source donne l'URL directe redimensionnée
                thumb = data.get("thumbnail", {}).get("source")
                if thumb:
                    # On demande une taille plus grande (300px)
                    thumb = thumb.replace("/200px-", "/300px-").replace("/160px-", "/300px-")
                    return thumb
    except Exception:
        pass
    # Fallback : API anglaise
    try:
        api_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            r = await client.get(api_en, headers={
                "User-Agent": "LuminApp/1.0 (https://github.com/lumin; contact@lumin.fr)",
            })
            if r.status_code == 200:
                data = r.json()
                thumb = data.get("thumbnail", {}).get("source")
                if thumb:
                    return thumb.replace("/200px-", "/300px-")
    except Exception:
        pass
    return None

@app.get("/proxy/ministre/{key}")
async def proxy_ministre_photo(key: str):
    """Proxy photo ministre via Wikipedia REST API."""
    key = key.lower()
    page_title = WIKI_PAGES.get(key)
    if not page_title:
        return JSONResponse(status_code=404, content={"detail": "Ministre inconnu"})

    # Vérifie le cache
    if key not in _photo_cache:
        _photo_cache[key] = await get_wiki_photo_url(page_title)

    url = _photo_cache[key]
    if not url:
        return JSONResponse(status_code=404, content={"detail": "Photo non disponible"})

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(url, headers={
                "User-Agent": "LuminApp/1.0 (https://github.com/lumin; contact@lumin.fr)",
                "Referer": "https://fr.wikipedia.org/",
            })
            ct = r.headers.get("content-type", "image/jpeg")
            if r.status_code == 200 and "image" in ct and len(r.content) > 1000:
                return Response(content=r.content, media_type=ct,
                    headers={"Cache-Control": "public, max-age=604800"})
    except Exception:
        pass

    # Si l'URL en cache a expiré, on force le refetch
    _photo_cache[key] = await get_wiki_photo_url(page_title)
    url = _photo_cache[key]
    if url:
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                r = await client.get(url, headers={
                    "User-Agent": "LuminApp/1.0 (https://github.com/lumin; contact@lumin.fr)",
                })
                ct = r.headers.get("content-type", "image/jpeg")
                if r.status_code == 200 and "image" in ct:
                    return Response(content=r.content, media_type=ct,
                        headers={"Cache-Control": "public, max-age=604800"})
        except Exception:
            pass

    return JSONResponse(status_code=404, content={"detail": "Photo non disponible"})

# ─────────────────────────────────────────────────────────────────────────────
# PROXY PORTRAIT DÉPUTÉ
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/proxy/portrait/{depute_id}")
async def proxy_portrait(depute_id: str, slug: str = Query(default=""), db: Session = Depends(get_db)):
    if not slug:
        depute = db.query(Depute).filter(Depute.id == depute_id).first()
        if depute and depute.slug:
            slug = depute.slug

    urls = []
    if slug:
        urls.append(f"https://www.nosdeputes.fr/depute/photo/{slug}")

    numeric = depute_id.replace("PA", "").replace("pa", "")
    an_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Referer": "https://www.assemblee-nationale.fr/dyn/deputes",
        "Accept": "image/webp,image/*,*/*;q=0.8",
    }
    an_urls = [
        f"https://www.assemblee-nationale.fr/dyn/static/atlas/assets/portraits/edito/{numeric}.jpg",
        f"https://www.assemblee-nationale.fr/static/atlas/assets/portraits/edito/2x/{numeric}.jpg",
    ]

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for url in urls:
            try:
                r = await client.get(url)
                ct = r.headers.get("content-type", "")
                if r.status_code == 200 and "image" in ct and len(r.content) > 2000:
                    return Response(content=r.content, media_type=ct,
                        headers={"Cache-Control": "public, max-age=604800"})
            except Exception:
                continue
        for url in an_urls:
            try:
                r = await client.get(url, headers=an_headers)
                ct = r.headers.get("content-type", "")
                if r.status_code == 200 and "image" in ct and len(r.content) > 2000:
                    return Response(content=r.content, media_type=ct,
                        headers={"Cache-Control": "public, max-age=604800"})
            except Exception:
                continue

    return JSONResponse(status_code=404, content={"detail": "Portrait non disponible"})

# ─────────────────────────────────────────────────────────────────────────────
# DONNÉES STATIQUES — Partis & Gouvernement
# (inchangées par rapport au fichier précédent — copie intégrale)
# ─────────────────────────────────────────────────────────────────────────────

COULEURS = {
    "RN": "#1A3C8C", "ENS": "#E85D00", "REN": "#E85D00", "NFP": "#8B0000",
    "DR": "#0D3B8C", "LR": "#0D3B8C", "MODEM": "#E07B00", "HOR": "#1565C0",
    "SOC": "#C2185B", "ECO": "#2E7D32", "LFI": "#B71C1C", "GDR": "#C62828",
    "LIOT": "#6A1B9A", "NI": "#546E7A",
}

PARTIS_DATA = {
    "RN": {
        "nom": "Rassemblement National", "nom_court": "RN", "couleur": "#1A3C8C",
        "description": "Premier groupe de l'Assemblée nationale avec 143 sièges. Fondé en 1972 sous le nom de Front National, il défend la priorité nationale et le contrôle de l'immigration. Marine Le Pen a été condamnée en appel, son inéligibilité de 5 ans confirmée début 2025.",
        "valeurs": ["Priorité nationale", "Souveraineté", "Sécurité", "Identité française", "Protection sociale"],
        "fondation": 1972, "orientation": "Droite nationaliste",
        "president": "Marine Le Pen / Jordan Bardella",
        "propositions_lois": [
            "Référendum constitutionnel sur l'immigration",
            "Suppression du droit du sol automatique",
            "Retraite à 60 ans pour les carrières longues",
            "Préférence nationale pour les aides sociales",
            "Sortie du commandement intégré de l'OTAN",
        ],
        "actualites": [
            "Inéligibilité de 5 ans de Marine Le Pen confirmée en appel (mars 2025)",
            "Jordan Bardella prend la tête opérationnelle du RN",
            "Le RN s'abstient sur la motion de censure pour éviter une dissolution",
        ],
    },
    "ENS": {
        "nom": "Ensemble pour la République", "nom_court": "ENS", "couleur": "#E85D00",
        "description": "Groupe parlementaire issu de Renaissance (ex-LREM), parti d'Emmanuel Macron fondé en 2016. Gabriel Attal en est le président à l'Assemblée. Le groupe soutient le gouvernement Lecornu tout en maintenant une certaine distance.",
        "valeurs": ["Progrès", "Europe", "Réforme de l'État", "Innovation"],
        "fondation": 2016, "orientation": "Centre",
        "president": "Gabriel Attal (groupe AN)",
        "propositions_lois": [
            "Loi de finances 2026 — réduction du déficit",
            "Réforme de l'assurance-chômage",
            "Loi industrie verte",
            "France 2030 — investissements stratégiques",
        ],
        "actualites": [
            "Gabriel Attal appelle Macron à 'partager le pouvoir' (fin 2025)",
            "Ensemble soutient Lecornu sans participation directe au gouvernement",
            "Le groupe perd des membres au profit d'Horizons",
        ],
    },
    "NFP": {
        "nom": "Nouveau Front Populaire", "nom_court": "NFP", "couleur": "#8B0000",
        "description": "Coalition de gauche formée pour les législatives de 2024, rassemblant LFI, PS, Écologistes et PCF. A renversé le gouvernement Bayrou par un vote de confiance défavorable en septembre 2025.",
        "valeurs": ["Justice sociale", "Planification écologique", "Services publics"],
        "fondation": 2024, "orientation": "Gauche",
        "president": "Coalition LFI / PS / Écolos / PCF",
        "propositions_lois": [
            "Abrogation de la réforme des retraites",
            "Blocage des prix de première nécessité",
            "Taxation des superprofits",
            "Plan de bifurcation écologique (100 Mds€)",
        ],
        "actualites": [
            "Le NFP a renversé Bayrou par vote de confiance (8 sept. 2025)",
            "Le PS refuse de voter une motion de censure contre Lecornu",
            "Tensions LFI/PS sur la stratégie parlementaire",
        ],
    },
    "DR": {
        "nom": "Droite Républicaine", "nom_court": "DR", "couleur": "#0D3B8C",
        "description": "Groupe LR à l'Assemblée nationale rebaptisé 'Droite Républicaine'. Plusieurs membres ont rejoint le gouvernement Lecornu malgré l'opposition de Laurent Wauquiez, entraînant leur suspension du parti.",
        "valeurs": ["Liberté", "Autorité", "Sécurité", "Économie de marché"],
        "fondation": 2015, "orientation": "Droite",
        "president": "Laurent Wauquiez",
        "propositions_lois": [
            "Immigration — quotas annuels votés par le Parlement",
            "Justice — peines planchers généralisées",
            "Relance du nucléaire — 6 nouveaux EPR",
        ],
        "actualites": [
            "6 ministres LR suspendus du parti pour avoir rejoint Lecornu",
            "Wauquiez maintient LR dans l'opposition",
            "Le groupe rebaptisé 'Droite Républicaine' à l'AN",
        ],
    },
    "MODEM": {
        "nom": "Mouvement Démocrate", "nom_court": "MoDem", "couleur": "#E07B00",
        "description": "Parti centriste fondé par François Bayrou en 2007. Bayrou a été Premier ministre de décembre 2024 à septembre 2025 avant d'être renversé. Jean-Noël Barrot (MoDem) est reconduit aux Affaires étrangères.",
        "valeurs": ["Humanisme", "Europe fédérale", "Démocratie", "Éducation"],
        "fondation": 2007, "orientation": "Centre",
        "president": "François Bayrou",
        "propositions_lois": [
            "Réforme du scrutin proportionnel",
            "Loi de programmation budgétaire pluriannuelle",
        ],
        "actualites": [
            "Bayrou renversé par vote de confiance (8 sept. 2025)",
            "Barrot (MoDem) reconduit aux Affaires étrangères sous Lecornu",
        ],
    },
    "HOR": {
        "nom": "Horizons", "nom_court": "HOR", "couleur": "#1565C0",
        "description": "Parti centriste-libéral fondé par Édouard Philippe en 2021. Philippe, officiellement candidat à la présidentielle 2027, a appelé Macron à démissionner après le vote du budget.",
        "valeurs": ["Pragmatisme", "Territoires", "Décentralisation"],
        "fondation": 2021, "orientation": "Centre droit",
        "president": "Édouard Philippe",
        "propositions_lois": ["Acte III de la décentralisation", "Simplification administrative"],
        "actualites": [
            "Philippe appelle Macron à démissionner (déc. 2025)",
            "Philippe officiellement candidat à la présidentielle 2027",
            "Horizons renforce son implantation aux municipales 2026",
        ],
    },
    "LFI": {
        "nom": "La France Insoumise", "nom_court": "LFI", "couleur": "#B71C1C",
        "description": "Mouvement de gauche radicale fondé par Mélenchon en 2016. Première force du NFP. Mélenchon a annoncé ne pas être candidat à la présidentielle 2027.",
        "valeurs": ["VIe République", "Planification écologique", "Justice fiscale", "Paix"],
        "fondation": 2016, "orientation": "Gauche radicale",
        "president": "Jean-Luc Mélenchon",
        "propositions_lois": [
            "VIe République — Assemblée constituante",
            "Retraite à 60 ans immédiate",
            "100% renouvelables d'ici 2040",
        ],
        "actualites": [
            "LFI a conduit le NFP à renverser Bayrou (sept. 2025)",
            "Mélenchon ne se présente pas en 2027",
            "Mathilde Panot reconduite à la tête du groupe",
        ],
    },
    "SOC": {
        "nom": "Socialistes et Apparentés", "nom_court": "PS", "couleur": "#C2185B",
        "description": "Le PS se redresse dans le cadre du NFP. Il a refusé de voter la censure contre Lecornu en échange de la suspension de la réforme des retraites jusqu'en 2027.",
        "valeurs": ["Justice sociale", "Solidarité", "Europe sociale", "Laïcité"],
        "fondation": 1969, "orientation": "Gauche",
        "president": "Olivier Faure",
        "propositions_lois": ["Abrogation de la réforme des retraites", "Loi sur le logement social"],
        "actualites": [
            "Le PS obtient la suspension des retraites jusqu'en 2027",
            "Le PS refuse de voter la censure contre Lecornu",
            "Résultats positifs aux municipales 2026",
        ],
    },
    "ECO": {
        "nom": "Les Écologistes", "nom_court": "Écolos", "couleur": "#2E7D32",
        "description": "Les Écologistes (ex-EELV), membres du NFP. S'opposent à la relance nucléaire de Lecornu.",
        "valeurs": ["Transition écologique", "Féminisme", "Non-violence"],
        "fondation": 2010, "orientation": "Gauche écologiste",
        "president": "Marine Tondelier",
        "propositions_lois": ["100% renouvelables d'ici 2035", "Interdiction des pesticides de synthèse"],
        "actualites": [
            "Opposition à la relance nucléaire du gouvernement",
            "Marine Tondelier, figure montante en vue de 2027",
        ],
    },
    "GDR": {
        "nom": "Gauche Démocrate et Républicaine", "nom_court": "GDR", "couleur": "#C62828",
        "description": "Groupe PCF et ultramarins. Membre du NFP, maintient ses distances avec LFI sur les questions géopolitiques.",
        "valeurs": ["Services publics", "Paix", "Droits des travailleurs"],
        "fondation": 1920, "orientation": "Gauche",
        "president": "André Chassaigne",
        "propositions_lois": ["Nationalisation des autoroutes", "Loi sur les logements vides"],
        "actualites": ["Le PCF marque ses distances avec LFI sur le géopolitique"],
    },
    "LIOT": {
        "nom": "Libertés, Indépendants, Outre-mer et Territoires", "nom_court": "LIOT", "couleur": "#6A1B9A",
        "description": "Groupe transpartisan. S'est abstenu sur la motion de censure contre Lecornu en octobre 2025, lui permettant de survivre.",
        "valeurs": ["Indépendance", "Territoires", "Outre-mer"],
        "fondation": 2022, "orientation": "Centre / Divers",
        "president": "Bertrand Pancher",
        "propositions_lois": ["Autonomie des Outre-mer", "Financement des communes rurales"],
        "actualites": ["LIOT s'abstient sur la censure Lecornu (oct. 2025)"],
    },
}

GOUVERNEMENT = [
    {"nom":"Macron",   "prenom":"Emmanuel",  "role":"Président de la République",                              "parti":"ENS",  "rang":0,  "photo_key":"macron",   "description":"Élu en 2017, réélu en 2022. Fondateur de Renaissance."},
    {"nom":"Lecornu",  "prenom":"Sébastien", "role":"Premier ministre",                                        "parti":"ENS",  "rang":1,  "photo_key":"lecornu",  "description":"Nommé PM le 9 sept. 2025. Ancien ministre des Armées. Gouvernement remanié le 26 fév. 2026."},
    {"nom":"Nuñez",    "prenom":"Laurent",   "role":"Ministre de l'Intérieur",                                 "parti":"ENS",  "rang":2,  "photo_key":"nunez",    "description":"Ancien préfet de police de Paris."},
    {"nom":"Vautrin",  "prenom":"Catherine", "role":"Ministre des Armées et des Anciens combattants",          "parti":"HOR",  "rang":3,  "photo_key":"vautrin",  "description":"Ancienne présidente de la région Grand Est."},
    {"nom":"Farandou", "prenom":"Jean-Pierre","role":"Ministre du Travail et des Solidarités",                 "parti":"ENS",  "rang":4,  "photo_key":"farandou", "description":"Ancien PDG de la SNCF (2019-2024)."},
    {"nom":"Barbut",   "prenom":"Monique",   "role":"Ministre de la Transition écologique et de la Biodiversité","parti":"ENS","rang":5,  "photo_key":"barbut",   "description":"Ancienne directrice de la CNULCD (ONU)."},
    {"nom":"Darmanin", "prenom":"Gérald",    "role":"Garde des Sceaux, ministre de la Justice",                "parti":"NI",   "rang":6,  "photo_key":"darmanin", "description":"A quitté Renaissance en oct. 2025. Ancien ministre de l'Intérieur."},
    {"nom":"Lescure",  "prenom":"Roland",    "role":"Ministre de l'Économie et des Finances",                  "parti":"ENS",  "rang":7,  "photo_key":"lescure",  "description":"Ancien député Renaissance du Canada."},
    {"nom":"Papin",    "prenom":"Serge",     "role":"Ministre des PME, Commerce et Pouvoir d'achat",           "parti":"NI",   "rang":8,  "photo_key":"papin",    "description":"Ancien PDG de Système U (2005-2017)."},
    {"nom":"Genevard", "prenom":"Annie",     "role":"Ministre de l'Agriculture et de la Souveraineté alimentaire","parti":"LR","rang":9,  "photo_key":"genevard", "description":"Ancienne présidente du groupe LR à l'AN. Suspendue de LR."},
    {"nom":"Geffray",  "prenom":"Édouard",   "role":"Ministre de l'Éducation nationale",                       "parti":"NI",   "rang":10, "photo_key":"geffray",  "description":"Ancien directeur général de l'enseignement scolaire."},
    {"nom":"Barrot",   "prenom":"Jean-Noël", "role":"Ministre de l'Europe et des Affaires étrangères",         "parti":"MODEM","rang":11, "photo_key":"barrot",   "description":"Reconduit depuis le gouvernement Bayrou."},
    {"nom":"Rist",     "prenom":"Stéphanie", "role":"Ministre de la Santé et des Familles",                    "parti":"ENS",  "rang":12, "photo_key":"rist",     "description":"Médecin, ancienne rapporteure du budget de la Sécu."},
    {"nom":"Pégard",   "prenom":"Catherine", "role":"Ministre de la Culture",                                  "parti":"NI",   "rang":13, "photo_key":"pegard",   "description":"Ancienne présidente du château de Versailles. Remplace Dati (démissionnée 25 fév. 2026)."},
    {"nom":"Gatel",    "prenom":"Françoise", "role":"Ministre de l'Aménagement du territoire et de la Décentralisation","parti":"NI","rang":14,"photo_key":"gatel","description":"Ancienne sénatrice UDI d'Ille-et-Vilaine."},
    {"nom":"Amiel",    "prenom":"David",     "role":"Ministre de l'Action et des Comptes publics",             "parti":"ENS",  "rang":15, "photo_key":"amiel",    "description":"Fidèle de Macron. Promu le 26 fév. 2026, remplace Montchalin."},
    {"nom":"Baptiste", "prenom":"Philippe",  "role":"Ministre de l'Enseignement supérieur et de la Recherche", "parti":"NI",   "rang":16, "photo_key":"baptiste",  "description":"Ancien directeur général du CNRS."},
    {"nom":"Ferrari",  "prenom":"Marina",    "role":"Ministre des Sports et de la Jeunesse",                   "parti":"ENS",  "rang":17, "photo_key":"ferrari",  "description":"Ancienne députée ENS de Savoie."},
    {"nom":"Tabarot",  "prenom":"Philippe",  "role":"Ministre des Transports",                                 "parti":"LR",   "rang":18, "photo_key":"tabarot",  "description":"Ancien sénateur LR des Alpes-Maritimes. Suspendu de LR."},
    {"nom":"Jeanbrun", "prenom":"Vincent",   "role":"Ministre de la Ville et du Logement",                     "parti":"LR",   "rang":19, "photo_key":"jeanbrun", "description":"Maire de L'Haÿ-les-Roses. Suspendu de LR."},
    {"nom":"Bergé",    "prenom":"Aurore",    "role":"Ministre déléguée — Égalité femmes-hommes",               "parti":"ENS",  "rang":20, "photo_key":"berge",    "description":"Ancienne présidente du groupe Renaissance à l'AN."},
    {"nom":"Bregeon",  "prenom":"Maud",      "role":"Porte-parole du Gouvernement · Énergie",                  "parti":"ENS",  "rang":21, "photo_key":"bregeon",  "description":"Porte-parole. Également chargée de l'Énergie auprès de Lescure."},
    {"nom":"Haddad",   "prenom":"Benjamin",  "role":"Ministre délégué — Europe",                               "parti":"ENS",  "rang":22, "photo_key":"haddad",   "description":"Chargé de l'Europe auprès de Barrot."},
]

# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_depute(d: Depute) -> dict:
    slug_param = f"?slug={d.slug}" if getattr(d, "slug", None) else ""
    return {
        "id": d.id, "prenom": d.prenom, "nom": d.nom,
        "groupe": d.groupe, "circonscription": d.circonscription,
        "slug": getattr(d, "slug", None),
        "photo_url": f"http://localhost:8000/proxy/portrait/{d.id}{slug_param}",
    }

@app.get("/deputes")
def get_deputes(db: Session = Depends(get_db),
    q: str = Query(default=""), groupe: str = Query(default=""),
    limit: int = Query(default=100), offset: int = Query(default=0)):
    query = db.query(Depute)
    if q:
        query = query.filter(
            (func.lower(Depute.nom).contains(q.lower())) |
            (func.lower(Depute.prenom).contains(q.lower())))
    if groupe:
        query = query.filter(Depute.groupe == groupe)
    total = query.count()
    items = query.order_by(Depute.nom).offset(offset).limit(limit).all()
    return {"total": total, "items": [_fmt_depute(d) for d in items]}

@app.get("/deputes/{depute_id}")
def get_depute(depute_id: str, db: Session = Depends(get_db)):
    d = db.query(Depute).filter(Depute.id == depute_id).first()
    if not d:
        return JSONResponse(status_code=404, content={"detail": "Introuvable"})
    return _fmt_depute(d)

@app.get("/partis")
def get_partis(db: Session = Depends(get_db)):
    counts = dict(db.query(Depute.groupe, func.count(Depute.id)).group_by(Depute.groupe).all())
    result = []
    for code, data in PARTIS_DATA.items():
        nb = counts.get(code, 0)
        if code == "NFP":
            nb = sum(counts.get(g, 0) for g in ["LFI","SOC","ECO","GDR"])
        elif code == "DR":
            nb = sum(counts.get(g, 0) for g in ["LR","DR"])
        result.append({"id": code, "slug": code.lower(), **data, "nb_sieges": nb})
    return sorted(result, key=lambda x: x["nb_sieges"], reverse=True)

@app.get("/partis/{slug}")
def get_parti(slug: str, db: Session = Depends(get_db)):
    code = slug.upper()
    aliases = {"LR": "DR", "RENAISSANCE": "ENS", "RE": "ENS"}
    code = aliases.get(code, code)
    if code not in PARTIS_DATA:
        return JSONResponse(status_code=404, content={"detail": "Parti introuvable"})
    data = PARTIS_DATA[code]
    codes_groupe = {"NFP": ["LFI","SOC","ECO","GDR"], "DR": ["LR","DR"]}.get(code, [code])
    deputes = db.query(Depute).filter(Depute.groupe.in_(codes_groupe)).order_by(Depute.nom).all()
    return {"id": code, "slug": slug, **data, "nb_sieges": len(deputes),
            "deputes": [_fmt_depute(d) for d in deputes]}

@app.get("/gouvernement")
def get_gouvernement():
    return [
        {**m,
         "couleur": COULEURS.get(m["parti"], "#607D8B"),
         "initiales": (m["prenom"][0] if m["prenom"] else "") + (m["nom"][0] if m["nom"] else ""),
         "photo_url": f"http://localhost:8000/proxy/ministre/{m['photo_key']}"}
        for m in GOUVERNEMENT
    ]

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Depute.id)).scalar()
    by_groupe = (db.query(Depute.groupe, func.count(Depute.id))
        .group_by(Depute.groupe).order_by(func.count(Depute.id).desc()).all())
    return {
        "total_deputes": total,
        "nb_groupes": len(by_groupe),
        "by_groupe": [{"groupe": g, "count": c, "couleur": COULEURS.get(g, "#888")} for g, c in by_groupe],
    }