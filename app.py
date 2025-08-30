import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from dotenv import load_dotenv
from passlib.hash import pbkdf2_sha256
import pandas as pd
from io import BytesIO

from extensions import db
from models import User, Facility, Pharmacy, Client, Refill, Stock
from utils import role_required

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///c_refill.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

db.init_app(app)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = User.query.filter_by(username=username).first()
        if user and pbkdf2_sha256.verify(password, user.password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['facility_id'] = user.facility_id
            session['pharmacy_id'] = user.pharmacy_id
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))
    role = session['role']
    if role == 'admin':
        fac_count = Facility.query.count()
        pharm_count = Pharmacy.query.count()
        client_count = Client.query.count()
        return render_template('admin_dashboard.html', fac_count=fac_count, pharm_count=pharm_count, client_count=client_count)
    if role == 'facility':
        facility = Facility.query.get(session.get('facility_id'))
        clients = Client.query.filter_by(facility_id=facility.id).count() if facility else 0
        pharms = Pharmacy.query.filter_by(facility_id=facility.id).count() if facility else 0
        return render_template('facility_dashboard.html', facility=facility, client_count=clients, pharm_count=pharms)
    if role == 'pharmacy':
        pharmacy = Pharmacy.query.get(session.get('pharmacy_id'))
        refill_count = Refill.query.filter_by(pharmacy_id=pharmacy.id).count() if pharmacy else 0
        return render_template('pharmacy_dashboard.html', pharmacy=pharmacy, refill_count=refill_count)
    return redirect(url_for('login'))

# admiun to add facility and pharmacies
@app.route('/admin/facility/new', methods=['GET','POST'])
@role_required('admin')
def admin_add_facility():
    if request.method == 'POST':
        name = request.form['name'].strip()
        shortname = request.form['shortname'].strip().upper()
        if not name or not shortname:
            flash('Name and shortname required', 'error')
            return redirect(url_for('admin_add_facility'))
        fac = Facility(name=name, shortname=shortname)
        db.session.add(fac)
        db.session.commit()
        flash('Facility added', 'ok')
        return redirect(url_for('dashboard'))
    return render_template('admin_add_facility.html')

@app.route('/admin/pharmacy/new', methods=['GET','POST'])
@role_required('admin')
def admin_add_pharmacy():
    facilities = Facility.query.order_by(Facility.name).all()
    if request.method == 'POST':
        name = request.form['name'].strip()
        facility_id = int(request.form['facility_id'])
        ph = Pharmacy(name=name, facility_id=facility_id)
        db.session.add(ph)
        db.session.commit()
        flash('Pharmacy added', 'ok')
        return redirect(url_for('dashboard'))
    return render_template('admin_add_pharmacy.html', facilities=facilities)

# client creation for everyone(you get to create, i get to create)
@app.route('/clients/new', methods=['GET','POST'])
def add_client():
    if 'role' not in session:
        return redirect(url_for('login'))
    role = session['role']
    facilities = Facility.query.order_by(Facility.name).all()
    pharmacies = Pharmacy.query.order_by(Pharmacy.name).all()

    if request.method == 'POST':
        unique_id = request.form['unique_id'].strip().upper()
        facility_id = int(request.form['facility_id'])
        pharmacy_id = int(request.form['pharmacy_id']) if request.form.get('pharmacy_id') else None

        if role == 'pharmacy':
            name = ''  # pharmacy never handles names cause we dont love them
        else:
            name = request.form.get('name','').strip()

        if not unique_id:
            flash('Unique ID required', 'error')
            return redirect(url_for('add_client'))

        client = Client(name=name, unique_id=unique_id, facility_id=facility_id, pharmacy_id=pharmacy_id)
        db.session.add(client)
        db.session.commit()
        flash('Client added', 'ok')
        return redirect(url_for('dashboard'))
    return render_template('client_new.html', facilities=facilities, pharmacies=pharmacies, role=role)

#facility sees clients and reports
@app.route('/facility/clients')
@role_required('facility')
def facility_clients():
    facility_id = session.get('facility_id')
    clients = Client.query.filter_by(facility_id=facility_id).all()
    pharmacies = {p.id: p for p in Pharmacy.query.filter_by(facility_id=facility_id).all()}
    return render_template('facility_clients.html', clients=clients, pharmacies=pharmacies)

@app.route('/facility/reports')
@role_required('facility')
def facility_reports():
    return render_template('facility_reports.html')

