from sqlalchemy import Column, String, Float
from backend.db.connection import Base


class MinistryOutcome(Base):
    __tablename__ = "ministry_outcomes"
    id = Column(String, primary_key=True)
    student_id = Column(String)
    impact_score = Column(Float)
    description = Column(String)
