package com.hospital.ovarian.inference;

import com.hospital.ovarian.model.ModelSpec;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

/**
 * ONNX 模型推理器（备选实现，桩函数）
 *
 * 何时用：原项目模型成功导出为 .onnx 后，切换 profile=onnx
 * 切换：application.yml spring.profiles.active=onnx
 *
 * 当前桩函数原因：onnxruntime 依赖未在本地 Maven 仓库
 * 接入步骤：
 *   1. mvn dependency:get -Dartifact=com.microsoft.onnxruntime:onnxruntime:1.17.0
 *   2. 取消本类中的 @Profile("stub") 注释（让 @Profile("onnx") 生效）
 *   3. 把 mockPredict 换成 r.get(0).getValue() 的真实结果
 *   4. 删除 import mock 部分
 */
@Slf4j
@Component
@Profile("onnx")
@RequiredArgsConstructor
public class OnnxModelRunner implements ModelRunner {

    private final ModelSpec spec;
    private String backendId = "onnx:stub:onnxruntime-not-installed";

    @EventListener(ApplicationReadyEvent.class)
    public void init() {
        log.warn("OnnxModelRunner currently a STUB. Install onnxruntime dependency then enable real impl.");
    }

    @Override public void load() { log.info("OnnxModelRunner STUB loaded"); }
    @Override public void unload() {}
    @Override public String backendId() { return backendId; }

    @Override
    public double[] predict(String modelName, float[] s, float[][] d, float[] m) {
        throw new IllegalStateException("ONNX model runtime is not installed");
    }
}
