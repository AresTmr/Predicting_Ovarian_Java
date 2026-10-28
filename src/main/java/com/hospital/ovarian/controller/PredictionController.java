package com.hospital.ovarian.controller;

import com.hospital.ovarian.entity.dto.PredictionDto;
import com.hospital.ovarian.entity.dto.VisitDto;
import com.hospital.ovarian.service.PredictionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/predict")
@RequiredArgsConstructor
public class PredictionController {

    private final PredictionService predictionService;

    /** 基于已有 visit 预测下一次剂量 */
    @PostMapping("/visit/{visitPk}")
    public PredictionDto predictByVisit(@PathVariable Long visitPk) {
        return predictionService.predict(visitPk);
    }

    /** 基于表单特征直接预测（前端"生成监测结果"按钮，未保存时也能调） */
    @PostMapping
    public PredictionDto predict(@RequestBody VisitDto features) {
        return predictionService.predictFromFeatures(features);
    }
}
