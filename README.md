# Placement Portal

A full-stack web application for managing campus placements. Supports three roles — **Admin**, **Company**, and **Student** — each with a dedicated workflow covering everything from company registration to final placement.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · Flask 3.0 |
| Database | SQLite · Flask-SQLAlchemy 3.1 |
| Auth | Flask-Login · Werkzeug (password hashing) |
| Forms | Flask-WTF · WTForms |
| Frontend | Jinja2 · Bootstrap 5 · Bootstrap Icons |

---

## Features

### Admin
- Approve or reject company registrations and placement drives
- Search and blacklist/activate students
- Dashboard with live KPIs (students, companies, drives, applications)
- Application outcome rates — placement, shortlist, and rejection percentages
- Bar chart: applications received per company
- Stats page: top 5 hiring companies, department-wise placements, overall placement %
- Company summary table: drives, applicants, selected, and selection rate per company

### Company
- Register and manage company profile
- Create placement drives with CGPA and department eligibility filters
- Set application deadlines
- View all applicants per drive
- Update application status: Applied → Shortlisted → Selected / Rejected
- Drives go live only after admin approval

### Student
- Register, build profile, and upload a PDF resume
- Profile completion tracker (6 fields)
- Browse all approved drives with real-time eligibility badges (Eligible / Not Eligible)
- Search drives by title or location
- Apply to drives with automatic eligibility enforcement
- Track all application statuses
- View placement history

---

## Project Structure

```
placement_portal/
├── app.py                      # Application factory & entry point
├── models.py                   # Database models
├── seed.py                     # Sample data generator
├── requirements.txt
├── instance/
│   └── placement.db            # SQLite database
├── application/
│   ├── auth.py                 # Login · Logout · Register
│   ├── admin.py                # Admin routes & analytics
│   ├── company.py              # Company routes
│   └── student.py              # Student routes
├── static/
│   ├── css/style.css
│   └── uploads/                # Uploaded resumes (PDF)
└── templates/
    ├── base.html
    ├── index.html
    ├── auth/
    ├── admin/                  # dashboard · companies · students · drives
    │                             applications · stats · summary
    ├── company/                # dashboard · profile · drives · applications
    └── student/                # dashboard · profile · history
```

---

## Data Models

```
User ──┬── StudentProfile ──── Application ──┐
       │                                      │
       └── CompanyProfile ─── PlacementDrive ─┘
```

| Model | Key Fields |
|---|---|
| `User` | username · email · password_hash · role · is_active · is_approved |
| `StudentProfile` | full_name · roll_number · department · cgpa · phone_no · resume_filename · graduation_year |
| `CompanyProfile` | company_name · industry · website · description · contact_person |
| `PlacementDrive` | title · location · salary_package · eligibility_cgpa · eligible_departments · drive_date · last_apply_date · status |
| `Application` | student_id · drive_id · status · applied_at |

**Application status flow:** `Applied → Shortlisted → Selected / Rejected`

**Drive status flow:** `Pending → Approved / Closed`

---

## Getting Started

### 1. Clone and install dependencies

```bash
git clone https://github.com/Soumyashit-DS/placement-portal.git
cd placement-portal
pip install -r requirements.txt
```

### 2. Run the app

```bash
python app.py
```

The app starts at **http://localhost:5001**. On first run, a default admin account is created automatically:

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

### 3. (Optional) Seed sample data

```bash
python seed.py
```

Creates 2 approved companies, 5 students, and several drives and applications for testing.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `placement-portal-secret-key` | Flask session secret — **change this in production** |

---

## Eligibility Logic

When a student applies to a drive, all three conditions must pass:

1. **CGPA** — student CGPA ≥ drive's minimum CGPA
2. **Department** — student's department is in the drive's eligible departments list (empty = all departments allowed)
3. **Deadline** — today's date ≤ drive's last apply date

The browse page shows an **Eligible** or **Not Eligible** badge on each drive card before the student applies.

---

## Resume Uploads

- PDF only, max **5 MB**
- Stored as `{student_id}_{unix_timestamp}.pdf` in `static/uploads/`
- Old file is only deleted after a successful database commit (prevents data loss on failure)

---

## License

MIT
