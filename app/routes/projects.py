# app/routes/projects.py

from fastapi import APIRouter, Depends, HTTPException # Added HTTPException just in case
# from sqlalchemy.orm import Session # <-- REMOVE
# Import schemas and async crud functions
from app import crud, schemas, models # Assuming schemas.Project/ProjectCreate exist
# from app.database import get_db # <-- REMOVE
from typing import List # Added for response model

router = APIRouter(
    prefix="/projects", # Added prefix for consistency
    tags=["projects"]   # Added tags for consistency
)

# --- Make routes async, remove db dependency, await crud calls ---

@router.post("/", response_model=schemas.Project) # Assuming schemas.Project exists
async def create_project(project: schemas.ProjectCreate): # <-- async def, removed db, assuming schemas.ProjectCreate exists
    # Assuming crud.create_project is now async and takes only 'project'
    # Also assuming it handles potential errors and might return None or raise
    created_project = await crud.create_project(project=project) # <-- await
    if not created_project:
        # Handle potential creation error (e.g., duplicate name?)
        raise HTTPException(status_code=400, detail="Project could not be created.")
    return created_project

@router.get("/", response_model=List[schemas.Project]) # Assuming schemas.Project exists
async def read_projects(skip: int = 0, limit: int = 10): # <-- async def, removed db
    # Assuming crud.get_projects is now async and takes only skip/limit
    projects = await crud.get_projects(skip=skip, limit=limit) # <-- await
    return projects