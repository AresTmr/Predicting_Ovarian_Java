package com.hospital.ovarian.inference;

import com.hospital.ovarian.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * 业务层推理服务
 * - 完全不依赖具体模型后端
 * - 通过 Spring 注入 ModelRunner 接口
 * - 当前实现 = PythonRpcRunner (active profile=rpc)
 * - 换 ONNX：切换 profile=onnx，零业务代码改动
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class InferenceService {

    private final ModelRunner runner;

    public String getBackendId() {
        return runner.backendId();
    }

    /**
     * 三个模型并行推理（FSH / LH / HMG）
     * @return ModelOutput(fsh, lh, hmg, backendId)
     */
    public ModelOutput predictAll(float[] staticF, float[][] dynamicF, float[] mask) {
        try {
            double[] fsh  = runner.predict("fsh",  staticF, dynamicF, mask);
            double[] lh   = runner.predict("lh",   staticF, dynamicF, mask);
            double[] hmg  = runner.predict("hmg",  staticF, dynamicF, mask);
            log.debug("Inference OK: backend={} fsh={} lh={} hmg={}",
                    runner.backendId(), fsh[0], lh[0], hmg[0]);
            return new ModelOutput(fsh, lh, hmg, runner.backendId());
        } catch (Exception e) {
            log.error("Inference failed", e);
            throw new BusinessException(503, "模型推理失败，未生成临床建议");
        }
    }

    /**
     * 模型输出 DTO（final 字段，让业务层可读 .fsh .lh .hmg .backendId）
     */
    public static class ModelOutput {
        public final double[] fsh;
        public final double[] lh;
        public final double[] hmg;
        public final String backendId;

        public ModelOutput(double[] fsh, double[] lh, double[] hmg, String backendId) {
            this.fsh = fsh;
            this.lh = lh;
            this.hmg = hmg;
            this.backendId = backendId;
        }
    }
}
