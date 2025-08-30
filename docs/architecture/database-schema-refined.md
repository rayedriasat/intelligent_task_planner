# Database Schema (Refined)

The schema includes performance-critical indexes on the `planner_task` and `planner_timeblock` tables to ensure fast queries for the calendar view and scheduling engine.

```sql
-- REFINED SQL Schema for Intelligent Task Planner
-- Version 1.1 - Added performance-critical indexes

-- Task Table
CREATE TABLE `planner_task` (
    `id` INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `description` TEXT NULL,
    `deadline` DATETIME(6) NOT NULL,
    `priority` INT NOT NULL,
    `estimated_hours` DOUBLE PRECISION NOT NULL,
    `min_block_size` DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    `status` VARCHAR(20) NOT NULL,
    `start_time` DATETIME(6) NULL,
    `end_time` DATETIME(6) NULL,
    `is_locked` BOOL NOT NULL DEFAULT FALSE,
    `actual_hours` DOUBLE PRECISION NULL,
    `user_id` INT NOT NULL,
    INDEX `planner_task_user_id_idx` (`user_id`),
    CONSTRAINT `planner_task_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
    INDEX `planner_task_status_idx` (`status`),
    INDEX `planner_task_user_id_start_time_end_time_idx` (`user_id`, `start_time`, `end_time`),
    INDEX `planner_task_user_id_priority_deadline_idx` (`user_id`, `priority`, `deadline`)
);

-- TimeBlock Table
CREATE TABLE `planner_timeblock` (
    `id` INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `start_time` DATETIME(6) NOT NULL,
    `end_time` DATETIME(6) NOT NULL,
    `is_recurring` BOOL NOT NULL DEFAULT FALSE,
    `day_of_week` INT NULL,
    `user_id` INT NOT NULL,
    INDEX `planner_timeblock_user_id_idx` (`user_id`),
    CONSTRAINT `planner_timeblock_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
    INDEX `planner_timeblock_user_id_start_time_end_time_idx` (`user_id`, `start_time`, `end_time`),
    INDEX `planner_timeblock_user_id_is_recurring_idx` (`user_id`, `is_recurring`)
);

-- PomodoroSession Table
CREATE TABLE `planner_pomodorosession` (
    `id` INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `start_time` DATETIME(6) NOT NULL,
    `end_time` DATETIME(6) NOT NULL,
    `task_id` INT NOT NULL,
    INDEX `planner_pomodorosession_task_id_idx` (`task_id`),
    CONSTRAINT `planner_pomodorosession_task_id_fk` FOREIGN KEY (`task_id`) REFERENCES `planner_task` (`id`) ON DELETE CASCADE
);
```
