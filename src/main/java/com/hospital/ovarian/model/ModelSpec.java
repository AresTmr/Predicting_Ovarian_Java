package com.hospital.ovarian.model;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import java.util.Map;

@Data
@Component
@ConfigurationProperties(prefix = "model")
public class ModelSpec {
    private String path = "./models";
    private String active = "rpc";
    private String rpcUrl = "http://127.0.0.1:8001";
    private Map<String, String> models;
}