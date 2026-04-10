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

# ── Données partis ────────────────────────────────────────────────────────────
PARTIS_DATA = {
    "RN": {
        "nom": "Rassemblement National", "nom_court": "RN", "couleur": "#003189",
        "description": "Le Rassemblement National est le premier parti de France par le nombre de voix aux législatives 2024. Fondé en 1972 sous le nom de Front National par Jean-Marie Le Pen, il a été rebaptisé en 2018 sous la direction de Marine Le Pen. Le parti prône la priorité nationale, le contrôle strict de l'immigration et une vision souverainiste de l'Europe.",
        "valeurs": ["Priorité nationale", "Souveraineté", "Sécurité", "Identité française", "Protection sociale", "Frexit / Europe des nations"],
        "fondation": 1972, "orientation": "Droite nationaliste", "position_hemicycle": 1,
        "president": "Marine Le Pen",
        "propositions_lois": [
            "Référendum sur l'immigration (restriction constitutionnelle)",
            "Suppression du droit du sol automatique",
            "Retraite à 60 ans pour les carrières longues",
            "Préférence nationale dans l'emploi et les aides sociales",
            "Sortie du commandement intégré de l'OTAN",
            "Rétablissement des frontières nationales (suspension Schengen)",
        ],
        "actualites": [
            "Marine Le Pen condamnée en appel — inéligibilité de 5 ans confirmée (mars 2025)",
            "Le groupe RN reste le plus important de l'Assemblée avec 143 sièges",
            "Jordan Bardella désigné chef de file pour les prochaines élections",
        ],
    },
    "NFP": {
        "nom": "Nouveau Front Populaire", "nom_court": "NFP", "couleur": "#B71C1C",
        "description": "Coalition de gauche formée pour les législatives de juin 2024, le Nouveau Front Populaire rassemble La France Insoumise, le Parti Socialiste, Les Écologistes et le Parti Communiste. Arrivée en tête en nombre de voix, elle n'a pas obtenu de majorité absolue.",
        "valeurs": ["Justice sociale", "Planification écologique", "Abrogation réforme des retraites", "Services publics", "Paix"],
        "fondation": 2024, "orientation": "Gauche", "position_hemicycle": 8,
        "president": "Coalition (LFI, PS, Écolos, PCF)",
        "propositions_lois": [
            "Abrogation de la réforme des retraites — retour à 60 ans",
            "Blocage des prix des produits de première nécessité",
            "Taxation des superprofits et des milliardaires",
            "Plan de bifurcation écologique (100 Mds€)",
            "Régularisation des travailleurs sans-papiers",
        ],
        "actualites": [
            "La coalition reste unie malgré les tensions internes LFI/PS",
            "Lucie Castets proposée comme Première ministre — refusée par l'Élysée",
            "Dépôt d'une motion de censure contre le gouvernement Bayrou (janvier 2025)",
        ],
    },
    "ENS": {
        "nom": "Ensemble pour la République", "nom_court": "ENS", "couleur": "#FF6D00",
        "description": "Ensemble pour la République est le groupe parlementaire de la majorité présidentielle issu de Renaissance (ex-LREM), parti fondé par Emmanuel Macron en 2016. Il défend une ligne réformiste centriste, pro-européenne et libérale sur le plan économique.",
        "valeurs": ["Progrès", "Europe fédérale", "Réforme de l'État", "Innovation", "Dépassement gauche/droite"],
        "fondation": 2016, "orientation": "Centre", "position_hemicycle": 4,
        "president": "Gabriel Attal",
        "propositions_lois": [
            "Loi de finances 2025 — réduction du déficit à 5% du PIB",
            "Réforme de l'assurance-chômage (durcissement conditions)",
            "Loi industrie verte — décarbonation de l'économie",
            "Réforme de la haute fonction publique",
            "Loi plein emploi — France Travail",
        ],
        "actualites": [
            "Gabriel Attal élu président du groupe Ensemble à l'AN",
            "Soutien au gouvernement Bayrou sans participation directe",
            "Débat interne sur la stratégie face au RN et au NFP",
        ],
    },
    "MODEM": {
        "nom": "Mouvement Démocrate", "nom_court": "MoDem", "couleur": "#FF8F00",
        "description": "Le Mouvement Démocrate est un parti centriste fondé par François Bayrou en 2007, après l'UDF. Profondément européen et humaniste, il est le parti du Premier ministre actuel. Il défend une vision sociale-libérale et une Europe intégrée.",
        "valeurs": ["Humanisme", "Europe fédérale", "Démocratie participative", "Éducation", "Social-libéralisme"],
        "fondation": 2007, "orientation": "Centre", "position_hemicycle": 5,
        "president": "François Bayrou",
        "propositions_lois": [
            "Réforme du mode de scrutin — introduction de la proportionnelle",
            "Loi de programmation budgétaire pluriannuelle",
            "Réforme de l'éducation nationale (autonomie des établissements)",
            "Politique familiale renforcée",
        ],
        "actualites": [
            "François Bayrou nommé Premier ministre le 13 janvier 2025",
            "Le MoDem obtient plusieurs portefeuilles ministériels clés",
            "Bayrou s'engage sur un budget équilibré d'ici 2029",
        ],
    },
    "HOR": {
        "nom": "Horizons", "nom_court": "HOR", "couleur": "#1565C0",
        "description": "Horizons est un parti centriste-libéral fondé par Édouard Philippe en 2021. Allié de la majorité présidentielle, il défend une ligne pragmatique orientée vers les territoires et la décentralisation, avec un ancrage au centre-droit.",
        "valeurs": ["Pragmatisme", "Territoires", "Décentralisation", "Réforme", "Europe"],
        "fondation": 2021, "orientation": "Centre droit", "position_hemicycle": 3,
        "president": "Édouard Philippe",
        "propositions_lois": [
            "Acte III de la décentralisation",
            "Loi de simplification administrative pour les collectivités",
            "Réforme de la fiscalité locale",
        ],
        "actualites": [
            "Édouard Philippe positionné pour 2027 — sondages favorables",
            "Horizons soutient le gouvernement Bayrou",
            "Le parti renforce son implantation locale aux municipales partielles",
        ],
    },
    "LR": {
        "nom": "Les Républicains", "nom_court": "LR", "couleur": "#0D47A1",
        "description": "Les Républicains est le principal parti de droite classique français, héritier du gaullisme et du libéralisme conservateur, issu de l'UMP fondée en 2002. Après la scission de 2024, une partie des élus LR a rejoint le gouvernement Bayrou.",
        "valeurs": ["Liberté", "Autorité", "Sécurité", "Europe des nations", "Économie de marché"],
        "fondation": 2015, "orientation": "Droite", "position_hemicycle": 2,
        "president": "Laurent Wauquiez",
        "propositions_lois": [
            "Loi immigration — version LR (quotas annuels, fin regroupement familial élargi)",
            "Réforme de la justice — peines planchers généralisées",
            "Équilibre budgétaire en 3 ans (coupes dans les dépenses sociales)",
            "Relance du nucléaire — 6 nouveaux EPR",
        ],
        "actualites": [
            "Scission : Retailleau, Wauquiez tirent le parti vers la droite dure",
            "Bruno Retailleau — ministre de l'Intérieur dans le gouvernement Bayrou",
            "LR perd des militants au profit du RN selon les derniers sondages",
        ],
    },
    "LFI": {
        "nom": "La France Insoumise", "nom_court": "LFI", "couleur": "#B71C1C",
        "description": "La France Insoumise est un mouvement politique de gauche radicale fondé par Jean-Luc Mélenchon en 2016. Première force du NFP en nombre de députés, il prône la rupture avec les traités européens et l'établissement d'une VIe République.",
        "valeurs": ["Souveraineté populaire", "VIe République", "Planification écologique", "Justice fiscale", "Paix et non-alignement"],
        "fondation": 2016, "orientation": "Gauche radicale", "position_hemicycle": 9,
        "president": "Jean-Luc Mélenchon",
        "propositions_lois": [
            "VIe République — Assemblée constituante",
            "Retraite à 60 ans — abrogation immédiate",
            "Salaire maximum légal (20× le SMIC)",
            "Sortie du commandement de l'OTAN",
            "Référendum sur les traités de libre-échange",
            "100% énergies renouvelables d'ici 2040",
        ],
        "actualites": [
            "Tensions au sein du NFP entre LFI et PS sur la stratégie parlementaire",
            "Mélenchon annonce ne pas être candidat à la présidentielle 2027",
            "Mathilde Panot réélue présidente du groupe LFI à l'AN",
        ],
    },
    "SOC": {
        "nom": "Socialistes et Apparentés", "nom_court": "PS", "couleur": "#E91E63",
        "description": "Le Parti Socialiste, fondé en 1969, est le principal parti de la gauche réformiste française. Après une crise profonde post-2017, il se redresse dans le cadre du NFP tout en cherchant à se différencier de LFI.",
        "valeurs": ["Justice sociale", "Solidarité", "Europe sociale", "Laïcité", "Égalité femmes-hommes"],
        "fondation": 1969, "orientation": "Gauche", "position_hemicycle": 7,
        "president": "Olivier Faure",
        "propositions_lois": [
            "Loi sur le revenu universel d'activité (RUA)",
            "Réforme de la fiscalité successorale",
            "Droit à l'avortement dans la Constitution (acquis)",
            "Loi sur le logement social d'urgence",
        ],
        "actualites": [
            "Le PS cherche à s'émanciper de LFI au sein du NFP",
            "Bonne performance aux sénatoriales partielles de 2025",
            "Olivier Faure maintient le cap d'une 'gauche de gouvernement'",
        ],
    },
    "ECO": {
        "nom": "Les Écologistes", "nom_court": "Écolos", "couleur": "#2E7D32",
        "description": "Les Écologistes (anciennement EELV) portent la transition écologique et les droits civiques au cœur de leur projet. Membres du NFP, ils défendent une écologie féministe, solidaire et non-violente.",
        "valeurs": ["Transition écologique", "Féminisme", "Non-violence", "Démocratie locale", "Droits des minorités"],
        "fondation": 2010, "orientation": "Gauche écologiste", "position_hemicycle": 6,
        "president": "Marine Tondelier",
        "propositions_lois": [
            "Loi énergie — 100% renouvelables d'ici 2035",
            "Interdiction des pesticides de synthèse d'ici 2030",
            "Revenu de base universel (900€/mois)",
            "Loi sur la santé environnementale",
            "Réduction du temps de travail à 32h",
        ],
        "actualites": [
            "Marine Tondelier, figure montante de la gauche française",
            "Les Écolos s'opposent à la relance nucléaire du gouvernement",
            "Succès aux élections municipales partielles dans plusieurs grandes villes",
        ],
    },
    "GDR": {
        "nom": "Gauche Démocrate et Républicaine", "nom_court": "GDR", "couleur": "#C62828",
        "description": "Le groupe GDR rassemble les députés communistes et une partie des élus ultramarins de gauche. Héritier du Parti Communiste Français fondé en 1920, il défend les services publics et une politique de paix.",
        "valeurs": ["Services publics", "Paix", "Droits des travailleurs", "Outre-mer", "Communisme républicain"],
        "fondation": 1920, "orientation": "Gauche", "position_hemicycle": 10,
        "president": "André Chassaigne",
        "propositions_lois": [
            "Nationalisation des autoroutes",
            "Loi sur la réquisition des logements vides",
            "Statut de la fonction publique étendu aux contractuels",
            "Loi cadre sur les droits des Outre-mer",
        ],
        "actualites": [
            "Le PCF marque ses distances avec LFI sur les questions géopolitiques",
            "André Chassaigne reconduit à la tête du groupe GDR",
            "Campagne nationale pour la nationalisation des autoroutes",
        ],
    },
    "LIOT": {
        "nom": "Libertés, Indépendants, Outre-mer et Territoires", "nom_court": "LIOT", "couleur": "#6A1B9A",
        "description": "LIOT est un groupe transpartisan qui rassemble des élus attachés à leur indépendance vis-à-vis des grandes machines partisanes, avec une forte représentation ultramarine. Il joue souvent un rôle de pivot dans les votes clés.",
        "valeurs": ["Indépendance", "Territoires", "Outre-mer", "Pragmatisme", "Libertés individuelles"],
        "fondation": 2022, "orientation": "Centre / Divers", "position_hemicycle": 5,
        "president": "Bertrand Pancher",
        "propositions_lois": [
            "Loi pour l'autonomie des collectivités d'Outre-mer",
            "Réforme du financement des communes rurales",
            "Loi contre les déserts médicaux en territoire",
        ],
        "actualites": [
            "LIOT joue un rôle clé dans la survie du gouvernement Bayrou",
            "Le groupe maintient sa ligne d'indépendance et vote au cas par cas",
            "Forte mobilisation sur la question des Outre-mer en difficulté budgétaire",
        ],
    },
}

