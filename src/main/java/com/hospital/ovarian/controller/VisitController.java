package com.hospital.ovarian.controller;

import com.hospital.ovarian.entity.dto.VisitDto;
import com.hospital.ovarian.service.VisitService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class VisitController {

    private final VisitService visitService;

    /** 单条新增 */
    @PostMapping("/cycles/{cyclePk}/visits")
    public VisitDto create(@PathVariable Long cyclePk, @RequestBody VisitDto req) {
        return visitService.createVisit(cyclePk, req);
    }

    /** 批量新增（前端"保存患者记录"按钮） */
    @PostMapping("/cycles/{cyclePk}/visits/batch")
    public List<VisitDto> batchCreate(@PathVariable Long cyclePk, @RequestBody List<VisitDto> req) {
        return visitService.batchCreateVisits(cyclePk, req);
    }

    /** 获取详情 */
    @GetMapping("/visits/{visitPk}")
    public VisitDto get(@PathVariable Long visitPk) {
        return visitService.getVisit(visitPk);
    }

    /** 更新 */
    @PutMapping("/visits/{visitPk}")
    public VisitDto update(@PathVariable Long visitPk, @RequestBody VisitDto req) {
        return visitService.updateVisit(visitPk, req);
    }

    /** 删除 */
    @DeleteMapping("/visits/{visitPk}")
    public void delete(@PathVariable Long visitPk) {
        visitService.deleteVisit(visitPk);
    }
}
