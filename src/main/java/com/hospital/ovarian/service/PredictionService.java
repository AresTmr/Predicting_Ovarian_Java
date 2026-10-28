package com.hospital.ovarian.service;

import com.hospital.ovarian.entity.dto.PredictionDto;
import com.hospital.ovarian.entity.dto.VisitDto;

public interface PredictionService {

    /**
     * 基于当前 visit 预测下一次复诊的 Gn 剂量
     * @param visitPk 当前 visit（输入）
     * @return 预测的 FSH/LH/HMG 剂量
     */
    PredictionDto predict(Long visitPk);

    /**
     * 直接基于特征向量预测（前端表单未保存也能调）
     */
    PredictionDto predictFromFeatures(VisitDto features);
}
