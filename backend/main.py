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
# Photos ministres : portraits Wikimedia Commons (libres de droits)
# ─────────────────────────────────────────────────────────────────────────────
PHOTOS_MINISTRES = {
    "macron":        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Emmanuel_Macron_in_2019.jpg/200px-Emmanuel_Macron_in_2019.jpg",
    "lecornu":       "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/S%C3%A9bastien_Lecornu_en_2022.jpg/200px-S%C3%A9bastien_Lecornu_en_2022.jpg",
    "nunez":         "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Laurent_Nu%C3%B1ez_-_2019_%28cropped%29.jpg/200px-Laurent_Nu%C3%B1ez_-_2019_%28cropped%29.jpg",
    "vautrin":       "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Catherine_Vautrin_%28cropped%29.jpg/200px-Catherine_Vautrin_%28cropped%29.jpg",
    "farandou":      "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Jean-Pierre_Farandou_2019.jpg/200px-Jean-Pierre_Farandou_2019.jpg",
    "darmanin":      "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/G%C3%A9rald_Darmanin_2017_01_%28cropped%29.jpg/200px-G%C3%A9rald_Darmanin_2017_01_%28cropped%29.jpg",
    "lescure":       "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Roland_Lescure_2022_%28cropped%29.jpg/200px-Roland_Lescure_2022_%28cropped%29.jpg",
    "genevard":      "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Annie_G%C3%A9nevard%2C_d%C3%A9put%C3%A9e.jpg/200px-Annie_G%C3%A9nevard%2C_d%C3%A9put%C3%A9e.jpg",
    "barrot":        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Jean-No%C3%ABl_Barrot_%28cropped%29.jpg/200px-Jean-No%C3%ABl_Barrot_%28cropped%29.jpg",
    "rist":          "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/St%C3%A9phanie_Rist_%28cropped%29.jpg/200px-St%C3%A9phanie_Rist_%28cropped%29.jpg",
    "geffray":       "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Edouard_Geffray_2022.jpg/200px-Edouard_Geffray_2022.jpg",
    "amiel":         "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/David_Amiel_%28cropped%29.jpg/200px-David_Amiel_%28cropped%29.jpg",
    "tabarot":       "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Philippe_Tabarot_2022.jpg/200px-Philippe_Tabarot_2022.jpg",
    "ferrari":       "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Marina_Ferrari_%28cropped%29.jpg/200px-Marina_Ferrari_%28cropped%29.jpg",
    "berge":         "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Aurore_Berg%C3%A9_%28cropped%29.jpg/200px-Aurore_Berg%C3%A9_%28cropped%29.jpg",
    "bregeon":       "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Maud_Bregeon_2022.jpg/200px-Maud_Bregeon_2022.jpg",
    "baptiste":      "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Philippe_Baptiste_2021.jpg/200px-Philippe_Baptiste_2021.jpg",
    "papin":         "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Serge_Papin_2011.jpg/200px-Serge_Papin_2011.jpg",
    "gatel":         "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Fran%C3%A7oise_Gatel.jpg/200px-Fran%C3%A7oise_Gatel.jpg",
    "pegard":        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Catherine_P%C3%A9gard_%28Versailles%29.jpg/200px-Catherine_P%C3%A9gard_%28Versailles%29.jpg",
    "barbut":        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Monique_Barbut_2013.jpg/200px-Monique_Barbut_2013.jpg",
    "haddad":        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Benjamin_Haddad_%28cropped%29.jpg/200px-Benjamin_Haddad_%28cropped%29.jpg",
    "jeanbrun":      "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Vincent_Jeanbrun_%28cropped%29.jpg/200px-Vincent_Jeanbrun_%28cropped%29.jpg",
}

