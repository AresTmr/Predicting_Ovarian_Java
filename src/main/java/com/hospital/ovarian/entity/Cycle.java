package com.hospital.ovarian.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("fact_cycle")
public class Cycle {

    @TableId(type = IdType.AUTO)
    private Long cyclePk;

    @TableField("patient_pk")
    private Long patientPk;
    private Integer cycleNo;
    @TableField("cycle_start_date")
    private LocalDate cycleStartDate;
    @TableField("cycle_status")
    private String cycleStatus;
    @TableField("cycle_end_date")
    private LocalDate cycleEndDate;
    @TableField("reserve_grade")
    private String reserveGrade;
    @TableField("reserve_index")
    private BigDecimal reserveIndex;
    @TableField("risk_decline")
    private String riskDecline;
    @TableField("expected_oocytes")
    private Integer expectedOocytes;
    @TableField("ohss_risk_level")
    private String ohssRiskLevel;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
