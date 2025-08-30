import sys, random
from passlib.hash import pbkdf2_sha256
from datetime import date


from app import app
from extensions import db
from models import User, Facility, Pharmacy, Client


FACILITIES = [
    "Sacred Heart Clinic",
    "Ajara Primary Health Centre",
    "Ajeromi General Hospital",
    "Akere Primary Health Centre",
    "Akerele Primary Health Centre",
    "All Souls Hospital",
    "Amukoko Primary Health Centre",
    "Apa Primary Health Centre",
    "Apapa General Hospital",
    "Badagry General Hospital",
    "Baruwa Primary Health Centre",
    "Coker Aguda Primary Health Centre",
    "DEETAB Hospital",
    "Dunia Hospital",
    "Ejire Primary Health Centre",
    "Faleti Medical Centre",
    "Gbagada General Hospital",
    "General Hospital Ijede",
    "General Hospital Ikorodu",
    "Harvey Road Comprehensive Health Centre",
    "Iba Primary Health Centre",
    "Ibafon Primary Health Centre",
    "Iga Idugaran Primary Health Centre",
    "Ijanikin Primary Health Centre",
    "Ijora Primary Health Centre",
    "Ilado PHC",
    "Ketu Primary Health Centre",
    "Lagos General Hospital",
    "Lagos Island Maternity Hospital",
    "Lagos State Mainland Hospital",
    "Layeni Primary Health Centre",
    "Massey Street Children's Hospital",
    "MAYFAIR Medical Centre",
    "Mobonike Hospital",
    "Odunbaku Primary Health Centre",
    "Ojo Primary Health Centre",
    "Olojowon Primary Health Centre",
    "Onikan Health Centre",
    "Orile Agege General Hospital",
    "Powerline Primary Health Centre",
    "Promise Medical Centre",
    "Randle General Hospital",
    "RCCG-RedeemAid Programme Action Committee CSO (Lagos)",
    "Sango Primary Health Centre",
    "Seme Primary Health Centre",
    "Shomolu GH",
    "Simpson Primary Health Centre",
    "St Raphael Divine Mercy Specialist Hospital",
    "St. Milla Hospital",
    "Sura Primary Health Centre",
    "Tolu Primary Health Centre",
    "Unita Hospital",
]

#helper
def base_code(name: str) -> str:
    #make shortname in 4
    parts = [p for p in name.replace("'", "").replace(".", "").split() if p]
    if not parts:
        return "FAC"
    code = parts[0][:2].upper()
    for p in parts[1:3]:
        code += p[0].upper()
    return (code or "FAC")[:4]

def unique_code(proposed: str) -> str:
    """Ensure shortname uniqueness in DB by adding 2,3,4… if needed."""
    # track
    if not hasattr(unique_code, "_used"):
        unique_code._used = set()

    code = proposed
    n = 2
    def exists(c):
        return (c in unique_code._used) or (Facility.query.filter_by(shortname=c).first() is not None)

    while exists(code):
        # suffix and keep it short
        stem = proposed[: max(1, 10 - len(str(n)))]
        code = f"{stem}{n}"
        n += 1

    unique_code._used.add(code)
    return code

PHARMACY_NAMES = [
    "Alpha Pharmacy","Beta Pharmacy","Cedar Pharmacy","Delta Pharmacy","Eagle Pharmacy",
    "Fountain Pharmacy","Grace Pharmacy","Harmony Pharmacy","Ivory Pharmacy","Jubilee Pharmacy",
    "Kingdom Pharmacy","Liberty Pharmacy","Miracle Pharmacy","Nova Pharmacy","Omega Pharmacy"
]

FIRST_NAMES = ["Adeola","Chinedu","Funke","Ifeanyi","Ngozi","Bamidele","Yusuf","Tosin","Amaka","Emeka",
               "Segun","Sade","Chika","Bolaji","Fatima","Kunle","Tunde","Bola","Halima","Kemi","Seyi","Uche","Gbenga"]
LAST_NAMES  = ["Adewale","Okeke","Balogun","Eze","Mohammed","Adeniyi","Ogunleye","Okafor","Abdullahi",
               "Ojo","Ogunyemi","Oladipo","Ogunbiyi","Okon","Okonjo","Ibrahim","Idowu"]

def ensure_admin():
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(username="admin", password=pbkdf2_sha256.hash("admin123"), role="admin"))

def create_facility_with_logins(name: str):
    base = base_code(name)
    code = unique_code(base)
    fac = Facility(name=name, shortname=code)
    db.session.add(fac)
    db.session.flush()  # get fac.id

    # facility login (username is shortname in lowercase)
    uname = code.lower()
    if not User.query.filter_by(username=uname).first():
        db.session.add(User(
            username=uname,
            password=pbkdf2_sha256.hash("facility123"),
            role="facility",
            facility_id=fac.id
        ))
    return fac, code

def create_pharmacies_for_facility(facility, code):
    pharms = []
    for i in range(1, 11):  # 10 placeholders
        pname = f"{random.choice(PHARMACY_NAMES)} {i}"
        pharm = Pharmacy(name=pname, facility_id=facility.id)
        db.session.add(pharm)
        db.session.flush()
        pharms.append(pharm)

        # pharmacy login
        p_uname = f"pharmacy{i}_{code.lower()}"
        if not User.query.filter_by(username=p_uname).first():
            db.session.add(User(
                username=p_uname,
                password=pbkdf2_sha256.hash("pharmacy123"),
                role="pharmacy",
                pharmacy_id=pharm.id
            ))
    return pharms

def create_clients_for_facility(facility, code, pharms):
    for j in range(1, 51):  # 50 clients
        full_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        uid = f"{code}{j:04d}"
        assign = random.choice(pharms) if pharms else None
        db.session.add(Client(
            name=full_name,
            unique_id=uid,
            facility_id=facility.id,
            pharmacy_id = assign.id if assign else None
        ))

#run the code cause we can
with app.app_context():
    if "--reset" in sys.argv:
        db.drop_all()
        db.create_all()
    else:
        db.create_all()

    ensure_admin()

    mapping = []  # keep (name, code) to print summary

    for fac_name in FACILITIES:
        # create facility with em logins with guaranteed-unique shortname
        fac, code = create_facility_with_logins(fac_name)
        mapping.append((fac_name, code))

        # 10 pharmacies + logins
        pharms = create_pharmacies_for_facility(fac, code)

        # 50 clients with IDs derived from the code
        create_clients_for_facility(fac, code, pharms)

    db.session.commit()

    # Print the clear stuffs
    print("✅ Seed complete.")
    print("--------------------------------------------------")
    print("Facility short codes (use lowercase as username):")
    for name, code in mapping:
        print(f"- {name}  -->  {code}   (login: {code.lower()} / facility123)")
    print("Admin login: admin / admin123")
