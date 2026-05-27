# 🎯 RecruitPro CRM
### Recruitment Consultancy Management System

A production-ready, full-featured CRM built with **Python + Streamlit + MySQL** for managing recruitment pipelines, candidate tracking, 90-day automation, and payment collection.

---

## 📋 Table of Contents
1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [Database Setup](#database-setup)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [Usage Guide](#usage-guide)

---

## ✨ Features

| Module | Features |
|--------|----------|
| **Authentication** | Admin/Recruiter login, bcrypt password hashing, session management |
| **Dashboard** | KPI cards, monthly trend charts, status distribution, 90-day alerts |
| **Candidate Management** | Full CRUD, bulk Excel import/export, WhatsApp integration |
| **90-Day Automation** | APScheduler background jobs, auto status updates, notifications |
| **Payment Tracking** | Pending/received tracking, overdue alerts, company-wise revenue |
| **Recruiter Management** | Performance leaderboard, conversion rates, revenue attribution |
| **Company Management** | Client company CRUD, placement history, revenue by client |
| **Notifications** | Real-time alerts for milestones, payment reminders |
| **Settings** | User management, scheduler control, activity logs, system info |
| **WhatsApp** | Pre-built templates for joining reminders, payment follow-ups |

---

## 🛠 Tech Stack

```
Frontend:   Streamlit 1.32
Backend:    Python 3.10+
Database:   MySQL 8.0
ORM:        SQLAlchemy 2.0
Charts:     Plotly 5.20
Scheduler:  APScheduler 3.10
Excel:      Pandas + openpyxl
Auth:       bcrypt
```

---

## 📁 Project Structure

```
recruitment_crm/
├── app.py                          # Main entry point
├── requirements.txt
├── .env                            # Environment config (edit this)
├── seed_demo.py                    # Demo data seeder
│
├── .streamlit/
│   └── config.toml                 # Streamlit theme config
│
├── database/
│   ├── __init__.py
│   ├── models.py                   # SQLAlchemy ORM models
│   ├── connection.py               # DB engine + session management
│   └── schema.sql                  # Raw MySQL schema (reference)
│
├── app/
│   ├── auth/
│   │   └── auth.py                 # Login, session, password hashing
│   │
│   ├── dashboard/
│   │   └── analytics.py            # KPIs, charts, notification queries
│   │
│   ├── candidates/
│   │   └── candidate_service.py    # CRUD, bulk import, 90-day tracker
│   │
│   ├── utils/
│   │   ├── scheduler.py            # APScheduler background jobs
│   │   └── whatsapp.py             # WhatsApp URL + message templates
│   │
│   └── ui/
│       ├── login_page.py
│       ├── sidebar.py
│       ├── dashboard_page.py
│       ├── candidates_page.py
│       ├── add_candidate_page.py
│       ├── payments_page.py
│       ├── recruiters_page.py
│       ├── companies_page.py
│       ├── notifications_page.py
│       └── settings_page.py
│
├── exports/                        # Generated Excel exports
└── uploads/                        # Uploaded resumes/files
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### Step 1: Clone / Download the project
```bash
cd recruitment_crm
```

### Step 2: Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure environment
Edit `.env` with your MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=recruitment_crm
DB_USER=root
DB_PASSWORD=your_mysql_password
```

### Step 5: Set up database
```bash
# Option A: Auto-setup via Python (recommended)
python -c "from database.connection import init_database; init_database()"

# Option B: Manual MySQL setup
mysql -u root -p < database/schema.sql
```

### Step 6: Seed demo data (optional but recommended)
```bash
python seed_demo.py
```

### Step 7: Run the app
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 🔐 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin@123` |
| Recruiter | `neha` | `recruiter@123` |
| Recruiter | `amit` | `recruiter@123` |
| Recruiter | `pooja` | `recruiter@123` |

> ⚠️ Change all passwords immediately in production!

---

## 🗄 Database Setup

### Manual MySQL setup
```sql
CREATE DATABASE recruitment_crm CHARACTER SET utf8mb4;
CREATE USER 'crm_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON recruitment_crm.* TO 'crm_user'@'localhost';
FLUSH PRIVILEGES;
```

Then run `python -c "from database.connection import init_database; init_database()"`

---

## ⚙️ Configuration

All configuration is in `.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=recruitment_crm
DB_USER=root
DB_PASSWORD=your_password

# App
APP_SECRET_KEY=change-this-to-random-string
APP_NAME=RecruitPro CRM

# Scheduler timezone
SCHEDULER_TIMEZONE=Asia/Kolkata
```

---

## 🤖 90-Day Automation

The scheduler runs two jobs automatically:

| Job | Schedule | Description |
|-----|----------|-------------|
| Day Tracking | Every hour | Recalculates days since joining, updates status |
| Overdue Check | Daily 9 AM | Marks payments as overdue after 105 days |

**What happens at milestones:**
- **30 days** → Status updated to "Completed 30 Days", notification sent
- **60 days** → Status updated to "Completed 60 Days", notification sent  
- **90 days** → Status = "Completed 90 Days", `is_90_day_eligible = True`, payment alert created
- **105+ days** → Payment status changed to "Overdue", escalation notification

Manually trigger via **Settings → Scheduler → Run Now**

---

## 📱 WhatsApp Integration

Each candidate profile has WhatsApp buttons that open `https://wa.me/<number>`.

Pre-built message templates:
- 📋 Joining Reminder
- 📄 Document Reminder  
- 🎉 Selection Congratulations
- 👋 General Follow-up
- 💰 Payment Confirmation (for company contacts)

---

## 📤 Excel Import

Template columns for bulk import:
```
Name | Phone | Email | Company | Designation | CTC | 
Selection Date | Expected Joining Date | Payment Amount | Notes
```

Download the template from **Add Candidate → Bulk Import**.

---

## 🚀 Deployment

### Option 1: Streamlit Cloud
1. Push to GitHub (remove `.env`, use Streamlit secrets)
2. Connect repo at `share.streamlit.io`
3. Add secrets in Streamlit Cloud dashboard

### Option 2: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t recruitpro-crm .
docker run -p 8501:8501 --env-file .env recruitpro-crm
```

### Option 3: Linux Server (systemd)
```ini
# /etc/systemd/system/recruitpro.service
[Unit]
Description=RecruitPro CRM
After=network.target mysql.service

[Service]
User=www-data
WorkingDirectory=/opt/recruitment_crm
ExecStart=/opt/recruitment_crm/venv/bin/streamlit run app.py --server.port=8501
Restart=always
EnvironmentFile=/opt/recruitment_crm/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable recruitpro
sudo systemctl start recruitpro
```

### Nginx reverse proxy
```nginx
server {
    listen 80;
    server_name yourcrm.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 📊 Usage Guide

### Adding a Candidate
1. Click **Add Candidate** in sidebar
2. Fill personal info (Name + Phone required)
3. Select Company and Recruiter
4. Set Status and Payment Amount
5. Save → Candidate gets auto-generated ID (CND01001)

### Tracking 90 Days
- Set **Joining Date** when candidate joins
- Scheduler automatically tracks progress
- Dashboard shows "Approaching 90 Days" alert
- At 90 days: notification + payment eligible flag set

### Processing Payment
1. Go to **Payments → Pending Payments**
2. Click 💬 to send WhatsApp follow-up to company
3. Click ✅ **Mark Received** when payment comes in
4. System records payment date and updates status

### Managing Recruiters
1. Go to **Settings → Add Recruiter** (Admin only)
2. Creates login account + recruiter profile
3. Performance auto-calculated on Recruiters page

---

## 🔒 Security Notes

- All passwords hashed with bcrypt (cost factor 12)
- Session-based authentication via Streamlit session_state
- Role-based access: Admin sees all; Recruiter sees their candidates
- Change default passwords before going live
- Use HTTPS in production (via Nginx SSL)
- Store `.env` outside web root

---

## 📞 Support

Built for recruitment consultancies managing candidate placements with 90-day payment milestones.

For issues, check:
1. Database connection in Settings → System Info
2. Scheduler status in Settings → Scheduler
3. Activity logs in Settings → Activity Logs
