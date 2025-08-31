from datetime import datetime
from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, facility, pharmacy
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'))
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'))

class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    shortname = db.Column(db.String(10), nullable=False, unique=True)
    pharmacies = db.relationship('Pharmacy', backref='facility', lazy=True)
    clients = db.relationship('Client', backref='facility', lazy=True)

class Pharmacy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    users = db.relationship('User', backref='pharmacy', lazy=True)
    stocks = db.relationship('Stock', backref='pharmacy', lazy=True)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))  # pharmacy never sees this; 
    unique_id = db.Column(db.String(20), unique=True, nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'))  # aservicing pharamacy

class Refill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    drug = db.Column(db.String(50), nullable=False)  # TDF-3TC-DTG or ABC-3TC-DTG
    refill_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)

    upload_filename = db.Column(db.String(255), nullable=True)  
   
class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    drug = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
