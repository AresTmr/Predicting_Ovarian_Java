package com.hospital.ovarian.entity.dto;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class AnalysisRunResponse {

    private String runId;
    private String status;
    private JsonNode result;
    private String errorMessage;
}
