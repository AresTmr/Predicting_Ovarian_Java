package com.hospital.ovarian.config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class AnalysisSchemaInitializer implements CommandLineRunner {

    private final JdbcTemplate jdbc;

    @Override
    public void run(String... args) {
        jdbc.execute(
            "CREATE TABLE IF NOT EXISTS analysis_run (" +
                "run_id VARCHAR(36) PRIMARY KEY, " +
                "patient_uuid VARCHAR(64), " +
                "status VARCHAR(16) NOT NULL, " +
                "model_version VARCHAR(128), " +
                "request_json CLOB, " +
                "result_json CLOB, " +
                "error_message VARCHAR(1000), " +
                "created_at TIMESTAMP NOT NULL, " +
                "finished_at TIMESTAMP" +
                ")"
        );
        log.info("analysis_run schema is ready");
    }
}
