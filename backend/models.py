# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
import datetime

from database import Base

class DBJob(Base):

    __tablename__ = "simulation_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


    user_id = Column(String(50), index=True)

    project_name = Column(String(100))


    status = Column(String(20), default="SAVED")

    config_json = Column(Text)


    created_at = Column(DateTime, default=datetime.datetime.utcnow)