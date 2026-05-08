-- ══════════════════════════════════════════════
--  EduGenie — MySQL Database Setup
--  Run: mysql -u root -p < schema.sql
-- ══════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS edugenie
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE edugenie;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id    INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(100) UNIQUE NOT NULL,
    password   VARCHAR(255) NOT NULL,          -- bcrypt hashed
    role       ENUM('student', 'teacher') DEFAULT 'student',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Quiz scores / performance history
CREATE TABLE IF NOT EXISTS quiz_scores (
    score_id   INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    pdf_name   VARCHAR(255),
    score      INT DEFAULT 0,
    total      INT DEFAULT 0,
    percentage FLOAT DEFAULT 0.0,
    taken_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_scores_user ON quiz_scores(user_id);
CREATE INDEX idx_scores_date ON quiz_scores(taken_at);

SELECT 'EduGenie database setup complete.' AS status;
