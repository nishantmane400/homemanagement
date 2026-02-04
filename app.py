import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# -----------------------------
# APP CONFIG
# -----------------------------
app = Flask(__name__)

# Database (SQLite – works on Railway)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ngo_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret Key (use ENV in production)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ngo_secret_key')

# Upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# -----------------------------
# MODELS
# -----------------------------
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class VisionMission(db.Model):
    __tablename__ = 'vision_mission'
    id = db.Column(db.Integer, primary_key=True)
    vision_description = db.Column(db.Text)
    mission_description = db.Column(db.Text)
    last_updated = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Statistic(db.Model):
    __tablename__ = 'statistic'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))
    value = db.Column(db.String(50))
    display_order = db.Column(db.Integer)
    status = db.Column(db.String(20), default='active')


class Banner(db.Model):
    __tablename__ = 'banners'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    image_url = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=1)
    status = db.Column(db.Boolean, default=True)

# -----------------------------
# DATABASE INIT
# -----------------------------
with app.app_context():
    db.create_all()

# -----------------------------
# PUBLIC HOME PAGE
# -----------------------------
@app.route('/')
def index():
    banners = Banner.query.filter_by(status=True).order_by(Banner.display_order).all()
    vm = VisionMission.query.first()
    stats = Statistic.query.filter_by(status='active').order_by(Statistic.display_order).all()

    return render_template(
        'index.html',
        banners=banners,
        vm=vm,
        stats=stats,
        admin=False
    )

# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# -----------------------------
# ADMIN HOME MANAGER
# -----------------------------
@app.route('/admin/home-manager', methods=['GET', 'POST'])
def home_manager():
    vm = VisionMission.query.first()
    banners = Banner.query.order_by(Banner.display_order).all()

    if request.method == 'POST':
        action = request.form.get('action')

        # ---- Vision & Mission ----
        if action == 'save_vm':
            if not vm:
                vm = VisionMission()

            vm.vision_description = request.form.get('vision_description')
            vm.mission_description = request.form.get('mission_description')

            db.session.add(vm)
            db.session.commit()
            flash('Vision & Mission updated successfully', 'success')

        # ---- Banner Upload ----
        elif action == 'add_banner':
            file = request.files.get('banner_image')
            title = request.form.get('image_name')

            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                banner = Banner(
                    title=title,
                    image_url=f'uploads/{filename}',
                    status=True
                )
                db.session.add(banner)
                db.session.commit()
                flash('Banner added successfully', 'success')

        return redirect(url_for('home_manager'))

    return render_template(
        'index.html',
        banners=banners,
        vm=vm,
        admin=True
    )

# -----------------------------
# APP ENTRY POINT (RAILWAY)
# -----------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
