import os
from datetime import datetime
from ldap3 import Server, Connection, ALL
from sqlalchemy.orm import sessionmaker
from models import Employee, EmployeePresence, Base
from sqlalchemy import create_engine
from ldap3.utils.dn import parse_dn

# Корневые OU и “человеческие” имена:
LDAP_BASES = [
    ("OU=Office,DC=ApexBank,DC=corp", "Старая структура"),
    ("OU=Tashkent,OU=Branches,OU=Internal,OU=Users_Accounts,DC=ApexBank,DC=corp", "Городские филиалы"),
    ("OU=Tashkent Region,OU=Branches,OU=Internal,OU=Users_Accounts,DC=ApexBank,DC=corp", "Филиалы - Ташкентская область"),
    ("OU=Region,OU=Branches,OU=Internal,OU=Users_Accounts,DC=ApexBank,DC=corp", "Региональные филиалы"),
    # Можно добавить еще OU
]

LDAP_SERVER = os.getenv("LDAP_SERVER", "ldap://dc-01.apexbank.corp")
LDAP_USER = os.getenv("LDAP_USER", "APEXBANK\\test.user")
LDAP_PASSWORD = os.getenv("LDAP_PASSWORD", "q1w2e3r4T*123")

DB_PATH = os.getenv("DB_PATH", "sqlite:///employees.db")
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def safe_attr(attrs, key):
    value = attrs.get(key, [''])
    return value[0] if value else ''

def extract_relative_ou_path(dn, base):
    """
    Вернуть только под-OU для дерева, без промежуточных папок.
    dn — Distinguished Name пользователя
    base — тот же DN, что и в LDAP_BASES
    """
    dn_upper = dn.upper()
    base_upper = base.upper()
    if dn_upper.endswith(',' + base_upper):
        relative = dn[:-(len(base)+1)]
    elif dn_upper == base_upper:
        relative = ''
    else:
        relative = dn
    try:
        pairs = parse_dn(relative)
        # Только OU, игнорируем CN
        ou_list = [x[1] for x in pairs if x[0] == "OU"]
        # Оставляем только самые нижние (например, Tashkent)
        return '/'.join(reversed(ou_list)) if ou_list else ""
    except Exception:
        return ""

def sync_ad():
    server = Server(LDAP_SERVER, get_info=ALL)
    conn = Connection(server, LDAP_USER, LDAP_PASSWORD, auto_bind=True)
    session = Session()
    emails_in_ad = set()

    for base, root_label in LDAP_BASES:
        base = base.strip()
        if not base:
            continue
        conn.search(
            search_base=base,
            search_filter='(&(objectClass=user)(mail=*))',
            attributes=[
                'displayName', 'telephoneNumber', 'mobile', 'mail',
                'title', 'department', 'userAccountControl', 'distinguishedName'
            ]
        )
        for entry in conn.entries:
            attrs = entry.entry_attributes_as_dict
            email = safe_attr(attrs, 'mail')
            if not email:
                continue
            emails_in_ad.add(email)
            dn = safe_attr(attrs, 'distinguishedName')
            ou_path = extract_relative_ou_path(dn, base)
            full_ou_path = f"{root_label}/{ou_path}" if ou_path else root_label
            uac = attrs.get('userAccountControl', [512])[0]
            is_enabled = not (int(uac) & 2)

            emp = session.query(Employee).filter_by(email=email).first()
            if not emp:
                emp = Employee(
                    name=safe_attr(attrs, 'displayName'),
                    phone=safe_attr(attrs, 'telephoneNumber'),
                    mobile=safe_attr(attrs, 'mobile'),
                    email=email,
                    title=safe_attr(attrs, 'title'),
                    department=safe_attr(attrs, 'department'),
                    is_enabled=is_enabled,
                    ou_path=full_ou_path,
                    updated_at=datetime.utcnow()
                )
                session.add(emp)
                session.flush()
            else:
                emp.name = safe_attr(attrs, 'displayName')
                emp.phone = safe_attr(attrs, 'telephoneNumber')
                emp.mobile = safe_attr(attrs, 'mobile')
                emp.title = safe_attr(attrs, 'title')
                emp.department = safe_attr(attrs, 'department')
                emp.is_enabled = is_enabled
                emp.ou_path = full_ou_path
                emp.updated_at = datetime.utcnow()
                session.add(emp)
                session.flush()
            presence = session.query(EmployeePresence).filter_by(employee_id=emp.id).first()
            if not presence:
                session.add(EmployeePresence(employee_id=emp.id, is_present=True, updated_at=datetime.utcnow()))
            else:
                presence.is_present = True
                presence.updated_at = datetime.utcnow()

    # Деактивируем отсутствующих в OU
    for presence in session.query(EmployeePresence).filter_by(is_present=True).all():
        emp = session.query(Employee).filter_by(id=presence.employee_id).first()
        if emp and emp.email not in emails_in_ad:
            presence.is_present = False
            presence.updated_at = datetime.utcnow()

    session.commit()
    conn.unbind()