# ─────────────────────────────────────────────────────────────────────────────
# Logos partis : Wikipedia/Wikimedia Commons (libres de droits)
# ─────────────────────────────────────────────────────────────────────────────
LOGOS_PARTIS = {
    # Groupe Ensemble pour la République (anciennement Renaissance à l'AN)
    "ENS":   "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Logo_Renaissance_%28parti_politique_fran%C3%A7ais%29.svg/200px-Logo_Renaissance_%28parti_politique_fran%C3%A7ais%29.svg.png",
    "REN":   "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Logo_Renaissance_%28parti_politique_fran%C3%A7ais%29.svg/200px-Logo_Renaissance_%28parti_politique_fran%C3%A7ais%29.svg.png",
    "RN":    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Rassemblement_National_2018.svg/200px-Rassemblement_National_2018.svg.png",
    "LR":    "https://upload.wikimedia.org/wikipedia/fr/thumb/a/a9/Logo_Les_R%C3%A9publicains.svg/200px-Logo_Les_R%C3%A9publicains.svg.png",
    "HOR":   "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Horizons_%28parti_politique%29_logo.svg/200px-Horizons_%28parti_politique%29_logo.svg.png",
    "MODEM": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Logo_MoDem_2017.svg/200px-Logo_MoDem_2017.svg.png",
    "SOC":   "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Parti_socialiste_%28France%29_logo_2023.svg/200px-Parti_socialiste_%28France%29_logo_2023.svg.png",
    "ECO":   "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Logo_Les_%C3%89cologistes.svg/200px-Logo_Les_%C3%89cologistes.svg.png",
    "LFI":   "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/La_France_insoumise_%282022%29_Logo.svg/200px-La_France_insoumise_%282022%29_Logo.svg.png",
    "GDR":   "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Parti_communiste_fran%C3%A7ais_%28logo%2C_2018%29.svg/200px-Parti_communiste_fran%C3%A7ais_%28logo%2C_2018%29.svg.png",
    "LIOT":  "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Logo_LIOT.svg/200px-Logo_LIOT.svg.png",
    "NFP":   "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Logo_Nouveau_Front_Populaire.svg/200px-Logo_Nouveau_Front_Populaire.svg.png",
    # Droite républicaine (nouveau nom du groupe LR à l'AN depuis 2024)
    "DR":    "https://upload.wikimedia.org/wikipedia/fr/thumb/a/a9/Logo_Les_R%C3%A9publicains.svg/200px-Logo_Les_R%C3%A9publicains.svg.png",
}

COULEURS = {
    "RN":"#003189","NFP":"#8B0000","ENS":"#FF6D00","REN":"#FF6D00","MODEM":"#FF8F00",
    "HOR":"#1565C0","LR":"#0D47A1","DR":"#0D47A1","LFI":"#B71C1C","SOC":"#E91E63",
    "ECO":"#2E7D32","GDR":"#C62828","LIOT":"#6A1B9A","NI":"#607D8B",
}

