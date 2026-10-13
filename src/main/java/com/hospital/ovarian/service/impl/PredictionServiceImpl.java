package com.hospital.ovarian.service.impl;

import com.hospital.ovarian.dao.VisitMapper;
import com.hospital.ovarian.entity.Visit;
import com.hospital.ovarian.entity.dto.PredictionDto;
import com.hospital.ovarian.entity.dto.VisitDto;
import com.hospital.ovarian.exception.BusinessException;
import com.hospital.ovarian.service.PredictionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import java.math.BigDecimal;

@Slf4j
@Service
@RequiredArgsConstructor
public class PredictionServiceImpl implements PredictionService {

    private final VisitMapper visitMapper;

    @Override
    public PredictionDto predict(Long visitPk) {
        Visit v = visitMapper.selectById(visitPk);
        if (v == null) throw BusinessException.notFound("复诊");
        return doPredict(toFeatures(v));
    }

    @Override
    public PredictionDto predictFromFeatures(VisitDto features) {
        return doPredict(features);
    }

    private PredictionDto doPredict(VisitDto f) {
        long t0 = System.currentTimeMillis();
        PredictionDto result = new PredictionDto();
        result.setModelVersion("stub-v1.0.0");
        BigDecimal e2 = f.getE2() != null ? f.getE2() : BigDecimal.ZERO;
        int total = f.getFollicleTotalCount() != null ? f.getFollicleTotalCount() : 0;
        int above18 = f.getFollicleSizeAbove18() != null ? f.getFollicleSizeAbove18() : 0;
        int fsh = 150 + Math.min(total, 20) * 25;
        if (above18 >= 3 || e2.compareTo(new BigDecimal("3000")) > 0) {
            fsh = Math.max(75, fsh - 50);
        }
        int hmg = total < 5 ? 75 : 0;
        int lh = 75;
        result.setPredictedFshDose(fsh);
        result.setPredictedLhDose(lh);
        result.setPredictedHmgDose(hmg);
        result.setConfidenceScore(new BigDecimal("0.85"));
        result.setInferenceTimeMs((int) (System.currentTimeMillis() - t0));
        return result;
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
