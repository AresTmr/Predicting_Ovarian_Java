package com.hospital.ovarian.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 患者实体（精简版 - 无 ORM 注解）
 */
@Data
public class Patient {

    private Long patientPk;
    private String patientUuid;
    private String caseNo;
    private String caseNoHash;

    private Integer age;
    private BigDecimal bmi;
    private BigDecimal amh;
    private Integer afc;
    private BigDecimal basalFsh;
    private BigDecimal basalLh;
    private BigDecimal basalE2;
    private BigDecimal basalP;
    private BigDecimal infertilityYears;
    private Integer protocolId;
    private Integer infertilityTypeId;

    private String sourceType;
    private Long createdBy;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private Boolean isArchived;
}
