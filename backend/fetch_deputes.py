import httpx
import asyncio
from db import SessionLocal, engine, Base
from models import Depute

Base.metadata.create_all(bind=engine)

async def récolte():
    url = "https://data.assemblee-nationale.fr/api/v2/acteurs?legislature=17"
    print("🛰️ Connexion à l'Assemblée Nationale...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        data = response.json()
        db = SessionLocal()
        
        for item in data.get("items", []):
            depute = Depute(
                id=item["uid"],
                prenom=item["prenom"],
                nom=item["nom"],
                groupe=item.get("groupeAbreviation", "N/A")
            )
            db.merge(depute)
        
        db.commit()
        db.close()
        print("✅ Base de données mise à jour !")

if __name__ == "__main__":
    asyncio.run(récolte())