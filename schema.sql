-- =============================================================================
-- MySQL Database Schema for AI-Powered Research Paper Intelligence System
-- =============================================================================

CREATE DATABASE IF NOT EXISTS research_paper_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE research_paper_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Papers Table
CREATE TABLE IF NOT EXISTS papers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(500) NOT NULL,
    authors VARCHAR(500) DEFAULT NULL,
    publication_year INT DEFAULT NULL,
    journal_conference VARCHAR(255) DEFAULT NULL,
    doi VARCHAR(100) DEFAULT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    total_pages INT DEFAULT 0,
    abstract TEXT DEFAULT NULL,
    processing_status ENUM('uploaded', 'processing', 'completed', 'failed') DEFAULT 'uploaded',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_papers_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FULLTEXT INDEX ft_paper_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Paper Sections Table
CREATE TABLE IF NOT EXISTS paper_sections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paper_id INT NOT NULL,
    section_name VARCHAR(100) NOT NULL,
    section_order INT NOT NULL DEFAULT 1,
    page_number INT DEFAULT NULL,
    content LONGTEXT NOT NULL,
    CONSTRAINT fk_sections_paper FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    FULLTEXT INDEX ft_section_content (content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Paper Keywords Table
CREATE TABLE IF NOT EXISTS paper_keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paper_id INT NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    relevance_score FLOAT NOT NULL DEFAULT 1.0,
    CONSTRAINT fk_keywords_paper FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    INDEX idx_keyword (keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Search Logs Table
CREATE TABLE IF NOT EXISTS search_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL,
    query_text VARCHAR(255) NOT NULL,
    search_type VARCHAR(50) DEFAULT 'keyword',
    results_count INT DEFAULT 0,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
