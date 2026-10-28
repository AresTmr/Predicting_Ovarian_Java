package com.hospital.ovarian.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.hospital.ovarian.entity.dto.AnalysisRequest;
import com.hospital.ovarian.entity.dto.AnalysisRunResponse;
import com.hospital.ovarian.service.AnalysisRunService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/recommendation-runs")
@RequiredArgsConstructor
public class AnalysisController {

    private final AnalysisRunService analysisRunService;

    @PostMapping
    public AnalysisRunResponse analyze(@RequestBody AnalysisRequest request) {
        return analysisRunService.analyze(request);
    }

    @GetMapping("/{runId}")
    public AnalysisRunResponse get(@PathVariable String runId) {
        return analysisRunService.get(runId);
    }

    @GetMapping("/runtime/health")
    public JsonNode health() {
        return analysisRunService.health();
    }
}
