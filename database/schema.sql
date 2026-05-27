-- ============================================================
-- RecruitPro CRM - MySQL Database Schema
-- Run this script to initialize the database manually
-- SQLAlchemy will also auto-create these via init_database()
-- ============================================================

CREATE DATABASE IF NOT EXISTS recruitment_crm
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE recruitment_crm;

-- ── Users ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    email           VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    role            ENUM('admin','recruiter','manager') NOT NULL DEFAULT 'recruiter',
    phone           VARCHAR(20),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login      DATETIME,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role_active (role, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Companies ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(150) NOT NULL,
    industry            VARCHAR(100),
    contact_person      VARCHAR(100),
    contact_email       VARCHAR(100),
    contact_phone       VARCHAR(20),
    address             TEXT,
    website             VARCHAR(200),
    payment_terms_days  INT NOT NULL DEFAULT 90,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Recruiters ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recruiters (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNIQUE,
    employee_id     VARCHAR(20) UNIQUE,
    department      VARCHAR(100),
    specialization  VARCHAR(200),
    target_monthly  INT NOT NULL DEFAULT 0,
    joining_date    DATE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Candidates ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidates (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id            VARCHAR(20) NOT NULL UNIQUE,
    name                    VARCHAR(100) NOT NULL,
    phone                   VARCHAR(20)  NOT NULL,
    alternate_phone         VARCHAR(20),
    email                   VARCHAR(100),
    company_id              INT,
    recruiter_id            INT,
    designation             VARCHAR(100),
    ctc                     DECIMAL(12,2),

    -- Dates
    selection_date          DATE,
    joining_date            DATE,
    expected_joining_date   DATE,

    -- Status
    status ENUM(
        'Interview Scheduled','Selected','Joined','Drop',
        'Completed 30 Days','Completed 60 Days','Completed 90 Days',
        'Payment Pending','Payment Received'
    ) NOT NULL DEFAULT 'Selected',

    -- Payment
    payment_status  ENUM('Pending','Invoiced','Received','Overdue') DEFAULT 'Pending',
    payment_amount  DECIMAL(12,2) DEFAULT 0.00,
    payment_received_date   DATE,
    invoice_number          VARCHAR(50),
    invoice_date            DATE,

    -- Tracking
    days_completed          INT DEFAULT 0,
    is_90_day_eligible      BOOLEAN NOT NULL DEFAULT FALSE,
    drop_reason             TEXT,
    resume_path             VARCHAR(500),
    notes                   TEXT,

    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id)   REFERENCES companies(id)  ON DELETE SET NULL,
    FOREIGN KEY (recruiter_id) REFERENCES recruiters(id) ON DELETE SET NULL,

    INDEX idx_candidate_id (candidate_id),
    INDEX idx_name         (name),
    INDEX idx_phone        (phone),
    INDEX idx_status       (status),
    INDEX idx_joining_date (joining_date),
    INDEX idx_payment      (payment_status, is_90_day_eligible)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Payments ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    payment_ref     VARCHAR(50) NOT NULL UNIQUE,
    candidate_id    INT,
    company_id      INT,
    amount          DECIMAL(12,2) NOT NULL,
    status          ENUM('Pending','Invoiced','Received','Overdue') DEFAULT 'Pending',
    due_date        DATE,
    received_date   DATE,
    invoice_number  VARCHAR(50),
    invoice_date    DATE,
    payment_mode    VARCHAR(50),
    transaction_id  VARCHAR(100),
    notes           TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL,
    FOREIGN KEY (company_id)   REFERENCES companies(id)  ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Notifications ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT,
    candidate_id    INT,
    type            ENUM('30_days','60_days','90_days','payment_due','payment_overdue','general') NOT NULL,
    title           VARCHAR(200) NOT NULL,
    message         TEXT NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)      REFERENCES users(id)      ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL,
    INDEX idx_user_unread (user_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Candidate Timeline ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidate_timeline (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id    INT,
    event_type      VARCHAR(50) NOT NULL,
    event_date      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    performed_by    VARCHAR(100),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    INDEX idx_candidate_timeline (candidate_id, event_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Activity Logs ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activity_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT,
    candidate_id    INT,
    action          VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(50),
    entity_id       INT,
    details         TEXT,
    ip_address      VARCHAR(45),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)      REFERENCES users(id)      ON DELETE SET NULL,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL,
    INDEX idx_action     (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Default Admin User ─────────────────────────────────────
-- Password: admin@123  (bcrypt hash — will be overwritten on first run)
INSERT IGNORE INTO users (username, email, password_hash, full_name, role)
VALUES (
    'admin',
    'admin@recruitpro.com',
    '$2b$12$placeholder_run_app_to_seed',
    'System Administrator',
    'admin'
);

-- ── Sample Companies ───────────────────────────────────────
INSERT IGNORE INTO companies (name, industry, contact_person, contact_phone)
VALUES
    ('TechCorp Solutions', 'IT/Software',       'Rahul Sharma',   '9876543210'),
    ('FinServ India',      'Banking/Finance',    'Priya Mehta',    '9876543211'),
    ('MediCare Hospitals', 'Healthcare',         'Dr. Suresh Kumar','9876543212');
