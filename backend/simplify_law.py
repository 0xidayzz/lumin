import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"

async def simplifier_texte_loi(texte_juridique: str):
    prompt = f"""
    Tu es un expert en vulgarisation juridique. 
    Réécris l'article de loi suivant en langage simple, clair et accessible à un citoyen.
    Garde l'essentiel, utilise des listes à puces si besoin.
    
    ARTICLE : {texte_juridique}
    
    VERSION SIMPLIFIÉE :
    """
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(OLLAMA_URL, json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            })
            return response.json().get("response")
        except Exception as e:
            return f"Erreur avec Ollama : {str(e)}"

if __name__ == "__main__":
    import asyncio
    test_loi = "L'article L. 123-1 du code de commerce est complété par un alinéa ainsi rédigé..."
    print(asyncio.run(simplifier_texte_loi(test_loi)))