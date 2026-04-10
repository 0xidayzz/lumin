from sqlalchemy import Column, String, Integer
from db import Base

class Depute(Base):
    __tablename__ = "deputes"
    id = Column(String, primary_key=True, index=True)
    prenom = Column(String)
    nom = Column(String)
    groupe = Column(String)
    circonscription = Column(String)