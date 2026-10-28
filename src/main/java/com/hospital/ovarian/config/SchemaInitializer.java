package com.hospital.ovarian.config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.init.ScriptUtils;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;

@Slf4j
@Component
@RequiredArgsConstructor
public class SchemaInitializer implements CommandLineRunner {

    private final DataSource dataSource;
    private final JdbcTemplate jdbc;

    @Override
    public void run(String... args) throws Exception {
        Integer tableCount = jdbc.queryForObject(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='PUBLIC' AND table_name='FACT_PATIENT'",
            Integer.class
        );
        if (tableCount != null && tableCount > 0) {
            log.info("schema already exists, skip");
            return;
        }
        try (Connection conn = dataSource.getConnection()) {
            ClassPathResource resource = new ClassPathResource("schema.sql");
            ScriptUtils.executeSqlScript(conn, resource);
            log.info("schema.sql executed");
        }
    }
}
