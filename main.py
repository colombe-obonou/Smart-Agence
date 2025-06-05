from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
from datetime import date

import Model, schemas, crud

# Configuration de la base de données
SQLALCHEMY_DATABASE_URL = "sqlite:///./agence_tickets.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Créer les tables
Model.Base.metadata.create_all(bind=engine)

# Initialisation de l'application FastAPI
app = FastAPI(
    title="API Gestion Agence Tickets",
    description="API pour gérer les agents, tickets et événements d'une agence",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dépendance pour obtenir la session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ ENDPOINTS AGENTS ============

@app.post("/agents/", response_model=schemas.Agent, status_code=status.HTTP_201_CREATED)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    """Créer un nouvel agent"""
    # Vérifier si l'email existe déjà
    db_agent = crud.get_agent_by_email(db, email=agent.Email)
    if db_agent:
        raise HTTPException(
            status_code=400,
            detail="Un agent avec cet email existe déjà"
        )
    return crud.create_agent(db=db, agent=agent)


@app.get("/agents/", response_model=List[schemas.Agent])
def read_agents(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    categorie: Optional[str] = Query(None, description="Filtrer par catégorie (transaction/conseil)"),
    search: Optional[str] = Query(None, description="Rechercher dans nom, prénoms ou email"),
    db: Session = Depends(get_db)
):
    """Récupérer la liste des agents avec filtres optionnels"""
    agents = crud.get_agents(
        db, 
        skip=skip, 
        limit=limit, 
        categorie=categorie, 
        search=search
    )
    return agents


@app.get("/agents/{agent_id}", response_model=schemas.Agent)
def read_agent(agent_id: int, db: Session = Depends(get_db)):
    """Récupérer un agent par son ID"""
    db_agent = crud.get_agent(db, agent_id=agent_id)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return db_agent


@app.put("/agents/{agent_id}", response_model=schemas.Agent)
def update_agent(
    agent_id: int, 
    agent_update: schemas.AgentUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour un agent"""
    db_agent = crud.update_agent(db, agent_id=agent_id, agent_update=agent_update)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return db_agent


@app.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """Supprimer un agent"""
    success = crud.delete_agent(db, agent_id=agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return None


@app.get("/agents/{agent_id}/tickets", response_model=List[schemas.Ticket])
def read_agent_tickets(
    agent_id: int, 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Récupérer tous les tickets d'un agent"""
    # Vérifier que l'agent existe
    agent = crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    
    tickets = crud.get_tickets(db, skip=skip, limit=limit, agent_id=agent_id)
    return tickets


@app.get("/agents/{agent_id}/statistics")
def read_agent_statistics(agent_id: int, db: Session = Depends(get_db)):
    """Récupérer les statistiques d'un agent"""
    stats = crud.get_agent_statistics(db, agent_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return stats


# ============ ENDPOINTS TICKETS ============

@app.post("/tickets/", response_model=schemas.Ticket, status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    """Créer un nouveau ticket"""
    try:
        return crud.create_ticket(db=db, ticket=ticket)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tickets/", response_model=List[schemas.Ticket])
def read_tickets(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    categorie: Optional[str] = Query(None, description="Filtrer par catégorie de service"),
    agent_id: Optional[int] = Query(None, description="Filtrer par ID agent"),
    date_debut: Optional[date] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_fin: Optional[date] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    statut: Optional[str] = Query(None, description="Filtrer par statut"),
    db: Session = Depends(get_db)
):
    """Récupérer la liste des tickets avec filtres optionnels"""
    tickets = crud.get_tickets(
        db, 
        skip=skip, 
        limit=limit,
        categorie=categorie,
        agent_id=agent_id,
        date_debut=date_debut,
        date_fin=date_fin,
        statut=statut
    )
    return tickets


@app.get("/tickets/{ticket_id}", response_model=schemas.Ticket)
def read_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Récupérer un ticket par son ID"""
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return db_ticket


@app.put("/tickets/{ticket_id}", response_model=schemas.Ticket)
def update_ticket(
    ticket_id: int, 
    ticket_update: schemas.TicketUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour les détails d'un ticket"""
    db_ticket = crud.update_ticket(db, ticket_id=ticket_id, ticket_update=ticket_update)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return db_ticket


@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Supprimer un ticket"""
    success = crud.delete_ticket(db, ticket_id=ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return None


@app.post("/tickets/{ticket_id}/status", response_model=schemas.EventTicket, status_code=status.HTTP_201_CREATED)
def update_ticket_status(
    ticket_id: int,
    status_update: schemas.EventTicketCreate,
    db: Session = Depends(get_db)
):
    """Mettre à jour le statut d'un ticket (créer un nouvel événement)"""
    try:
        # Utiliser l'agent_id du body de la requête
        event = crud.update_ticket_status(
            db=db, 
            ticket_id=ticket_id, 
            agent_id=status_update.Agent_id,
            nouveau_statut=status_update.statut
        )
        return event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tickets/{ticket_id}/status")
def read_ticket_current_status(ticket_id: int, db: Session = Depends(get_db)):
    """Récupérer le statut actuel d'un ticket"""
    # Vérifier que le ticket existe
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    statut = crud.get_ticket_current_status(db, ticket_id)
    return {
        "ticket_id": ticket_id,
        "statut_actuel": statut.value if statut else None,
        "timestamp": "current"
    }


@app.get("/tickets/{ticket_id}/events", response_model=List[schemas.EventTicket])
def read_ticket_events(ticket_id: int, db: Session = Depends(get_db)):
    """Récupérer l'historique des événements d'un ticket"""
    # Vérifier que le ticket existe
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    events = crud.get_ticket_events(db, ticket_id)
    return events


# ============ ENDPOINTS STATISTIQUES ============

@app.get("/statistics/global")
def read_global_statistics(db: Session = Depends(get_db)):
    """Récupérer les statistiques globales de l'agence"""
    return crud.get_global_statistics(db)


# ============ ENDPOINTS UTILITAIRES ============

@app.get("/health")
def health_check():
    """Vérification de l'état de l'API"""
    return {"status": "healthy", "message": "API Gestion Agence Tickets opérationnelle"}


@app.get("/")
def root():
    """Point d'entrée racine de l'API"""
    return {
        "message": "Bienvenue sur l'API Gestion Agence Tickets",
        "version": "1.0.0",
        "documentation": "/docs"
    }


# ============ GESTION DES ERREURS GLOBALES ============

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Gestionnaire d'erreur pour ValueError"""
    return HTTPException(status_code=400, detail=str(exc))


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Gestionnaire d'erreur général"""
    return HTTPException(
        status_code=500, 
        detail="Erreur interne du serveur"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)