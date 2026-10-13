package com.hospital.ovarian.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("fact_patient")
public class Patient {

    @TableId(type = IdType.AUTO)
    private Long patientPk;

    private String patientUuid;
    private String caseNo;
    @TableField("case_no_hash")
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
