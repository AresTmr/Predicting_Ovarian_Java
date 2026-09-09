package com.hospital.ovarian.controller;

import com.hospital.ovarian.entity.dto.PatientDto;
import com.hospital.ovarian.service.PatientService;
import com.hospital.ovarian.utils.PageResult;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/patients")
@RequiredArgsConstructor
public class PatientController {

    private final PatientService patientService;

    @GetMapping("/search")
    public Map<String, Object> search(
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        PageResult<PatientDto> result = patientService.searchPatients(keyword, page, size);
        Map<String, Object> resp = new HashMap<>();
        resp.put("total", result.getTotal());
        resp.put("items", result.getItems());
        resp.put("page", page);
        resp.put("size", size);
        return resp;
    }

    @GetMapping("/{patientUuid}")
    public PatientDto detail(@PathVariable String patientUuid) {
        return patientService.getPatientDetail(patientUuid);
    }

    @GetMapping("/one-click-fill")
    public PatientDto oneClickFill(@RequestParam String caseNo) {
        return patientService.oneClickFill(caseNo);
    }

    @GetMapping("/_health")
    public Map<String, Object> health() {
        Map<String, Object> h2 = new HashMap<>();
        h2.put("status", "UP");
        h2.put("version", "2.2.0");
        h2.put("build", "compile-test");
        return h2;
    }
}