# ─────────────────────────────────────────────────────────────────────────────
# Données partis (groupes parlementaires AN, XVIIe législature)
# ─────────────────────────────────────────────────────────────────────────────
PARTIS_DATA = {
    "RN": {
        "nom": "Rassemblement National", "nom_court": "RN", "couleur": "#003189",
        "description": "Premier groupe de l'Assemblée nationale avec 143 sièges, le RN est le parti de Marine Le Pen et Jordan Bardella. Fondé en 1972 sous le nom de Front National, il défend la priorité nationale, le contrôle de l'immigration et un euroscepticisme affirmé. Marine Le Pen a été condamnée en appel pour détournement de fonds européens, son inéligibilité de 5 ans confirmée début 2025.",
        "valeurs": ["Priorité nationale", "Souveraineté", "Sécurité", "Identité française", "Protection sociale"],
        "fondation": 1972, "orientation": "Droite nationaliste", "position_hemicycle": 1,
        "president": "Marine Le Pen / Jordan Bardella",
        "propositions_lois": [
            "Référendum constitutionnel sur l'immigration",
            "Suppression du droit du sol automatique",
            "Retraite à 60 ans pour les carrières longues",
            "Préférence nationale pour les aides sociales et l'emploi",
            "Sortie du commandement intégré de l'OTAN",
            "Rétablissement des frontières nationales",
        ],
        "actualites": [
            "Inéligibilité de 5 ans de Marine Le Pen confirmée en appel (mars 2025)",
            "Jordan Bardella prend la tête du groupe RN à l'Assemblée",
            "Le RN vote contre le gouvernement Lecornu mais évite la censure",
        ],
    },
    "ENS": {
        "nom": "Ensemble pour la République", "nom_court": "ENS", "couleur": "#FF6D00",
        "description": "Groupe parlementaire issu de Renaissance (ex-LREM), parti d'Emmanuel Macron fondé en 2016. Gabriel Attal en est le président à l'Assemblée. Le groupe soutient le gouvernement Lecornu sans y participer directement depuis le remaniement de février 2026.",
        "valeurs": ["Progrès", "Europe", "Réforme de l'État", "Innovation", "Économie de marché"],
        "fondation": 2016, "orientation": "Centre", "position_hemicycle": 4,
        "president": "Gabriel Attal (groupe AN)",
        "propositions_lois": [
            "Loi de finances 2026 — réduction du déficit public",
            "Réforme de l'assurance-chômage",
            "Loi industrie verte — décarbonation de l'économie",
            "France 2030 — investissements stratégiques",
            "Réforme du lycée professionnel",
        ],
        "actualites": [
            "Gabriel Attal appelle Macron à 'partager le pouvoir' (fin 2025)",
            "Ensemble soutient le gouvernement Lecornu tout en marquant son indépendance",
            "Le groupe perd des membres au profit d'Horizons",
        ],
    },
    "NFP": {
        "nom": "Nouveau Front Populaire", "nom_court": "NFP", "couleur": "#8B0000",
        "description": "Coalition de gauche formée pour les législatives de juin 2024, rassemblant LFI, PS, Les Écologistes et le PCF. Arrivée en tête en nombre de voix, elle n'a pas obtenu de majorité absolue. Le NFP est traversé de tensions internes entre LFI et les partis réformistes.",
        "valeurs": ["Justice sociale", "Planification écologique", "Abrogation réforme des retraites", "Services publics"],
        "fondation": 2024, "orientation": "Gauche", "position_hemicycle": 8,
        "president": "Coalition LFI / PS / Écolos / PCF",
        "propositions_lois": [
            "Abrogation de la réforme des retraites",
            "Blocage des prix des produits de première nécessité",
            "Taxation des superprofits et des milliardaires",
            "Plan de bifurcation écologique (100 Mds€)",
        ],
        "actualites": [
            "Le NFP a renversé Bayrou par un vote de confiance défavorable (8 sept. 2025)",
            "Tensions LFI/PS sur la stratégie face au gouvernement Lecornu",
            "Le PS et les Écolos refusent de voter une motion de censure contre Lecornu",
        ],
    },
    "DR": {
        "nom": "Droite Républicaine", "nom_court": "DR", "couleur": "#0D47A1",
        "description": "Le groupe Droite Républicaine (ex-LR) à l'Assemblée nationale est présidé par Laurent Wauquiez. Après la scission, plusieurs membres LR ont rejoint le gouvernement Lecornu malgré l'opposition du parti, entraînant leur suspension. Le groupe maintient une ligne de droite classique.",
        "valeurs": ["Liberté", "Autorité", "Sécurité", "Économie de marché", "Europe des nations"],
        "fondation": 2015, "orientation": "Droite", "position_hemicycle": 2,
        "president": "Laurent Wauquiez",
        "propositions_lois": [
            "Immigration — quotas annuels votés par le Parlement",
            "Justice — peines planchers généralisées",
            "Relance du nucléaire — 6 nouveaux EPR",
            "Équilibre budgétaire accéléré",
        ],
        "actualites": [
            "Scission : 6 ministres LR (Genevard, Tabarot…) suspendus du parti",
            "Wauquiez maintient LR dans l'opposition au gouvernement Lecornu",
            "LR rebaptisé 'Droite Républicaine' à l'Assemblée",
        ],
    },
    "MODEM": {
        "nom": "Mouvement Démocrate", "nom_court": "MoDem", "couleur": "#FF8F00",
        "description": "Parti centriste fondé par François Bayrou en 2007. Bayrou a été Premier ministre de décembre 2024 à septembre 2025 avant d'être renversé par un vote de confiance. Le MoDem reste un allié clé de la majorité présidentielle.",
        "valeurs": ["Humanisme", "Europe fédérale", "Démocratie", "Éducation", "Social-libéralisme"],
        "fondation": 2007, "orientation": "Centre", "position_hemicycle": 5,
        "president": "François Bayrou",
        "propositions_lois": [
            "Réforme du scrutin proportionnel",
            "Loi de programmation budgétaire pluriannuelle",
            "Autonomie renforcée des établissements scolaires",
        ],
        "actualites": [
            "Bayrou renversé par vote de confiance le 8 septembre 2025 (364 contre)",
            "Jean-Noël Barrot (MoDem) reconduit aux Affaires étrangères sous Lecornu",
            "Le MoDem pèse dans le soutien au gouvernement Lecornu",
        ],
    },
    "HOR": {
        "nom": "Horizons", "nom_court": "HOR", "couleur": "#1565C0",
        "description": "Parti centriste-libéral fondé par Édouard Philippe en 2021. Philippe, ancien Premier ministre, est officiellement candidat à la présidentielle 2027. Il a appelé Macron à démissionner après le vote du budget 2026.",
        "valeurs": ["Pragmatisme", "Territoires", "Décentralisation", "Réforme"],
        "fondation": 2021, "orientation": "Centre droit", "position_hemicycle": 3,
        "president": "Édouard Philippe",
        "propositions_lois": [
            "Acte III de la décentralisation",
            "Simplification administrative pour les collectivités",
            "Réforme de la fiscalité locale",
        ],
        "actualites": [
            "Édouard Philippe appelle Macron à démissionner après le budget (déc. 2025)",
            "Philippe officiellement candidat à la présidentielle 2027",
            "Horizons renforce son implantation aux municipales 2026",
        ],
    },
    "LFI": {
        "nom": "La France Insoumise", "nom_court": "LFI", "couleur": "#B71C1C",
        "description": "Mouvement de gauche radicale fondé par Jean-Luc Mélenchon en 2016. Première force du NFP en nombre de députés. Mélenchon a annoncé ne pas être candidat à la présidentielle 2027. Mathilde Panot dirige le groupe à l'Assemblée.",
        "valeurs": ["VIe République", "Planification écologique", "Justice fiscale", "Paix", "Souveraineté populaire"],
        "fondation": 2016, "orientation": "Gauche radicale", "position_hemicycle": 9,
        "president": "Jean-Luc Mélenchon",
        "propositions_lois": [
            "VIe République — Assemblée constituante",
            "Retraite à 60 ans — abrogation immédiate",
            "Salaire maximum légal (20× le SMIC)",
            "Sortie du commandement de l'OTAN",
            "100% énergies renouvelables d'ici 2040",
        ],
        "actualites": [
            "LFI a conduit le NFP à renverser Bayrou (sept. 2025)",
            "Mélenchon annonce ne pas se présenter à la présidentielle 2027",
            "Tensions avec le PS sur la stratégie face au gouvernement Lecornu",
        ],
    },
    "SOC": {
        "nom": "Socialistes et Apparentés", "nom_court": "PS", "couleur": "#E91E63",
        "description": "Le Parti Socialiste, fondé en 1969, se redresse dans le cadre du NFP. Le PS a refusé de voter la motion de censure contre Lecornu en octobre 2025, obtenant la suspension de la réforme des retraites jusqu'en 2027.",
        "valeurs": ["Justice sociale", "Solidarité", "Europe sociale", "Laïcité"],
        "fondation": 1969, "orientation": "Gauche", "position_hemicycle": 7,
        "president": "Olivier Faure",
        "propositions_lois": [
            "Abrogation de la réforme des retraites",
            "Réforme de la fiscalité successorale",
            "Loi sur le logement social d'urgence",
        ],
        "actualites": [
            "Le PS obtient la suspension de la réforme des retraites jusqu'en 2027",
            "Tensions LFI/PS : le PS refuse de voter la motion de censure contre Lecornu",
            "Résultats positifs aux élections municipales 2026",
        ],
    },
    "ECO": {
        "nom": "Les Écologistes", "nom_court": "Écolos", "couleur": "#2E7D32",
        "description": "Les Écologistes (ex-EELV), membres du NFP, défendent la transition écologique. Ils s'opposent à la relance nucléaire du gouvernement Lecornu et à la politique d'expulsions locatives record de 2025.",
        "valeurs": ["Transition écologique", "Féminisme", "Non-violence", "Droits des minorités"],
        "fondation": 2010, "orientation": "Gauche écologiste", "position_hemicycle": 6,
        "president": "Marine Tondelier",
        "propositions_lois": [
            "100% renouvelables d'ici 2035 — abandon du nucléaire",
            "Interdiction des pesticides de synthèse d'ici 2030",
            "Revenu de base universel (900€/mois)",
            "Réduction du temps de travail à 32h",
        ],
        "actualites": [
            "Les Écolos s'opposent à la relance nucléaire du gouvernement",
            "Marine Tondelier, figure montante de la gauche en vue de 2027",
            "Record d'expulsions locatives 2025 : les Écolos en première ligne",
        ],
    },
    "GDR": {
        "nom": "Gauche Démocrate et Républicaine", "nom_court": "GDR", "couleur": "#C62828",
        "description": "Le groupe GDR rassemble les députés communistes et ultramarins de gauche. Membre du NFP, il maintient ses distances avec LFI sur les questions géopolitiques.",
        "valeurs": ["Services publics", "Paix", "Droits des travailleurs", "Outre-mer"],
        "fondation": 1920, "orientation": "Gauche", "position_hemicycle": 10,
        "president": "André Chassaigne",
        "propositions_lois": [
            "Nationalisation des autoroutes",
            "Loi sur la réquisition des logements vides",
            "Loi cadre sur les droits des Outre-mer",
        ],
        "actualites": [
            "Le PCF marque ses distances avec LFI sur les questions géopolitiques",
            "Campagne nationale pour la nationalisation des autoroutes",
            "André Chassaigne reconduit à la tête du groupe GDR",
        ],
    },
    "LIOT": {
        "nom": "Libertés, Indépendants, Outre-mer et Territoires", "nom_court": "LIOT", "couleur": "#6A1B9A",
        "description": "Groupe transpartisan attaché à l'indépendance et aux territoires. LIOT a joué un rôle clé en s'abstenant lors de la motion de censure contre Lecornu en octobre 2025, permettant au gouvernement de survivre.",
        "valeurs": ["Indépendance", "Territoires", "Outre-mer", "Pragmatisme"],
        "fondation": 2022, "orientation": "Centre / Divers", "position_hemicycle": 5,
        "president": "Bertrand Pancher",
        "propositions_lois": [
            "Autonomie renforcée des collectivités d'Outre-mer",
            "Réforme du financement des communes rurales",
            "Loi contre les déserts médicaux",
        ],
        "actualites": [
            "LIOT s'abstient sur la motion de censure contre Lecornu (oct. 2025)",
            "Le groupe maintient sa ligne d'indépendance — vote au cas par cas",
            "Mobilisation sur la crise budgétaire des Outre-mer",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Gouvernement Lecornu II — composition au 26 février 2026 (remaniement)
# Source : info.gouv.fr / vie-publique.fr / Journal officiel
# ─────────────────────────────────────────────────────────────────────────────
GOUVERNEMENT = [
    # ── PRÉSIDENT ──
    {"nom":"Macron",    "prenom":"Emmanuel",  "role":"Président de la République",
     "parti":"ENS",  "rang":0, "photo_key":"macron",
     "description":"Élu en 2017, réélu en 2022. Fondateur de Renaissance (ex-LREM). Président de la République en exercice depuis mai 2017."},
    # ── PREMIER MINISTRE ──
    {"nom":"Lecornu",   "prenom":"Sébastien", "role":"Premier ministre — chargé de la Planification écologique",
     "parti":"ENS",  "rang":1, "photo_key":"lecornu",
     "description":"Nommé Premier ministre le 9 septembre 2025 après la démission de Bayrou. Ancien ministre des Armées (2022-2025). Gouvernement remanié le 26 février 2026."},
    # ── MINISTRES DE PLEIN EXERCICE ──
    {"nom":"Nuñez",     "prenom":"Laurent",   "role":"Ministre de l'Intérieur",
     "parti":"ENS",  "rang":2, "photo_key":"nunez",
     "description":"Ancien préfet de police de Paris. Reconduit à l'Intérieur depuis le gouvernement Lecornu I."},
    {"nom":"Vautrin",   "prenom":"Catherine", "role":"Ministre des Armées et des Anciens combattants",
     "parti":"HOR",  "rang":3, "photo_key":"vautrin",
     "description":"Ancienne présidente de la région Grand Est. Nommée aux Armées en remplacement de Lecornu, devenu Premier ministre."},
    {"nom":"Farandou",  "prenom":"Jean-Pierre","role":"Ministre du Travail et des Solidarités",
     "parti":"ENS",  "rang":4, "photo_key":"farandou",
     "description":"Ancien PDG de la SNCF (2019-2024). Première entrée en politique."},
    {"nom":"Barbut",    "prenom":"Monique",   "role":"Ministre de la Transition écologique et de la Biodiversité",
     "parti":"ENS",  "rang":5, "photo_key":"barbut",
     "description":"Ancienne directrice de la Convention des Nations Unies sur la lutte contre la désertification."},
    {"nom":"Darmanin",  "prenom":"Gérald",    "role":"Garde des Sceaux, ministre de la Justice",
     "parti":"NI",   "rang":6, "photo_key":"darmanin",
     "description":"A quitté Renaissance en octobre 2025 pour être au gouvernement. Ancien ministre de l'Intérieur (2020-2024)."},
    {"nom":"Lescure",   "prenom":"Roland",    "role":"Ministre de l'Économie, des Finances et de la Souveraineté industrielle",
     "parti":"ENS",  "rang":7, "photo_key":"lescure",
     "description":"Ancien député Renaissance du Canada. Remplace Éric Lombard à l'Économie."},
    {"nom":"Papin",     "prenom":"Serge",     "role":"Ministre des PME, Commerce, Artisanat, Tourisme et Pouvoir d'achat",
     "parti":"NI",   "rang":8, "photo_key":"papin",
     "description":"Ancien PDG de Système U (2005-2017). Première nomination au gouvernement."},
    {"nom":"Genevard",  "prenom":"Annie",     "role":"Ministre de l'Agriculture et de la Souveraineté alimentaire",
     "parti":"LR",   "rang":9, "photo_key":"genevard",
     "description":"Ancienne présidente du groupe LR à l'AN. Suspendue de LR pour avoir rejoint le gouvernement."},
    {"nom":"Geffray",   "prenom":"Édouard",   "role":"Ministre de l'Éducation nationale",
     "parti":"NI",   "rang":10,"photo_key":"geffray",
     "description":"Ancien directeur général de l'enseignement scolaire. Première nomination au gouvernement."},
    {"nom":"Barrot",    "prenom":"Jean-Noël", "role":"Ministre de l'Europe et des Affaires étrangères",
     "parti":"MODEM","rang":11,"photo_key":"barrot",
     "description":"Reconduit aux Affaires étrangères depuis le gouvernement Bayrou. Fils du commissaire européen Jacques Barrot."},
    {"nom":"Rist",      "prenom":"Stéphanie", "role":"Ministre de la Santé et des Familles",
     "parti":"ENS",  "rang":12,"photo_key":"rist",
     "description":"Médecin de formation, ancienne rapporteure générale du budget de la Sécu. Reconduite à la Santé."},
    {"nom":"Pégard",    "prenom":"Catherine", "role":"Ministre de la Culture",
     "parti":"NI",   "rang":13,"photo_key":"pegard",
     "description":"Ancienne présidente du château de Versailles et conseillère culture d'Emmanuel Macron. Remplace Rachida Dati (démissionnée le 25 fév. 2026 pour les municipales à Paris)."},
    {"nom":"Gatel",     "prenom":"Françoise", "role":"Ministre de l'Aménagement du territoire et de la Décentralisation",
     "parti":"NI",   "rang":14,"photo_key":"gatel",
     "description":"Ancienne sénatrice UDI d'Ille-et-Vilaine. Assure la représentation de l'UDI au gouvernement."},
    {"nom":"Amiel",     "prenom":"David",     "role":"Ministre de l'Action et des Comptes publics",
     "parti":"ENS",  "rang":15,"photo_key":"amiel",
     "description":"Fidèle historique de Macron. Promu du rang de délégué à ministre de plein exercice le 26 fév. 2026, remplaçant Montchalin partie à la Cour des comptes."},
    {"nom":"Baptiste",  "prenom":"Philippe",  "role":"Ministre de l'Enseignement supérieur, Recherche et Espace",
     "parti":"NI",   "rang":16,"photo_key":"baptiste",
     "description":"Ancien directeur général du CNRS. Reconduit à l'Enseignement supérieur."},
    {"nom":"Ferrari",   "prenom":"Marina",   "role":"Ministre des Sports, Jeunesse et Vie associative",
     "parti":"ENS",  "rang":17,"photo_key":"ferrari",
     "description":"Ancienne députée ENS de Savoie. Reconduite aux Sports."},
    {"nom":"Tabarot",   "prenom":"Philippe",  "role":"Ministre des Transports",
     "parti":"LR",   "rang":18,"photo_key":"tabarot",
     "description":"Ancien sénateur LR des Alpes-Maritimes. Suspendu de LR pour avoir rejoint le gouvernement."},
    {"nom":"Jeanbrun",  "prenom":"Vincent",   "role":"Ministre de la Ville et du Logement",
     "parti":"LR",   "rang":19,"photo_key":"jeanbrun",
     "description":"Maire de L'Haÿ-les-Roses. Suspendu de LR pour avoir rejoint le gouvernement."},
    # ── MINISTRES DÉLÉGUÉS CLÉS ──
    {"nom":"Bergé",     "prenom":"Aurore",    "role":"Ministre déléguée — Égalité femmes-hommes",
     "parti":"ENS",  "rang":20,"photo_key":"berge",
     "description":"Ancienne présidente du groupe Renaissance à l'AN."},
    {"nom":"Bregeon",   "prenom":"Maud",      "role":"Porte-parole du Gouvernement — Énergie",
     "parti":"ENS",  "rang":21,"photo_key":"bregeon",
     "description":"Porte-parole du gouvernement. Également chargée de l'Énergie auprès du ministre de l'Économie."},
    {"nom":"Haddad",    "prenom":"Benjamin",  "role":"Ministre délégué — Europe",
     "parti":"ENS",  "rang":22,"photo_key":"haddad",
     "description":"Ancien directeur de l'Institut Hudson à Washington. Chargé de l'Europe auprès de Barrot."},
]

# ─────────────────────────────────────────────────────────────────────────────
# Proxies
# ─────────────────────────────────────────────────────────────────────────────
WP_HEADERS = {
    "User-Agent": "LuminBot/1.0 (https://github.com/lumin; contact@lumin.fr) Python/httpx",
    "Accept": "image/webp,image/png,image/*,*/*",
}

@app.get("/proxy/logo/{parti_id}")
async def proxy_logo(parti_id: str):
    url = LOGOS_PARTIS.get(parti_id.upper())
    if not url:
        return JSONResponse(status_code=404, content={"detail": "Logo non disponible"})
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(url, headers=WP_HEADERS)
            ct = r.headers.get("content-type", "image/png")
            if r.status_code == 200 and "image" in ct and len(r.content) > 500:
                return Response(content=r.content, media_type=ct,
                    headers={"Cache-Control": "public, max-age=2592000"})
    except Exception:
        pass
    return JSONResponse(status_code=404, content={"detail": "Logo non disponible"})

@app.get("/proxy/ministre/{key}")
async def proxy_ministre_photo(key: str):
    url = PHOTOS_MINISTRES.get(key.lower())
    if not url:
        return JSONResponse(status_code=404, content={"detail": "Photo non disponible"})
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(url, headers=WP_HEADERS)
            ct = r.headers.get("content-type", "image/jpeg")
            if r.status_code == 200 and "image" in ct and len(r.content) > 500:
                return Response(content=r.content, media_type=ct,
                    headers={"Cache-Control": "public, max-age=2592000"})
    except Exception:
        pass
    return JSONResponse(status_code=404, content={"detail": "Photo non disponible"})

@app.get("/proxy/portrait/{depute_id}")
async def proxy_portrait(depute_id: str, slug: str = Query(default=""), db: Session = Depends(get_db)):
    if not slug:
        depute = db.query(Depute).filter(Depute.id == depute_id).first()
        if depute and depute.slug:
            slug = depute.slug
    urls = []
    if slug:
        urls.append(f"https://www.nosdeputes.fr/depute/photo/{slug}")
    numeric = depute_id.replace("PA","").replace("pa","")
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
                ct = r.headers.get("content-type","")
                if r.status_code == 200 and "image" in ct and len(r.content) > 2000:
                    return Response(content=r.content, media_type=ct,
                        headers={"Cache-Control":"public, max-age=604800"})
            except Exception:
                continue
        for url in an_urls:
            try:
                r = await client.get(url, headers=an_headers)
                ct = r.headers.get("content-type","")
                if r.status_code == 200 and "image" in ct and len(r.content) > 2000:
                    return Response(content=r.content, media_type=ct,
                        headers={"Cache-Control":"public, max-age=604800"})
            except Exception:
                continue
    return JSONResponse(status_code=404, content={"detail": "Portrait non disponible"})

# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
def _fmt_depute(d: Depute) -> dict:
    slug_param = f"?slug={d.slug}" if d.slug else ""
    return {
        "id": d.id, "prenom": d.prenom, "nom": d.nom,
        "groupe": d.groupe, "circonscription": d.circonscription, "slug": d.slug,
        "photo_url": f"http://localhost:8000/proxy/portrait/{d.id}{slug_param}",
        "url_nosdeputes": getattr(d, "url_nosdeputes", None),
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
        return JSONResponse(status_code=404, content={"detail":"Introuvable"})
    return _fmt_depute(d)

@app.get("/partis")
def get_partis(db: Session = Depends(get_db)):
    counts = dict(db.query(Depute.groupe, func.count(Depute.id)).group_by(Depute.groupe).all())
    result = []
    for code, data in PARTIS_DATA.items():
        nb = counts.get(code, 0)
        if code == "NFP":
            nb = counts.get("LFI",0)+counts.get("SOC",0)+counts.get("ECO",0)+counts.get("GDR",0)
        elif code == "DR":
            nb = counts.get("LR",0)+counts.get("DR",0)
        result.append({"id":code,"slug":code.lower(),**data,"nb_sieges":nb})
    return sorted(result, key=lambda x: x["nb_sieges"], reverse=True)

@app.get("/partis/{slug}")
def get_parti(slug: str, db: Session = Depends(get_db)):
    code = slug.upper()
    # Alias : "lr" → "DR" (Droite Républicaine), "ens"→"ENS"
    aliases = {"LR":"DR","RENAISSANCE":"ENS","RE":"ENS"}
    code = aliases.get(code, code)
    if code not in PARTIS_DATA:
        return JSONResponse(status_code=404, content={"detail":"Parti introuvable"})
    data = PARTIS_DATA[code]
    codes_groupe = [code]
    if code == "NFP": codes_groupe = ["LFI","SOC","ECO","GDR"]
    if code == "DR":  codes_groupe = ["LR","DR"]
    deputes = db.query(Depute).filter(Depute.groupe.in_(codes_groupe)).order_by(Depute.nom).all()
    return {"id":code,"slug":slug,**data,"nb_sieges":len(deputes),"deputes":[_fmt_depute(d) for d in deputes]}

@app.get("/gouvernement")
def get_gouvernement():
    return [
        {**m,
         "couleur": COULEURS.get(m["parti"],"#607D8B"),
         "initiales": (m["prenom"][0] if m["prenom"] else "")+(m["nom"][0] if m["nom"] else ""),
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
        "by_groupe": [{"groupe":g,"count":c,"couleur":COULEURS.get(g,"#888")} for g,c in by_groupe],
    }