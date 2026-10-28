package com.hospital.ovarian.entity.dto;

import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class AnalysisRequest {

    private Map<String, Object> patient;
    private List<Map<String, Object>> records;
}
