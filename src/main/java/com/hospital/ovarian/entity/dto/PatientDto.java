package com.hospital.ovarian.entity.dto;

import lombok.Data;
import java.math.BigDecimal;
import java.util.List;

@Data
public class PatientDto {

    private String patientUuid;
    private String caseNo;
    private String caseNoMasked;

    private Integer age;
    private BigDecimal bmi;
    private BigDecimal amh;
    private Integer afc;
    private BigDecimal basalFsh;
    private BigDecimal basalLh;
    private BigDecimal basalE2;
    private BigDecimal basalP;
    private BigDecimal infertilityYears;
    private String protocolCode;
    private String infertilityTypeCode;

    private CycleDto latestCycle;

    @Data
    public static class CycleDto {
        private Long cyclePk;
        private Integer cycleNo;
        private String cycleStatus;
        private String reserveGrade;
        private String ohssRiskLevel;
        private List<VisitDto> visits;
    }
}
