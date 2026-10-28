package com.hospital.ovarian.service.impl;

import com.hospital.ovarian.dao.VisitMapper;
import com.hospital.ovarian.entity.Visit;
import com.hospital.ovarian.entity.dto.PredictionDto;
import com.hospital.ovarian.entity.dto.VisitDto;
import com.hospital.ovarian.exception.BusinessException;
import com.hospital.ovarian.inference.InferenceService;
import com.hospital.ovarian.inference.InferenceService.ModelOutput;
import com.hospital.ovarian.service.PredictionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * 预测服务（业务层，桥接推理层和前端展示）
 * - 单个 visitPk：调 inferenceService.predictAll，调 3 个模型
 * - 返回 PredictionDto 包含：FSH / LH / HMG 三个剂量 + 获卵数 + OHSS 风险
 * - 底层走 InferenceService 抽象，可换 ONNX / RPC
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PredictionServiceImpl implements PredictionService {

    private final VisitMapper visitMapper;
    private final InferenceService inference;

    @Override
    public PredictionDto predict(Long visitPk) {
        Visit v = visitMapper.selectById(visitPk);
        if (v == null) throw BusinessException.notFound("复诊");
        PredictionDto result = predictFromFeatures(toFeatures(v));
        result.setVisitPk(visitPk);
        return result;
    }

    @Override
    public PredictionDto predictFromFeatures(VisitDto features) {
        // 1. 提取 float[] 输入
        float[] staticF  = new float[]{
            features.getAge() != null ? features.getAge().floatValue() : 30f,
            features.getBmi() != null ? features.getBmi().floatValue() : 21f,
            features.getAfc() != null ? features.getAfc().floatValue() : 8f,
            features.getAmh() != null ? features.getAmh().floatValue() : 2f,
            features.getBasalFsh() != null ? features.getBasalFsh().floatValue() : 6f
        };
        int time = features.getFollicleTotalCount() == null ? 1 : Math.max(1, features.getFollicleTotalCount());
        float[][] dynamicF = new float[time][3];
        float[] mask = new float[time];
        for (int i = 0; i < time; i++) {
            dynamicF[i][0] = features.getE2() != null ? features.getE2().floatValue() / 100f : 0.5f;
            dynamicF[i][1] = features.getFollicleTotalCount() != null ? features.getFollicleTotalCount().floatValue() / 20f : 0.4f;
            dynamicF[i][2] = (float) i;
            mask[i] = 1.0f;
        }

        // 2. 调 inference（走 RPC 或 ONNX）
        long t0 = System.currentTimeMillis();
        ModelOutput out = inference.predictAll(staticF, dynamicF, mask);
        long cost = System.currentTimeMillis() - t0;

        // 3. 组装返回（FSH 第一个值=LH 第二=HMG 第三）
        // 0=dose, 1=oocytes, 2=confidence
        PredictionDto result = new PredictionDto();
        result.setModelVersion("backend:" + out.backendId);
        result.setPredictedFshDose(toDose(out.fsh[0]));
        result.setPredictedLhDose(toDose(out.lh[0]));
        result.setPredictedHmgDose(toDose(out.hmg[0]));
        result.setConfidenceScore(toScore((out.fsh[2] + out.lh[2] + out.hmg[2]) / 3.0));
        result.setInferenceTimeMs((int) cost);
        return result;
    }

    /** 剂量（IU/天）取整 */
    private Integer toDose(double d) {
        return (int) Math.round(d);
    }

    /** 置信度（0~1）保留 4 位小数 */
    private BigDecimal toScore(double d) {
        return BigDecimal.valueOf(d).setScale(4, RoundingMode.HALF_UP);
    }

    private VisitDto toFeatures(Visit v) {
        VisitDto f = new VisitDto();
        f.setE2(v.getE2()); f.setLh(v.getLh()); f.setP(v.getP()); f.setFsh(v.getFsh());
        f.setEndometriumThickness(v.getEndometriumThickness());
        f.setFollicleTotalCount(v.getFollicleTotalCount());
        f.setFollicleLeftCount(v.getFollicleLeftCount());
        f.setFollicleRightCount(v.getFollicleRightCount());
        f.setFollicleMaxDiameter(v.getFollicleMaxDiameter());
        f.setFollicleAvgDiameter(v.getFollicleAvgDiameter());
        f.setFollicleSizeUnder10(v.getFollicleSizeUnder10());
        f.setFollicleSize10_12(v.getFollicleSize10_12());
        f.setFollicleSize13_15(v.getFollicleSize13_15());
        f.setFollicleSize16_18(v.getFollicleSize16_18());
        f.setFollicleSizeAbove18(v.getFollicleSizeAbove18());
        return f;
    }
}
