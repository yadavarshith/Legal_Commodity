from sqlalchemy import Column, String, JSON, Integer, DateTime
from .database import Base
import datetime

class InspectionCase(Base):
    __tablename__ = "inspection_cases"
    id = Column(String, primary_key=True)
    status = Column(String)
    data = Column(JSON) # Store Inspection JSON snapshot
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class InspectorDecision(Base):
    __tablename__ = "inspector_decisions"
    id = Column(Integer, primary_key=True)
    inspection_id = Column(String)
    finding_id = Column(String)
    decision = Column(String)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
