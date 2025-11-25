from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from .database import Base
import datetime


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    projects = relationship('Project', back_populates='owner')


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # docx or pptx
    prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    owner = relationship('User', back_populates='projects')
    sections = relationship('Section', back_populates='project', order_by='Section.position')


class Section(Base):
    __tablename__ = 'sections'
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    title = Column(String, nullable=False)
    content = Column(Text, default='')
    position = Column(Integer, default=0)
    is_slide = Column(Boolean, default=False)
    project = relationship('Project', back_populates='sections')
    refinements = relationship('Refinement', back_populates='section', order_by='Refinement.created_at')
    comments = relationship('Comment', back_populates='section')


class Refinement(Base):
    __tablename__ = 'refinements'
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey('sections.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    prompt = Column(Text)
    new_content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    section = relationship('Section', back_populates='refinements')


class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey('sections.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    section = relationship('Section', back_populates='comments')
