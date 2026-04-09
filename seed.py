"""Run this to fill the database with sample data."""
from datetime import date
from app import app
from models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application

with app.app_context():
    # ── Companies ──────────────────────────────────────────────────────────────
    c1u = User(username='techcorp', email='hr@techcorp.com', role='company', is_active=True, is_approved=True)
    c1u.set_password('company123'); db.session.add(c1u); db.session.flush()
    c1 = CompanyProfile(user_id=c1u.id, company_name='TechCorp Solutions', industry='IT Services',
                        contact_person='Rahul Sharma', contact_phone='9876543210',
                        website='https://techcorp.example.com',
                        description='Leading IT services company with 10000+ employees.')
    db.session.add(c1)

    c2u = User(username='innovate', email='hr@innovate.com', role='company', is_active=True, is_approved=True)
    c2u.set_password('company123'); db.session.add(c2u); db.session.flush()
    c2 = CompanyProfile(user_id=c2u.id, company_name='Innovate Labs', industry='Software',
                        contact_person='Priya Patel',
                        description='Product startup building next-gen developer tools.')
    db.session.add(c2)

    c3u = User(username='datasys', email='hr@datasys.com', role='company', is_active=True, is_approved=True)
    c3u.set_password('company123'); db.session.add(c3u); db.session.flush()
    c3 = CompanyProfile(user_id=c3u.id, company_name='DataSys Analytics', industry='Data & Analytics',
                        contact_person='Neha Gupta', contact_phone='9700000003',
                        description='Data-driven insights company working with Fortune 500 clients.')
    db.session.add(c3)

    # Pending company — visible in admin approval queue
    c4u = User(username='globalfin', email='hr@globalfin.com', role='company', is_active=True, is_approved=False)
    c4u.set_password('company123'); db.session.add(c4u); db.session.flush()
    c4 = CompanyProfile(user_id=c4u.id, company_name='GlobalFin Services', industry='Finance',
                        contact_person='Amit Kumar')
    db.session.add(c4); db.session.flush()

    # ── Students ───────────────────────────────────────────────────────────────
    profiles = []
    for uname, email, name, roll, dept, cgpa, phone in [
        ('student1', 'alice@college.edu',  'Alice Johnson', 'CS2021001', 'CSE', 8.5, '9111111111'),
        ('student2', 'bob@college.edu',    'Bob Williams',  'CS2021002', 'CSE', 7.8, '9222222222'),
        ('student3', 'carol@college.edu',  'Carol Davis',   'EC2021001', 'ECE', 9.1, '9333333333'),
        ('student4', 'david@college.edu',  'David Brown',   'ME2021001', 'ME',  7.2, '9444444444'),
        ('student5', 'eve@college.edu',    'Eve Wilson',    'CS2021003', 'CSE', 8.9, '9555555555'),
        ('student6', 'frank@college.edu',  'Frank Thomas',  'EC2021002', 'ECE', 7.5, '9666666666'),
        ('student7', 'grace@college.edu',  'Grace Lee',     'IT2021001', 'IT',  8.2, '9777777777'),
    ]:
        u = User(username=uname, email=email, role='student', is_active=True, is_approved=True)
        u.set_password('student123'); db.session.add(u); db.session.flush()
        sp = StudentProfile(user_id=u.id, full_name=name, roll_number=roll,
                            department=dept, cgpa=cgpa, phone_no=phone, graduation_year=2026)
        db.session.add(sp); profiles.append(sp)
    db.session.flush()

    alice, bob, carol, david, eve, frank, grace = profiles

    # ── Placement Drives ───────────────────────────────────────────────────────
    d1 = PlacementDrive(
        company_id=c1.id, title='Software Engineer',
        description='Full-stack development role working on cloud-native web applications.',
        location='Bangalore', salary_package='12 LPA',
        eligibility_cgpa=7.0, eligible_departments='CSE, ECE',
        drive_date=date(2026, 5, 5), last_apply_date=date(2026, 4, 28),
        status='Approved')

    d2 = PlacementDrive(
        company_id=c1.id, title='Data Analyst',
        description='Analyse business data and build dashboards for stakeholders.',
        location='Hyderabad', salary_package='8 LPA',
        eligibility_cgpa=6.5, eligible_departments='',   # All departments
        drive_date=date(2026, 5, 12), last_apply_date=date(2026, 5, 2),
        status='Approved')

    d3 = PlacementDrive(
        company_id=c2.id, title='Backend Developer',
        description='Build scalable microservices in Python and Go.',
        location='Pune', salary_package='15 LPA',
        eligibility_cgpa=7.5, eligible_departments='CSE',
        drive_date=date(2026, 5, 20), last_apply_date=date(2026, 5, 8),
        status='Approved')

    d4 = PlacementDrive(
        company_id=c3.id, title='Data Scientist',
        description='ML modelling and predictive analytics for enterprise clients.',
        location='Chennai', salary_package='18 LPA',
        eligibility_cgpa=8.0, eligible_departments='CSE, IT',
        drive_date=date(2026, 5, 15), last_apply_date=date(2026, 5, 1),
        status='Approved')

    # Pending — visible in admin drive approval queue
    d5 = PlacementDrive(
        company_id=c2.id, title='UI/UX Designer',
        description='Design intuitive user experiences for our SaaS products.',
        location='Mumbai', salary_package='10 LPA',
        status='Pending')

    # Closed — shows historical drive
    d6 = PlacementDrive(
        company_id=c1.id, title='DevOps Engineer',
        description='CI/CD pipelines and cloud infrastructure management.',
        location='Bangalore', salary_package='14 LPA',
        drive_date=date(2026, 3, 20), last_apply_date=date(2026, 3, 10),
        status='Closed')

    db.session.add_all([d1, d2, d3, d4, d5, d6]); db.session.flush()

    # ── Applications ───────────────────────────────────────────────────────────
    # d1 — TechCorp Software Engineer (CSE, ECE eligible, CGPA ≥ 7.0)
    # d2 — TechCorp Data Analyst (All depts, CGPA ≥ 6.5)
    # d3 — Innovate Backend Developer (CSE, CGPA ≥ 7.5)
    # d4 — DataSys Data Scientist (CSE, IT, CGPA ≥ 8.0)
    db.session.add_all([
        Application(student_id=alice.id,  drive_id=d1.id, status='Shortlisted'),
        Application(student_id=bob.id,    drive_id=d1.id, status='Applied'),
        Application(student_id=carol.id,  drive_id=d1.id, status='Selected'),
        Application(student_id=eve.id,    drive_id=d1.id, status='Selected'),
        Application(student_id=frank.id,  drive_id=d1.id, status='Applied'),

        Application(student_id=alice.id,  drive_id=d2.id, status='Selected'),
        Application(student_id=bob.id,    drive_id=d2.id, status='Shortlisted'),
        Application(student_id=david.id,  drive_id=d2.id, status='Applied'),
        Application(student_id=grace.id,  drive_id=d2.id, status='Applied'),

        Application(student_id=alice.id,  drive_id=d3.id, status='Applied'),
        Application(student_id=eve.id,    drive_id=d3.id, status='Shortlisted'),
        Application(student_id=bob.id,    drive_id=d3.id, status='Rejected'),

        Application(student_id=alice.id,  drive_id=d4.id, status='Selected'),
        Application(student_id=eve.id,    drive_id=d4.id, status='Shortlisted'),
        Application(student_id=grace.id,  drive_id=d4.id, status='Applied'),
    ])
    db.session.commit()

    print('Seeding complete! Credentials:')
    print()
    print('  Admin:    admin / admin123')
    print()
    print('  Companies (approved):')
    print('    techcorp  / company123  ->  TechCorp Solutions')
    print('    innovate  / company123  ->  Innovate Labs')
    print('    datasys   / company123  ->  DataSys Analytics')
    print()
    print('  Company (pending approval):')
    print('    globalfin / company123  ->  GlobalFin Services')
    print()
    print('  Students (student1-7 / student123):')
    print('    student1  Alice Johnson  CSE  8.5')
    print('    student2  Bob Williams   CSE  7.8')
    print('    student3  Carol Davis    ECE  9.1')
    print('    student4  David Brown    ME   7.2')
    print('    student5  Eve Wilson     CSE  8.9')
    print('    student6  Frank Thomas   ECE  7.5')
    print('    student7  Grace Lee      IT   8.2')
