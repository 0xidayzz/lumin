# 🔦 Lumin : La Vigie de l'Hémicycle

> **Rendre la démocratie accessible à tous grâce à l'IA.**

Lumin est une plateforme open source autonome conçue pour ingérer, analyser et vulgariser l'intégralité des débats et textes de lois de l'Assemblée Nationale française. 

La démocratie produit des millions de mots, mais personne n'a le temps de tous les lire. L'objectif de Lumin est de transformer cette montagne d'informations brutes en une source de savoir claire, organisée et accessible pour les citoyens, les journalistes et les professionnels de la politique.

## 🏛️ Le Concept : Le parcours de l'information

1. **La Récolte :** Ingestion automatique des comptes rendus via l'API Open Data de l'Assemblée Nationale.
2. **Le Nettoyage :** Filtrage du "bruit" parlementaire (formules de politesse, rappels au règlement) pour isoler la substance politique.
3. **L'Intelligence :** Analyse par LLM (Claude API) pour extraire le sujet, la position des élus, et générer des résumés en 3 points. Simplification des textes de lois juridiques en langage clair via un LLM local (Ollama/Mistral).
4. **La Mémoire :** Vectorisation et stockage pour permettre une recherche sémantique puissante ("Qu'a dit ce ministre sur l'eau ces deux dernières années ?").

## 🛠️ Stack Technique

Lumin est pensé pour être robuste, rapide et hébergeable avec une infrastructure maîtrisée.

* **Frontend :** Next.js 14 (App Router), React, Tailwind CSS
* **Backend :** Python 3.12, FastAPI
* **Base de données :** PostgreSQL avec l'extension `pgvector` pour la recherche sémantique
* **Intelligence Artificielle :**
  * **Analyse sémantique complexe :** API Anthropic (Claude 3.5 Sonnet)
  * **Vulgarisation de textes (Local) :** Ollama (Modèle Mistral 7B)
  * **Embeddings (Local) :** Ollama (Modèle nomic-embed-text)
* **Conteneurisation :** Docker & Docker Compose

## 🚀 Prérequis (Développement Local)

L'environnement de développement a été pensé et optimisé pour **macOS (Apple Silicon - M1/M2/M3/M4/M5)**.

* [Homebrew](https://brew.sh/)
* Python 3.12 (via `pyenv`)
* Node.js 20 (via `nvm`)
* [Docker Desktop pour Mac (Apple Silicon)](https://www.docker.com/products/docker-desktop)
* [Ollama](https://ollama.com/) avec les modèles téléchargés :
  ```bash
  ollama pull mistral
  ollama pull nomic-embed-text