@app.route('/facility/reports/refill.xlsx')
@role_required('facility')
def facility_refill_report():
    facility_id = session.get('facility_id')
    # refill, pharamcy and clients
    data = db.session.query(Client.name, Client.unique_id, Refill.drug, Refill.refill_date, Pharmacy.name.label('pharmacy_name'))\
        .join(Refill, Refill.client_id==Client.id)\
        .join(Pharmacy, Pharmacy.id==Refill.pharmacy_id)\
        .filter(Client.facility_id==facility_id).all()
    df = pd.DataFrame(data, columns=['Client Name','Unique ID','Drug','Refill Date','Pharmacy'])
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Refills')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='facility_refills.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/facility/reports/stock.xlsx')
@role_required('facility')
def facility_stock_report():
    facility_id = session.get('facility_id')
    #stock upload kinda confused on how to do this tho i hio[pe to remember]
    subq = db.session.query(Stock.pharmacy_id, Stock.drug, db.func.max(Stock.date).label('max_date'))\
        .join(Pharmacy, Pharmacy.id==Stock.pharmacy_id)\
        .filter(Pharmacy.facility_id==facility_id)\
        .group_by(Stock.pharmacy_id, Stock.drug).subquery()
    rows = db.session.query(Pharmacy.name, Stock.drug, Stock.quantity, Stock.date)\
        .join(subq, (Stock.pharmacy_id==subq.c.pharmacy_id) & (Stock.drug==subq.c.drug) & (Stock.date==subq.c.max_date))\
        .join(Pharmacy, Pharmacy.id==Stock.pharmacy_id).all()
    df = pd.DataFrame(rows, columns=['Pharmacy','Drug','Quantity','Date'])
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Stocks')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='facility_stocks.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

#pharamcy: still no names babes
@app.route('/pharmacy/refill', methods=['GET','POST'])
@role_required('pharmacy')
def pharmacy_refill():
    if request.method == 'POST':
        unique_id = request.form['unique_id'].strip().upper()
        drug = request.form['drug']
        refill_date = request.form['refill_date']
        pharmacy_id = session.get('pharmacy_id')
        client = Client.query.filter_by(unique_id=unique_id).first()
        if not client:
            flash('Client not found', 'error')
            return redirect(url_for('pharmacy_refill'))
        r = Refill(client_id=client.id, drug=drug, refill_date=datetime.fromisoformat(refill_date).date(), pharmacy_id=pharmacy_id)
        db.session.add(r)
        db.session.commit()
        flash('Refill saved', 'ok')
        return redirect(url_for('pharmacy_refill'))
    return render_template('pharmacy_refill.html')

@app.route('/pharmacy/stocks', methods=['GET','POST'])
@role_required('pharmacy')
def pharmacy_stocks():
    if request.method == 'POST':
        drug = request.form['drug']
        quantity = int(request.form['quantity'])
        date = request.form['date']
        s = Stock(pharmacy_id=session.get('pharmacy_id'), drug=drug, quantity=quantity, date=datetime.fromisoformat(date).date())
        db.session.add(s)
        db.session.commit()
        flash('Stock saved', 'ok')
        return redirect(url_for('pharmacy_stocks'))
    return render_template('pharmacy_stock.html')

@app.route('/pharmacy/reports')
@role_required('pharmacy')
def pharmacy_reports():
    return render_template('pharmacy_reports.html')

@app.route('/pharmacy/reports/refill.xlsx')
@role_required('pharmacy')
def pharmacy_refill_report_download():
    pharmacy_id = session.get('pharmacy_id')
    rows = db.session.query(Client.unique_id, Refill.drug, Refill.refill_date)\
        .join(Refill, Refill.client_id==Client.id)\
        .filter(Refill.pharmacy_id==pharmacy_id).all()
    df = pd.DataFrame(rows, columns=['Unique ID','Drug','Refill Date'])
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Refills')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='pharmacy_refills.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/pharmacy/reports/stock.xlsx')
@role_required('pharmacy')
def pharmacy_stock_report_download():
    pharmacy_id = session.get('pharmacy_id')
    subq = db.session.query(Stock.drug, db.func.max(Stock.date).label('max_date')).filter(Stock.pharmacy_id==pharmacy_id).group_by(Stock.drug).subquery()
    rows = db.session.query(Stock.drug, Stock.quantity, Stock.date)\
        .join(subq, (Stock.drug==subq.c.drug) & (Stock.date==subq.c.max_date))\
        .filter(Stock.pharmacy_id==pharmacy_id).all()
    df = pd.DataFrame(rows, columns=['Drug','Quantity','Date'])
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Stocks')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='pharmacy_stocks.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# run run run
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)