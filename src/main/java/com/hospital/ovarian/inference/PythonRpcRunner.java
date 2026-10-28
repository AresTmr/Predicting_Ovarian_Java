package com.hospital.ovarian.inference;

import com.hospital.ovarian.model.ModelSpec;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Python 推理服务调用器（RPC over HTTP）
 * 通过 HTTP POST 调 Python FastAPI 服务（inference_service.py）
 * 不读、不改原项目任何代码
 */
@Slf4j
@Component
@Profile("rpc")
@RequiredArgsConstructor
public class PythonRpcRunner implements ModelRunner {

    private final ModelSpec spec;
    private RestTemplate http = new RestTemplate();
    private String backendId = "python-rpc:pending";

    @EventListener(ApplicationReadyEvent.class)
    public void init() { load(); }

    @Override
    public void load() {
        this.http = new RestTemplate();
        backendId = "python-rpc:" + spec.getRpcUrl();
        log.info("PythonRpcRunner ready at {}", spec.getRpcUrl());
    }

    @Override
    public void unload() { this.http = null; }

    @Override
    public double[] predict(String modelName, float[] staticF, float[][] dynamicF, float[] mask) {
        if (http == null) {
            throw new IllegalStateException("Python RPC client is not initialized");
        }
        try {
            HttpHeaders h = new HttpHeaders();
            h.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = new HashMap<>();
            body.put("model", modelName);
            body.put("static", toList(staticF));
            body.put("dynamic", toList(dynamicF));
            body.put("mask", toList(mask));

            @SuppressWarnings("rawtypes")
            Map resp = http.postForObject(spec.getRpcUrl() + "/predict",
                    new HttpEntity<>(body, h), Map.class);
            if (resp == null) {
                throw new IllegalStateException("Python RPC returned an empty response");
            }
            Object output = resp.get("output");
            if (output instanceof List) {
                List<?> list = (List<?>) output;
                double[] out = new double[list.size()];
                for (int i = 0; i < list.size(); i++) out[i] = ((Number) list.get(i)).doubleValue();
                return out;
            }
            throw new IllegalStateException("Python RPC response has no output list");
        } catch (Exception e) {
            log.error("RPC predict failed for model={}", modelName, e);
            throw new IllegalStateException("Python RPC prediction failed for " + modelName, e);
        }
    }

    @Override
    public String backendId() { return backendId; }

    private static List<Float> toList(float[] a) {
        List<Float> l = new java.util.ArrayList<>(a.length);
        for (float v : a) l.add(v);
        return l;
    }
    private static List<List<Float>> toList(float[][] a) {
        List<List<Float>> l = new java.util.ArrayList<>(a.length);
        for (float[] row : a) l.add(toList(row));
        return l;
    }

}
