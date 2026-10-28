package com.hospital.ovarian.controller;

import com.hospital.ovarian.service.DataImportService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/import")
@RequiredArgsConstructor
public class DataImportController {

    private final DataImportService dataImportService;

    /** 导入默认路径 data/patient_import.csv */
    @PostMapping("/default")
    public Map<String, Object> importDefault() {
        return dataImportService.importDefault();
    }

    /** 导入指定路径的 CSV */
    @PostMapping("/csv")
    public Map<String, Object> importFromCsv(@RequestParam String filePath) {
        return dataImportService.importPatientsFromCsv(filePath);
    }
}
