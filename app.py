import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from models import db, User

# ─── CREATING APP ──────────────────────────────────────────────────────

app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'placement-portal-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'placement.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB

# Ensure instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

# ─── EXTENSIONS ──────────────────────────────────────────────────────

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── REGISTER ROUTES ────────────────────────────────────────────────

from application.auth import auth_bp
from application.admin import admin_bp
from application.company import company_bp
from application.student import student_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(company_bp, url_prefix='/company')
app.register_blueprint(student_bp, url_prefix='/student')


# ─── HOME PAGE ───────────────────────────────────────────────────────

from flask import render_template
@app.route('/')
def index():
    return render_template('index.html')


# ─── CREATE TABLES & SEED ADMIN ─────────────────────────────────────

with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin', email='admin@portal.com',
                     role='admin', is_active=True, is_approved=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin created: admin / admin123')


# ─── RUN ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5001)
