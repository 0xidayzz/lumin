from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx

app = FastAPI(title="Lumin API")
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    # Le scheduler lancera la récolte automatiquement toutes les 12h
    from fetch_deputes import récolte
    scheduler.add_job(récolte, 'interval', hours=12)
    scheduler.start()
    print("🚀 Lumin est autonome et surveille l'Assemblée.")

@app.get("/")
async def root():
    return {"message": "Lumin Backend Operationnel"}