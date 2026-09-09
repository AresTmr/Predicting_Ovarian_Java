package com.hospital.ovarian.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class Cycle {

    private Long cyclePk;
    private Long patientPk;
    private Integer cycleNo;
    private LocalDate cycleStartDate;
    private String cycleStatus;
    private LocalDate cycleEndDate;
    private String reserveGrade;
    private BigDecimal reserveIndex;
    private String riskDecline;
    private Integer expectedOocytes;
    private String ohssRiskLevel;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
