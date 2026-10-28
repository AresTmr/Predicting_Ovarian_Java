-- 字典表
CREATE TABLE IF NOT EXISTS dim_protocol (
    protocol_id INT PRIMARY KEY AUTO_INCREMENT,
    protocol_code VARCHAR(32) UNIQUE NOT NULL,
    protocol_name VARCHAR(64) NOT NULL,
    description VARCHAR(256),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dim_infertility_type (
    type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_code VARCHAR(32) UNIQUE NOT NULL,
    type_name VARCHAR(64) NOT NULL
);

-- 患者主表
CREATE TABLE IF NOT EXISTS fact_patient (
    patient_pk BIGINT PRIMARY KEY AUTO_INCREMENT,
    patient_uuid VARCHAR(32) UNIQUE NOT NULL,
    case_no VARCHAR(32) UNIQUE NOT NULL,
    case_no_hash VARCHAR(64),
    age INT NOT NULL,
    bmi DECIMAL(5,2) NOT NULL,
    amh DECIMAL(6,3) NOT NULL,
    afc INT NOT NULL,
    basal_fsh DECIMAL(6,2) NOT NULL,
    basal_lh DECIMAL(6,2) NOT NULL,
    basal_e2 DECIMAL(8,2) NOT NULL,
    basal_p DECIMAL(6,2) NOT NULL,
    infertility_years DECIMAL(4,1),
    protocol_id INT,
    infertility_type_id INT,
    source_type VARCHAR(16) NOT NULL,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_archived BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_patient_case_no ON fact_patient(case_no);

-- 促排周期
CREATE TABLE IF NOT EXISTS fact_cycle (
    cycle_pk BIGINT PRIMARY KEY AUTO_INCREMENT,
    patient_pk BIGINT NOT NULL,
    cycle_no INT NOT NULL,
    cycle_start_date DATE,
    cycle_status VARCHAR(16) DEFAULT 'ACTIVE',
    cycle_end_date DATE,
    reserve_grade VARCHAR(4),
    reserve_index DECIMAL(5,2),
    risk_decline VARCHAR(64),
    expected_oocytes INT,
    ohss_risk_level VARCHAR(16),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_cycle UNIQUE (patient_pk, cycle_no),
    CONSTRAINT fk_cycle_patient FOREIGN KEY (patient_pk) REFERENCES fact_patient(patient_pk)
);

-- 复诊记录
CREATE TABLE IF NOT EXISTS fact_visit (
    visit_pk BIGINT PRIMARY KEY AUTO_INCREMENT,
    cycle_pk BIGINT NOT NULL,
    visit_no INT NOT NULL,
    stimulation_day INT NOT NULL,
    days_since_last_visit INT NOT NULL DEFAULT 0,
    visit_date DATE,
    e2 DECIMAL(8,2),
    lh DECIMAL(6,2),
    p DECIMAL(6,2),
    fsh DECIMAL(6,2),
    endometrium_thickness DECIMAL(5,1),
    follicle_total_count INT,
    follicle_left_count INT,
    follicle_right_count INT,
    follicle_max_diameter DECIMAL(5,2),
    follicle_avg_diameter DECIMAL(5,2),
    follicle_size_under_10 INT,
    follicle_size_10_12 INT,
    follicle_size_13_15 INT,
    follicle_size_16_18 INT,
    follicle_size_above_18 INT,
    fsh_dose DECIMAL(8,2) DEFAULT 0,
    lh_dose DECIMAL(8,2) DEFAULT 0,
    hmg_dose DECIMAL(8,2) DEFAULT 0,
    note VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_visit UNIQUE (cycle_pk, visit_no),
    CONSTRAINT fk_visit_cycle FOREIGN KEY (cycle_pk) REFERENCES fact_cycle(cycle_pk)
);

-- 预测结果
CREATE TABLE IF NOT EXISTS fact_prediction (
    prediction_pk BIGINT PRIMARY KEY AUTO_INCREMENT,
    visit_pk BIGINT NOT NULL,
    predicted_fsh_dose DECIMAL(8,2),
    predicted_lh_dose DECIMAL(8,2),
    predicted_hmg_dose DECIMAL(8,2),
    confidence_score DECIMAL(5,4),
    top_features TEXT,
    model_version VARCHAR(32) NOT NULL,
    inference_time_ms INT,
    actual_fsh_dose DECIMAL(8,2),
    actual_lh_dose DECIMAL(8,2),
    actual_hmg_dose DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pred_visit FOREIGN KEY (visit_pk) REFERENCES fact_visit(visit_pk)
);

-- 病历号访问审计
CREATE TABLE IF NOT EXISTS audit_case_no_access (
    access_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    case_no_hash VARCHAR(64) NOT NULL,
    access_action VARCHAR(32) NOT NULL,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    client_ip VARCHAR(45)
);

-- 字典初始数据
-- 用 MERGE 而非 INSERT：保证脚本可重复执行（重启时字典表已存在也不会主键冲突）
MERGE INTO dim_protocol (protocol_code, protocol_name) KEY(protocol_code) VALUES
    ('GNRHA_ULTRALONG', '超长方案'),
    ('GNRHA_LONG', '长方案'),
    ('GNRHA_SHORT', '短方案'),
    ('ANTAGONIST', '拮抗剂方案'),
    ('MILD', '微刺激方案'),
    ('NATURAL', '自然周期'),
    ('OTHER', '其他');

MERGE INTO dim_infertility_type (type_code, type_name) KEY(type_code) VALUES
    ('PRIMARY', '原发不孕'),
    ('SECONDARY', '继发不孕');
