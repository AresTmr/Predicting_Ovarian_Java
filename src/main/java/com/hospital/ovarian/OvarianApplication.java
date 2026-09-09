package com.hospital.ovarian;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 启动入口（精简编译版本 - 仅 Web）
 */
@SpringBootApplication
public class OvarianApplication {

    public static void main(String[] args) {
        SpringApplication.run(OvarianApplication.class, args);
        System.out.println("\n============================================================");
        System.out.println("  Predicting Ovarian Java  v2.2.0  (build-test mode)");
        System.out.println("  Port: 18501");
        System.out.println("  NOTE: Database / Inference / Swagger are stubbed");
        System.out.println("  This is a compile-validation build.");
        System.out.println("============================================================\n");
    }
}
