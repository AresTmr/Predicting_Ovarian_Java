package com.hospital.ovarian.controller;

import com.hospital.ovarian.entity.dto.CycleDto;
import com.hospital.ovarian.service.CycleService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class CycleController {

    private final CycleService cycleService;

    /** 创建周期 */
    @PostMapping("/patients/{patientUuid}/cycles")
    public CycleDto createCycle(@PathVariable String patientUuid, @RequestBody CycleDto req) {
        return cycleService.saveCycleWithVisits(patientUuid, req);
    }

    /** 周期详情 */
    @GetMapping("/cycles/{cyclePk}")
    public CycleDto getCycle(@PathVariable Long cyclePk) {
        return cycleService.getCycleDetail(cyclePk);
    }

    /** 患者的所有周期 */
    @GetMapping("/patients/{patientUuid}/cycles")
    public List<CycleDto> listCycles(@PathVariable String patientUuid) {
        return cycleService.listCyclesByPatient(patientUuid);
    }
}
