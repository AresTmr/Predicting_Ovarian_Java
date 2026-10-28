package com.hospital.ovarian.entity.dto;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class PredictionDto {

    private Long visitPk;
    private BigDecimal confidenceScore;
    private String modelVersion;
    private Integer inferenceTimeMs;


    private Integer predictedFshDose;
    private Integer predictedLhDose;
    private Integer predictedHmgDose;
}
