package com.hospital.ovarian.service;

import com.hospital.ovarian.entity.Cycle;
import com.hospital.ovarian.entity.dto.CycleDto;
import com.hospital.ovarian.entity.dto.VisitDto;

import java.util.List;

public interface CycleService {

    /** 创建新周期 */
    CycleDto createCycle(String patientUuid, CycleDto req);

    /** 获取周期详情（含所有 visit） */
    CycleDto getCycleDetail(Long cyclePk);

    /** 列出患者所有周期 */
    List<CycleDto> listCyclesByPatient(String patientUuid);

    /** 批量保存 visit（连同创建周期场景） */
    CycleDto saveCycleWithVisits(String patientUuid, CycleDto req);
}
