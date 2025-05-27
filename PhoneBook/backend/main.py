from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Employee, EmployeePresence, Base
from sync_ad import sync_ad, DB_PATH
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для разработки! На проде ограничить.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

@app.get("/api/employees/")
def get_employees():
    """Получить всех сотрудников, присутствующих в базе (фильтрация на фронте по OU)."""
    session = Session()
    active_ids = [p.employee_id for p in session.query(EmployeePresence).filter_by(is_present=True)]
    employees = session.query(Employee).filter(Employee.id.in_(active_ids)).all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "phone": e.phone,
            "mobile": e.mobile,
            "email": e.email,
            "title": e.title,
            "department": e.department,
            "is_enabled": e.is_enabled,
            "ou_path": e.ou_path,
            "updated_at": e.updated_at,
        }
        for e in employees
    ]

@app.get("/api/ou-tree/")
def get_ou_tree():
    """
    Вернуть дерево OU и сотрудников для фронта.
    Корни будут: "Офис", "Региональные филиалы" и т.д., в зависимости от sync_ad.py!
    """
    session = Session()
    employees = session.query(Employee).filter(
        Employee.ou_path != None,
        EmployeePresence.is_present == True,
        Employee.id == EmployeePresence.employee_id
    ).all()
    tree = {}
    for e in employees:
        parts = e.ou_path.split('/') if e.ou_path else []
        node = tree
        for part in parts:
            node = node.setdefault(part, {})
        node.setdefault('__employees__', []).append({
            "id": e.id,
            "name": e.name,
            "phone": e.phone,
            "mobile": e.mobile,
            "email": e.email,
            "title": e.title,
            "department": e.department,
            "is_enabled": e.is_enabled,
            "ou_path": e.ou_path,
            "updated_at": str(e.updated_at),
        })
    return tree

@app.post("/api/sync/")
def sync_now():
    sync_ad()
    return {"status": "ok"}

# --- Автоматическая синхронизация каждые 10 минут ---
scheduler = BackgroundScheduler()
scheduler.add_job(sync_ad, 'interval', minutes=10)
scheduler.start()

# --- Первый запуск при старте приложения ---
sync_ad()