# ── Gouvernement Bayrou (janvier 2025) ───────────────────────────────────────
GOUVERNEMENT = [
    {"nom": "Macron",       "prenom": "Emmanuel",   "role": "Président de la République",         "parti": "ENS",   "rang": 0,  "description": "Élu en 2017, réélu en 2022. Ancien banquier et ministre de l'Économie, fondateur de Renaissance."},
    {"nom": "Bayrou",       "prenom": "François",   "role": "Premier ministre",                   "parti": "MODEM", "rang": 1,  "description": "Fondateur du MoDem, candidat à 3 présidentielles. Nommé PM le 13 janvier 2025 après la chute de Barnier."},
    {"nom": "Barrot",       "prenom": "Jean-Noël",  "role": "Ministre des Affaires étrangères",   "parti": "MODEM", "rang": 2,  "description": "Ancien secrétaire d'État au Numérique. Maintenu à son poste des Affaires étrangères."},
    {"nom": "Retailleau",   "prenom": "Bruno",      "role": "Ministre de l'Intérieur",            "parti": "LR",    "rang": 3,  "description": "Sénateur de Vendée, figure de la droite dure. Reconduit à l'Intérieur depuis le gouvernement Barnier."},
    {"nom": "Lombard",      "prenom": "Éric",       "role": "Ministre de l'Économie et des Finances","parti":"ENS", "rang": 4,  "description": "Ancien directeur général du Crédit Mutuel. Nommé pour la première fois ministre."},
    {"nom": "Lecornu",      "prenom": "Sébastien",  "role": "Ministre des Armées",                "parti": "ENS",   "rang": 5,  "description": "Reconduit aux Armées. Ancien ministre des Outre-mer et de la Transition écologique."},
    {"nom": "Dussopt",      "prenom": "Olivier",    "role": "Ministre du Travail et de l'Emploi", "parti": "ENS",   "rang": 6,  "description": "Ancien maire d'Annonay, porté par la réforme des retraites de 2023."},
    {"nom": "Warsmann",     "prenom": "Jean-Luc",   "role": "Ministre de la Justice",             "parti": "LR",    "rang": 7,  "description": "Ancien président de la Commission des lois. Juriste de formation."},
    {"nom": "Vautrin",      "prenom": "Catherine",  "role": "Ministre de la Santé et du Travail", "parti": "HOR",   "rang": 8,  "description": "Ancienne présidente de la région Grand Est. Figure centriste."},
    {"nom": "Genevard",     "prenom": "Annie",      "role": "Ministre de l'Agriculture",          "parti": "LR",    "rang": 9,  "description": "Ancienne présidente du groupe LR à l'AN. Reconduite à l'Agriculture."},
    {"nom": "Ferracci",     "prenom": "Marc",       "role": "Ministre chargé de l'Industrie",     "parti": "ENS",   "rang": 10, "description": "Économiste, proche de Macron. Spécialiste du marché du travail."},
    {"nom": "Garot",        "prenom": "Guillaume",  "role": "Ministre de l'Éducation nationale",  "parti": "SOC",   "rang": 11, "description": "Ancien ministre délégué à l'Agroalimentaire sous Hollande."},
    {"nom": "Pannier-Runacher","prenom":"Agnès",    "role": "Ministre de la Transition énergétique","parti":"ENS",  "rang": 12, "description": "Spécialiste de l'énergie, défenseure de la filière nucléaire."},
    {"nom": "Kasbarian",    "prenom": "Guillaume",  "role": "Ministre du Logement",               "parti": "ENS",   "rang": 13, "description": "Porté par la loi anti-squat portant son nom. Reconduit au Logement."},
    {"nom": "Oudéa-Castéra","prenom": "Amélie",     "role": "Ministre des Sports",                "parti": "ENS",   "rang": 14, "description": "Ancienne ministre de l'Éducation, ex-directrice générale de Roland-Garros."},
]

