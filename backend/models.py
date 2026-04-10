from sqlalchemy import Column, String, Integer
from db import Base

class Depute(Base):
    __tablename__ = "deputes"
    id             = Column(String, primary_key=True)   # ex: PA719318
    prenom         = Column(String, nullable=False)
    nom            = Column(String, nullable=False)
    groupe         = Column(String, nullable=True)
    circonscription= Column(String, nullable=True)
    slug           = Column(String, nullable=True)       # ex: marine-le-pen (nosdeputes)
    url_nosdeputes = Column(String, nullable=True)       # ex: https://nosdeputes.fr/marine-le-pen