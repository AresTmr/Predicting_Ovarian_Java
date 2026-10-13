package com.hospital.ovarian.service;

import java.util.Map;

public interface DataImportService {

    /**
     * 从 CSV 导入患者基线数据
     * @param filePath CSV 绝对路径
     * @return 导入结果统计
     */
    Map<String, Object> importPatientsFromCsv(String filePath);

    /**
     * 导入文件自动定位（默认 data/patient_import.csv）
     */
    Map<String, Object> importDefault();
}
