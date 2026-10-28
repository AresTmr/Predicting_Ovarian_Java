package com.hospital.ovarian.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hospital.ovarian.entity.dto.AnalysisRequest;
import com.hospital.ovarian.entity.dto.AnalysisRunResponse;
import com.hospital.ovarian.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.sql.Timestamp;
import java.sql.Clob;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AnalysisRunService {

    private final JdbcTemplate jdbc;
    private final ObjectMapper objectMapper;

    @Value("${model.rpc-url:http://127.0.0.1:8001}")
    private String runtimeUrl;

    @Value("${model.connect-timeout-ms:3000}")
    private int connectTimeoutMs;

    @Value("${model.read-timeout-ms:30000}")
    private int readTimeoutMs;

    public AnalysisRunResponse analyze(AnalysisRequest request) {
        validate(request);
        String runId = UUID.randomUUID().toString();
        String requestJson = writeJson(request);
        Timestamp startedAt = Timestamp.valueOf(LocalDateTime.now());
        try {
            RestTemplate restTemplate = restTemplate();
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<AnalysisRequest> entity = new HttpEntity<>(request, headers);
            ResponseEntity<JsonNode> response = restTemplate.postForEntity(
                runtimeUrl + "/analyze",
                entity,
                JsonNode.class
            );
            JsonNode result = response.getBody();
            if (result == null || !"OK".equals(result.path("status").asText())) {
                throw new BusinessException(503, "模型服务返回了无效结果");
            }
            String modelVersion = result.path("model").path("dose").asText("local-python-runtime")
                + " / " + result.path("model").path("efficacyRunId").asText("");
            save(runId, request, "OK", modelVersion, requestJson, writeJson(result), null, startedAt);
            return new AnalysisRunResponse(runId, "OK", result, null);
        } catch (ResourceAccessException ex) {
            String message = "模型服务不可用，未生成临床建议";
            save(runId, request, "FAILED", null, requestJson, null, message, startedAt);
            throw new BusinessException(503, message);
        } catch (BusinessException ex) {
            save(runId, request, "FAILED", null, requestJson, null, ex.getMessage(), startedAt);
            throw ex;
        } catch (Exception ex) {
            String message = "模型计算失败，未生成临床建议";
            save(runId, request, "FAILED", null, requestJson, null, message, startedAt);
            log.error("Analysis run failed: runId={}", runId, ex);
            throw new BusinessException(503, message);
        }
    }

    public AnalysisRunResponse get(String runId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
            "SELECT run_id, status, result_json, error_message FROM analysis_run WHERE run_id = ?",
            runId
        );
        if (rows.isEmpty()) {
            throw BusinessException.notFound("分析结果");
        }
        Map<String, Object> row = rows.get(0);
        JsonNode result = null;
        Object resultJson = row.get("RESULT_JSON");
        if (resultJson != null) {
            try {
                String jsonText;
                if (resultJson instanceof Clob) {
                    Clob clob = (Clob) resultJson;
                    jsonText = clob.getSubString(1, (int) clob.length());
                } else {
                    jsonText = resultJson.toString();
                }
                result = objectMapper.readTree(jsonText);
            } catch (Exception ex) {
                throw new BusinessException(500, "分析结果读取失败");
            }
        }
        return new AnalysisRunResponse(
            String.valueOf(row.get("RUN_ID")),
            String.valueOf(row.get("STATUS")),
            result,
            row.get("ERROR_MESSAGE") == null ? null : String.valueOf(row.get("ERROR_MESSAGE"))
        );
    }

    public JsonNode health() {
        try {
            return restTemplate().getForObject(runtimeUrl + "/health", JsonNode.class);
        } catch (Exception ex) {
            throw new BusinessException(503, "模型服务不可用");
        }
    }

    private void save(
        String runId,
        AnalysisRequest request,
        String status,
        String modelVersion,
        String requestJson,
        String resultJson,
        String errorMessage,
        Timestamp startedAt
    ) {
        String patientUuid = null;
        if (request.getPatient() != null) {
            Object value = request.getPatient().get("patientUuid");
            if (value == null) value = request.getPatient().get("patient_id");
            patientUuid = value == null ? null : String.valueOf(value);
        }
        jdbc.update(
            "INSERT INTO analysis_run " +
                "(run_id, patient_uuid, status, model_version, request_json, result_json, error_message, created_at, finished_at) " +
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            runId,
            patientUuid,
            status,
            modelVersion,
            requestJson,
            resultJson,
            errorMessage,
            startedAt,
            Timestamp.valueOf(LocalDateTime.now())
        );
    }

    private void validate(AnalysisRequest request) {
        if (request == null || request.getPatient() == null || request.getPatient().isEmpty()) {
            throw BusinessException.invalidParam("patient");
        }
        if (request.getRecords() == null || request.getRecords().isEmpty()) {
            throw BusinessException.invalidParam("records");
        }
    }

    private RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(connectTimeoutMs);
        factory.setReadTimeout(readTimeoutMs);
        return new RestTemplate(factory);
    }

    private String writeJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception ex) {
            throw new BusinessException(500, "请求序列化失败");
        }
    }
}
