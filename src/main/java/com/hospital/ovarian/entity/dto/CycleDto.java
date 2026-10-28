package com.hospital.ovarian.entity.dto;

import lombok.Data;
import java.time.LocalDate;
import java.util.List;

@Data
public class CycleDto {

    private Long cyclePk;
    private String patientUuid;
    private Integer cycleNo;
    private LocalDate cycleStartDate;
    private String cycleStatus;
    private LocalDate cycleEndDate;

    private String reserveGrade;
    private String reserveIndex;
    private String riskDecline;
    private Integer expectedOocytes;
    private String ohssRiskLevel;

    private List<VisitDto> visits;
}
