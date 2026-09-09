package com.hospital.ovarian.entity.dto;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class VisitDto {

    private Integer visitNo;
    private Integer stimulationDay;
    private Integer daysSinceLastVisit;
    private LocalDate visitDate;

    private BigDecimal e2;
    private BigDecimal lh;
    private BigDecimal p;
    private BigDecimal fsh;
    private BigDecimal endometriumThickness;

    private Integer follicleTotalCount;
    private Integer follicleLeftCount;
    private Integer follicleRightCount;
    private BigDecimal follicleMaxDiameter;
    private BigDecimal follicleAvgDiameter;
    private Integer follicleSizeUnder10;
    private Integer follicleSize10_12;
    private Integer follicleSize13_15;
    private Integer follicleSize16_18;
    private Integer follicleSizeAbove18;

    private BigDecimal fshDose;
    private BigDecimal lhDose;
    private BigDecimal hmgDose;
}