COULEURS = {
    "RN":"#003189","NFP":"#B71C1C","ENS":"#FF6D00","MODEM":"#FF8F00","HOR":"#1565C0",
    "LR":"#0D47A1","LFI":"#B71C1C","SOC":"#E91E63","ECO":"#2E7D32",
    "GDR":"#C62828","LIOT":"#6A1B9A","NI":"#607D8B",
}

# ── Proxy photo ───────────────────────────────────────────────────────────────
@app.get("/proxy/portrait/{depute_id}")
async def proxy_portrait(depute_id: str, slug: str = Query(default=""), db: Session = Depends(get_db)):
    # Récupère le slug depuis la DB si non fourni
    if not slug:
        depute = db.query(Depute).filter(Depute.id == depute_id).first()
        if depute and depute.slug:
            slug = depute.slug

    urls = []
    # 1. nosdeputes.fr — source principale, pas de protection hotlink
    if slug:
        urls.append(f"https://www.nosdeputes.fr/depute/photo/{slug}")

    # 2. Tente AN avec headers complets (parfois ça passe)
    numeric = depute_id.replace("PA","").replace("pa","")
    headers_an = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Referer": "https://www.assemblee-nationale.fr/dyn/deputes",
        "Accept": "image/webp,image/*,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-origin",
    }
    an_urls = [
        f"https://www.assemblee-nationale.fr/dyn/static/atlas/assets/portraits/edito/{numeric}.jpg",
        f"https://www.assemblee-nationale.fr/static/atlas/assets/portraits/edito/2x/{numeric}.jpg",
    ]

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for url in urls:
            try:
                r = await client.get(url)
                ct = r.headers.get("content-type","")
                if r.status_code == 200 and "image" in ct and len(r.content) > 2000:
                    return Response(content=r.content, media_type=ct,
                        headers={"Cache-Control":"public, max-age=604800"})
            except Exception:
                continue
        for url in an_urls:
            try:
                r = await client.get(url, headers=headers_an)
                ct = r.headers.get("content-type","")
                if r.status_code == 200 and "image" in ct and len(r.content) > 2000:
                    return Response(content=r.content, media_type=ct,
                        headers={"Cache-Control":"public, max-age=604800"})
            except Exception:
                continue

    return JSONResponse(status_code=404, content={"detail": "Portrait non disponible"})

