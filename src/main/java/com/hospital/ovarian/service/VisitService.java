package com.hospital.ovarian.service;

import com.hospital.ovarian.entity.dto.VisitDto;

import java.util.List;

public interface VisitService {

    /** 获取 visit 详情 */
    VisitDto getVisit(Long visitPk);

    /** 单条新增 visit */
    VisitDto createVisit(Long cyclePk, VisitDto req);

    /** 批量新增 visit（用于前端一键保存） */
    List<VisitDto> batchCreateVisits(Long cyclePk, List<VisitDto> req);

    /** 更新 visit */
    VisitDto updateVisit(Long visitPk, VisitDto req);

    /** 删除 visit */
    void deleteVisit(Long visitPk);
}
