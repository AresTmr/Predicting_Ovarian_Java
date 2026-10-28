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
@TableName("fact_visit")
public class Visit {

    @TableId(type = IdType.AUTO)
    private Long visitPk;

    @TableField("cycle_pk")
    private Long cyclePk;
    @TableField("visit_no")
    private Integer visitNo;
    @TableField("stimulation_day")
    private Integer stimulationDay;
    @TableField("days_since_last_visit")
    private Integer daysSinceLastVisit;
    @TableField("visit_date")
    private LocalDate visitDate;

    private BigDecimal e2;
    private BigDecimal lh;
    private BigDecimal p;
    private BigDecimal fsh;

    @TableField("endometrium_thickness")
    private BigDecimal endometriumThickness;

    @TableField("follicle_total_count")
    private Integer follicleTotalCount;
    @TableField("follicle_left_count")
    private Integer follicleLeftCount;
    @TableField("follicle_right_count")
    private Integer follicleRightCount;
    @TableField("follicle_max_diameter")
    private BigDecimal follicleMaxDiameter;
    @TableField("follicle_avg_diameter")
    private BigDecimal follicleAvgDiameter;
    @TableField("follicle_size_under_10")
    private Integer follicleSizeUnder10;
    @TableField("follicle_size_10_12")
    private Integer follicleSize10_12;
    @TableField("follicle_size_13_15")
    private Integer follicleSize13_15;
    @TableField("follicle_size_16_18")
    private Integer follicleSize16_18;
    @TableField("follicle_size_above_18")
    private Integer follicleSizeAbove18;

    @TableField("fsh_dose")
    private BigDecimal fshDose;
    @TableField("lh_dose")
    private BigDecimal lhDose;
    @TableField("hmg_dose")
    private BigDecimal hmgDose;

    private String note;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
