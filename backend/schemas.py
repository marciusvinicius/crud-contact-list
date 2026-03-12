from typing import List, Optional

from pydantic import BaseModel, EmailStr


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    emails: List[EmailStr]


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    emails: Optional[List[EmailStr]] = None


class Contact(ContactBase):
    id: int

