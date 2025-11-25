from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, crud, auth, llm_client, exporter
from .database import engine, Base, get_db
from fastapi import status
from dotenv import load_dotenv
import os

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title='AI Document Authoring')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth.decode_token(token)
    user = db.query(models.User).filter(models.User.id == payload.get('sub')).first()
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    return user


@app.post('/auth/register', status_code=201)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    user = crud.create_user(db, user_in.email, user_in.password)
    token = auth.create_access_token({'sub': user.id})
    return {'access_token': token, 'token_type': 'bearer'}


@app.post('/auth/login')
def login(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, user_in.email)
    if not user or not auth.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = auth.create_access_token({'sub': user.id})
    return {'access_token': token, 'token_type': 'bearer'}


@app.post('/projects', response_model=schemas.ProjectOut)
def create_project(project_in: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    proj = crud.create_project(db, current_user.id, project_in)
    return proj


@app.get('/projects')
def list_projects(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    projects = crud.get_projects_for_user(db, current_user.id)
    return projects


@app.get('/projects/{project_id}')
def get_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    proj = crud.get_project(db, project_id, current_user.id)
    if not proj:
        raise HTTPException(status_code=404, detail='Project not found')
    return proj


@app.post('/projects/{project_id}/generate')
def generate_content(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    proj = crud.get_project(db, project_id, current_user.id)
    if not proj:
        raise HTTPException(status_code=404, detail='Project not found')
    # Generate for each section sequentially
    for sec in proj.sections:
        prompt = f"Write content for section titled '{sec.title}' about: {proj.prompt or ''}"
        text = llm_client.generate_for_section(prompt)
        crud.update_section_content(db, sec.id, text)
    return {'status': 'generated'}


@app.post('/refine')
def refine(ref_in: schemas.RefinementCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    sec = db.query(models.Section).filter(models.Section.id == ref_in.section_id).first()
    if not sec:
        raise HTTPException(status_code=404, detail='Section not found')
    # run LLM for refinement scoped to that section
    prompt = f"Refine the following section content with instructions: {ref_in.prompt}\nCurrent content:\n{sec.content}" 
    new_text = llm_client.generate_for_section(prompt)
    r = crud.create_refinement(db, sec.id, current_user.id, ref_in.prompt, new_text)
    return {'refinement_id': r.id, 'new_content': new_text}


@app.post('/comment')
def comment(c_in: schemas.CommentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    sec = db.query(models.Section).filter(models.Section.id == c_in.section_id).first()
    if not sec:
        raise HTTPException(status_code=404, detail='Section not found')
    c = crud.add_comment(db, sec.id, current_user.id, c_in.text)
    return c


@app.get('/export/{project_id}')
def export_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    proj = crud.get_project(db, project_id, current_user.id)
    if not proj:
        raise HTTPException(status_code=404, detail='Project not found')
    sections = proj.sections
    if proj.doc_type == 'docx':
        bio = exporter.export_docx(proj, sections)
        return Response(content=bio.getvalue(), media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', headers={"Content-Disposition": f"attachment; filename=project_{proj.id}.docx"})
    else:
        bio = exporter.export_pptx(proj, sections)
        return Response(content=bio.getvalue(), media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation', headers={"Content-Disposition": f"attachment; filename=project_{proj.id}.pptx"})


@app.post('/projects/{project_id}/suggest_outline')
def suggest_outline(project_id: int, count: int = 5, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    proj = crud.get_project(db, project_id, current_user.id)
    if not proj:
        raise HTTPException(status_code=404, detail='Project not found')
    # Ask LLM to suggest section or slide titles
    prompt = f"Suggest {count} concise section or slide titles (one per line) for a document about: {proj.prompt or proj.title}. Return titles only."
    text = llm_client.generate_for_section(prompt)
    # parse lines and strip numbering/bullets
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    titles = []
    for l in lines:
        # remove leading numbering or bullets
        import re
        t = re.sub(r'^\s*\d+\.|^\s*[-*\u2022]\s*', '', l).strip()
        if t:
            titles.append(t)
    # fallback: if parsing failed, use the whole text as one title
    if not titles:
        titles = [text.strip()]
    return {'suggestions': titles}


@app.post('/projects/{project_id}/apply_outline')
def apply_outline(project_id: int, payload: dict, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    proj = crud.get_project(db, project_id, current_user.id)
    if not proj:
        raise HTTPException(status_code=404, detail='Project not found')
    titles = payload.get('titles') or []
    created = []
    for idx, t in enumerate(titles):
        sec = crud.add_section(db, proj.id, title=t, position=idx, is_slide=(proj.doc_type == 'pptx'))
        created.append({'id': sec.id, 'title': sec.title})
    return {'created': created}