# ── Deputés ────────────────────────────────────────────────────────────────────
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
        return JSONResponse(status_code=404, content={"detail":"Introuvable"})
    return _fmt_depute(d)

def _fmt_depute(d: Depute) -> dict:
    slug_param = f"?slug={d.slug}" if d.slug else ""
    return {
        "id": d.id, "prenom": d.prenom, "nom": d.nom,
        "groupe": d.groupe, "circonscription": d.circonscription,
        "slug": d.slug,
        "photo_url": f"http://localhost:8000/proxy/portrait/{d.id}{slug_param}",
        "url_nosdeputes": d.url_nosdeputes,
    }

# ── Partis ─────────────────────────────────────────────────────────────────────
@app.get("/partis")
def get_partis(db: Session = Depends(get_db)):
    counts = dict(db.query(Depute.groupe, func.count(Depute.id)).group_by(Depute.groupe).all())
    result = []
    for code, data in PARTIS_DATA.items():
        nb = counts.get(code, 0)
        if code == "NFP":  # NFP = LFI+SOC+ECO+GDR agrégés
            nb = counts.get("LFI",0)+counts.get("SOC",0)+counts.get("ECO",0)+counts.get("GDR",0)
        result.append({"id":code,"slug":code.lower(),**data,"nb_sieges":nb})
    return sorted(result, key=lambda x: x["nb_sieges"], reverse=True)

