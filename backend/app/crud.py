from sqlalchemy.orm import Session
from . import models, schemas, auth
from typing import List


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, email: str, password: str):
    hashed = auth.get_password_hash(password)
    user = models.User(email=email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_project(db: Session, owner_id: int, project_in: schemas.ProjectCreate):
    proj = models.Project(owner_id=owner_id, title=project_in.title, doc_type=project_in.doc_type, prompt=project_in.prompt)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    for idx, s in enumerate(project_in.sections or []):
        sec = models.Section(project_id=proj.id, title=s.title, position=s.position or idx, is_slide=s.is_slide)
        db.add(sec)
    db.commit()
    db.refresh(proj)
    return proj


def get_projects_for_user(db: Session, user_id: int):
    return db.query(models.Project).filter(models.Project.owner_id == user_id).all()


def get_project(db: Session, project_id: int, user_id: int):
    return db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user_id).first()


def add_section(db: Session, project_id: int, title: str, position: int = 0, is_slide: bool = False):
    sec = models.Section(project_id=project_id, title=title, position=position, is_slide=is_slide)
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return sec


def update_section_content(db: Session, section_id: int, new_content: str):
    sec = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not sec:
        return None
    sec.content = new_content
    db.commit()
    db.refresh(sec)
    return sec


def create_refinement(db: Session, section_id: int, user_id: int, prompt: str, new_content: str):
    r = models.Refinement(section_id=section_id, user_id=user_id, prompt=prompt, new_content=new_content)
    db.add(r)
    # update section content
    sec = db.query(models.Section).filter(models.Section.id == section_id).first()
    if sec:
        sec.content = new_content
    db.commit()
    db.refresh(r)
    return r


def add_comment(db: Session, section_id: int, user_id: int, text: str):
    c = models.Comment(section_id=section_id, user_id=user_id, text=text)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
