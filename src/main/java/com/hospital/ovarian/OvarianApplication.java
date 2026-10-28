package com.hospital.ovarian;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 启动入口（MyBatis-Plus + H2 + Web）
 */
@SpringBootApplication

@MapperScan("com.hospital.ovarian.dao")
public class OvarianApplication {

    public static void main(String[] args) {
        SpringApplication.run(OvarianApplication.class, args);
        System.out.println("\n============================================================");
        System.out.println("  Predicting Ovarian Java  v2.2.0  (H2 + MyBatis-Plus)");
        System.out.println("  Port: 18502");
        System.out.println("  H2 Console: http://127.0.0.1:18502/h2-console");
        System.out.println("============================================================\n");
    }
}