@app.get("/partis/{slug}")
def get_parti(slug: str, db: Session = Depends(get_db)):
    code = slug.upper()
    if code not in PARTIS_DATA:
        return JSONResponse(status_code=404, content={"detail":"Parti introuvable"})
    data = PARTIS_DATA[code]
    codes_groupe = [code]
    if code == "NFP":
        codes_groupe = ["LFI","SOC","ECO","GDR"]
    deputes = (db.query(Depute)
        .filter(Depute.groupe.in_(codes_groupe))
        .order_by(Depute.nom).all())
    return {
        "id":code,"slug":slug,**data,
        "nb_sieges":len(deputes),
        "deputes":[_fmt_depute(d) for d in deputes],
    }

# ── Gouvernement ───────────────────────────────────────────────────────────────
@app.get("/gouvernement")
def get_gouvernement():
    return [
        {**m, "couleur": COULEURS.get(m["parti"],"#607D8B"),
         "initiales": (m["prenom"][0] if m["prenom"] else "") + m["nom"][0]}
        for m in GOUVERNEMENT
    ]

# ── Stats ──────────────────────────────────────────────────────────────────────
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Depute.id)).scalar()
    by_groupe = (db.query(Depute.groupe, func.count(Depute.id))
        .group_by(Depute.groupe).order_by(func.count(Depute.id).desc()).all())
    return {
        "total_deputes": total,
        "nb_groupes": len(by_groupe),
        "by_groupe": [{"groupe":g,"count":c,"couleur":COULEURS.get(g,"#888")} for g,c in by_groupe],
    }