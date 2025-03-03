from sqlalchemy import Boolean, Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    username = Column(String(255), primary_key=True)
    password = Column(String(255), nullable=False)
    email = Column(String(255))
    local = Column(Boolean, default=False)
    admin = Column(Boolean, default=False)

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)