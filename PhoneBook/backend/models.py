from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    phone = Column(String)
    mobile = Column(String)
    email = Column(String, unique=True)
    title = Column(String)
    department = Column(String)
    is_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    ou_path = Column(String)  # “Путь” с корневым (человеческим) названием

class EmployeePresence(Base):
    __tablename__ = 'employee_presence'
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    is_present = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)