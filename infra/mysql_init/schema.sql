USE work_allocation;
CREATE TABLE IF NOT EXISTS resources (
    resource_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialty VARCHAR(50),
    skill_level INT,
    total_cases_handled INT
);
CREATE TABLE IF NOT EXISTS resource_calendar (
    calendar_id VARCHAR(10) PRIMARY KEY,
    resource_id VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    available_from TIME NOT NULL,
    available_to TIME NOT NULL,
    current_workload INT DEFAULT 0,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);
CREATE INDEX IF NOT EXISTS idx_resource_calendar_resource_date ON resource_calendar (resource_id, date);
CREATE TABLE IF NOT EXISTS specialty_mapping (
    work_type VARCHAR(50) PRIMARY KEY,
    required_specialty VARCHAR(50),
    alternate_specialty VARCHAR(50)
);
CREATE TABLE IF NOT EXISTS work_requests (
    work_id VARCHAR(128) PRIMARY KEY,
    -- increased size
    work_type VARCHAR(50) NOT NULL,
    description TEXT,
    priority TINYINT NOT NULL,
    scheduled_timestamp DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to VARCHAR(10),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES resources(resource_id)
);
CREATE INDEX IF NOT EXISTS idx_work_requests_status ON work_requests (status);