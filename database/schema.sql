-- database/schema.sql
-- Run this once on the Raspberry Pi to prepare the MySQL database.
--
--   mysql -u hasin -p < database/schema.sql

CREATE DATABASE IF NOT EXISTS road CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE road;

-- ── Road damage detections ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS detected_road_conditions (
    id           INT UNSIGNED   NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(50)    NOT NULL COMMENT 'Pothole | Crack | etc.',
    latitude     DECIMAL(10, 7) NOT NULL,
    longitude    DECIMAL(10, 7) NOT NULL,
    confidence   FLOAT          DEFAULT NULL COMMENT 'YOLO confidence score 0–1',
    source       VARCHAR(20)    DEFAULT ''vision'' COMMENT 'vision | accelerometer | combined',
    detected_at  TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name       (name),
    INDEX idx_location   (latitude, longitude),
    INDEX idx_detected   (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
