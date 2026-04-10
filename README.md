# 🔦 Lumin : La Vigie de l'Hémicycle

> **L'IA au service de la transparence parlementaire.**

Lumin est une plateforme open source autonome conçue pour ingérer, analyser et vulgariser l'intégralité des débats et textes de lois de l'Assemblée Nationale française. 

---

## 🏛️ La Mission
La démocratie produit des millions de mots, mais la complexité du langage législatif crée une barrière entre les citoyens et leurs représentants. Lumin transforme cette montagne d'informations brutes en une source de savoir claire, organisée et accessible.

### 🔄 Le Cycle de l'Information
* **📡 Récolte :** Ingestion automatique via l'API Open Data de l'Assemblée Nationale.
* **🧼 Raffinement :** Filtrage automatique du "bruit" parlementaire (procédure, politesse).
* **🧠 Analyse IA :** Extraction des positions politiques via **Claude 3.5** et vulgarisation en langage clair via **Mistral (Local)**.
* **🔍 Mémoire Vectorielle :** Recherche sémantique avancée ("Quels députés ont parlé de la gestion de l'eau ?").

---

## 🛠️ Stack Technique

| Composant | Technologie |
| :--- | :--- |
| **Frontend** | Next.js 14, Tailwind CSS, Shadcn/UI |
| **Backend** | Python 3.12, FastAPI |
| **Base de données** | PostgreSQL + `pgvector` |
| **IA (Cloud)** | Anthropic Claude 3.5 Sonnet |
| **IA (Local)** | Ollama (Mistral 7B + Nomic Embeddings) |
| **Infrastructure** | Docker & Docker Compose |

---

## 🚀 Installation Rapide (macOS Apple Silicon)

### 1. Prérequis
Assurez-vous d'avoir installé :
* [Docker Desktop](https://www.docker.com/products/docker-desktop)
* [Ollama](https://ollama.com/)
* Python 3.12+ & Node.js 20+

### 2. Configuration Ollama
```bash
ollama pull mistral
ollama pull nomic-embed-text