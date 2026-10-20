import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Position(Base):
    __tablename__ = "positions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pos_name = Column(String, nullable=False)
    is_free = Column(Boolean, default=True, nullable=False)

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Strict ForeignKey referencing Position.id
    position_id = Column(String(36), ForeignKey("positions.id"), nullable=False)
    app_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    educ = Column(String, nullable=False)
    experience = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    status = Column(String, default="New", nullable=False) # "New", "Hired", "Canceled"

# import uuid
# from datetime import datetime, date
# from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey
# from sqlalchemy.orm import declarative_base

# Base = declarative_base()

# class Position(Base):
#     __tablename__ = "positions"

#     id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     pos_name = Column(String, nullable=False)
#     is_free = Column(Boolean, default=True, nullable=False)

# class Application(Base):
#     __tablename__ = "applications"

#     id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     # Strict ForeignKey referencing Position.id
#     position_id = Column(String(36), ForeignKey("positions.id"), nullable=False)
#     app_date = Column(DateTime, default=datetime.utcnow, nullable=False)
#     educ = Column(String, nullable=False)
#     experience = Column(String, nullable=False)
#     full_name = Column(String, nullable=False)
#     email = Column(String, nullable=False)
#     birth_date = Column(Date, nullable=False)
#     status = Column(String, default="New", nullable=False) # "New", "Hired", "Canceled"