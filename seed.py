"""Run this to fill the database with sample data."""
from datetime import date
from app import app
from models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application

with app.app_context():
    c1u = User(username='techcorp', email='hr@techcorp.com', role='company', is_active=True, is_approved=True)
    c1u.set_password('company123'); db.session.add(c1u); db.session.flush()
    c1 = CompanyProfile(user_id=c1u.id, company_name='TechCorp Solutions', industry='IT Services', contact_person='Rahul Sharma', contact_phone='9876543210')
    db.session.add(c1)

    c2u = User(username='innovate', email='hr@innovate.com', role='company', is_active=True, is_approved=True)
    c2u.set_password('company123'); db.session.add(c2u); db.session.flush()
    c2 = CompanyProfile(user_id=c2u.id, company_name='Innovate Labs', industry='Software', contact_person='Priya Patel')
    db.session.add(c2)

    c3u = User(username='globalfin', email='hr@globalfin.com', role='company', is_active=True, is_approved=False)
    c3u.set_password('company123'); db.session.add(c3u); db.session.flush()
    c3 = CompanyProfile(user_id=c3u.id, company_name='GlobalFin Services', industry='Finance', contact_person='Amit Kumar')
    db.session.add(c3); db.session.flush()

    profiles = []
    for uname, email, name, roll, dept, cgpa, phone in [
        ('student1','alice@college.edu','Alice Johnson','CS2021001','CSE',8.5,'9111111111'),
        ('student2','bob@college.edu','Bob Williams','CS2021002','CSE',7.8,'9222222222'),
        ('student3','carol@college.edu','Carol Davis','EC2021001','ECE',9.1,'9333333333'),
        ('student4','david@college.edu','David Brown','ME2021001','ME',7.2,'9444444444'),
        ('student5','eve@college.edu','Eve Wilson','CS2021003','CSE',8.9,'9555555555'),
    ]:
        u = User(username=uname, email=email, role='student', is_active=True, is_approved=True)
        u.set_password('student123'); db.session.add(u); db.session.flush()
        sp = StudentProfile(user_id=u.id, full_name=name, roll_number=roll, department=dept, cgpa=cgpa, phone=phone, graduation_year=2026)
        db.session.add(sp); profiles.append(sp)
    db.session.flush()

    d1 = PlacementDrive(company_id=c1.id, title='Software Engineer', description='Full-stack role.', location='Bangalore', salary_package='12 LPA', eligibility_cgpa=7.0, eligible_departments='CSE, ECE', drive_date=date(2026,4,15), last_apply_date=date(2026,4,10), status='Approved')
    d2 = PlacementDrive(company_id=c1.id, title='Data Analyst', description='Analyze data.', location='Hyderabad', salary_package='8 LPA', eligibility_cgpa=6.5, eligible_departments='All', drive_date=date(2026,4,20), last_apply_date=date(2026,4,15), status='Approved')
    d3 = PlacementDrive(company_id=c2.id, title='Backend Developer', description='Microservices.', location='Pune', salary_package='15 LPA', eligibility_cgpa=7.5, eligible_departments='CSE', drive_date=date(2026,5,1), last_apply_date=date(2026,4,25), status='Approved')
    d4 = PlacementDrive(company_id=c2.id, title='UI/UX Designer', location='Mumbai', salary_package='10 LPA', status='Pending')
    d5 = PlacementDrive(company_id=c1.id, title='DevOps Engineer', location='Bangalore', salary_package='14 LPA', status='Closed')
    db.session.add_all([d1,d2,d3,d4,d5]); db.session.flush()

    db.session.add_all([
        Application(student_id=profiles[0].id, drive_id=d1.id, status='Shortlisted'),
        Application(student_id=profiles[1].id, drive_id=d1.id, status='Applied'),
        Application(student_id=profiles[2].id, drive_id=d1.id, status='Selected'),
        Application(student_id=profiles[0].id, drive_id=d2.id, status='Applied'),
        Application(student_id=profiles[3].id, drive_id=d2.id, status='Applied'),
        Application(student_id=profiles[4].id, drive_id=d3.id, status='Shortlisted'),
        Application(student_id=profiles[0].id, drive_id=d3.id, status='Applied'),
        Application(student_id=profiles[1].id, drive_id=d3.id, status='Rejected'),
    ])
    db.session.commit()
    print('Done! Credentials:')
    print('  Admin:    admin / admin123')
    print('  Company:  techcorp / company123, innovate / company123')
    print('  Pending:  globalfin / company123')
    print('  Students: student1-5 / student123')
