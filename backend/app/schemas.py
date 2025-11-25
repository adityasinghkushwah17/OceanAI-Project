from pydantic import BaseModel, EmailStr
from typing import List, Optional
import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class SectionBase(BaseModel):
    title: str
    position: Optional[int] = 0
    is_slide: Optional[bool] = False


class SectionCreate(SectionBase):
    pass


class SectionOut(SectionBase):
    id: int
    content: Optional[str] = ''

    class Config:
        orm_mode = True


class ProjectCreate(BaseModel):
    title: str
    doc_type: str
    prompt: Optional[str]
    sections: Optional[List[SectionCreate]] = []


class ProjectOut(BaseModel):
    id: int
    title: str
    doc_type: str
    prompt: Optional[str]
    sections: List[SectionOut]

    class Config:
        orm_mode = True


class RefinementCreate(BaseModel):
    prompt: str
    section_id: int


class CommentCreate(BaseModel):
    section_id: int
    text: str
