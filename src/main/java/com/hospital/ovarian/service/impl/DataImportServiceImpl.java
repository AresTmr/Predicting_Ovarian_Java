package com.hospital.ovarian.service.impl;

import com.hospital.ovarian.dao.CycleMapper;
import com.hospital.ovarian.dao.PatientMapper;
import com.hospital.ovarian.dao.VisitMapper;
import com.hospital.ovarian.entity.Cycle;
import com.hospital.ovarian.entity.Patient;
import com.hospital.ovarian.entity.Visit;
import com.hospital.ovarian.service.DataImportService;
import com.hospital.ovarian.utils.CaseNoHasher;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.FileReader;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class DataImportServiceImpl implements DataImportService, CommandLineRunner {

    private final PatientMapper patientMapper;
    private final CycleMapper cycleMapper;
    private final VisitMapper visitMapper;

    @Override
    public Map<String, Object> importPatientsFromCsv(String filePath) {
        log.info("开始导入: {}", filePath);
        long t0 = System.currentTimeMillis();
        int success = 0, failed = 0, skipped = 0;

        try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
            String header = reader.readLine();
            if (header == null) throw new IllegalArgumentException("CSV 为空");
            String[] cols = header.split(",");
            Map<String, Integer> colIdx = new HashMap<>();
            for (int i = 0; i < cols.length; i++) colIdx.put(cols[i].trim(), i);

            String line;
            int lineNo = 1;
            while ((line = reader.readLine()) != null) {
                lineNo++;
                String[] values = line.split(",", -1);
                try {
                    String caseNo = get(values, colIdx, "case_no", "UNKNOWN");
                    Long existCount = patientMapper.selectCount(
                            new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<Patient>()
                                    .eq("case_no", caseNo)
                    );
                    if (existCount != null && existCount > 0) {
                        skipped++;
                        continue;
                    }
                    Patient p = new Patient();
                    p.setPatientUuid(get(values, colIdx, "patient_uuid", "P" + lineNo));
                    p.setCaseNo(caseNo);
                    p.setCaseNoHash(CaseNoHasher.sha256(caseNo));
                    p.setAge((int) Double.parseDouble(get(values, colIdx, "age", "30")));
                    p.setBmi(new BigDecimal(get(values, colIdx, "bmi", "22.0")));
                    p.setAmh(new BigDecimal(get(values, colIdx, "amh", "2.0")));
                    p.setAfc((int) Double.parseDouble(get(values, colIdx, "afc", "10")));
                    p.setBasalFsh(new BigDecimal(get(values, colIdx, "basal_fsh", "6.0")));
                    p.setBasalLh(new BigDecimal(get(values, colIdx, "basal_lh", "5.0")));
                    p.setBasalE2(new BigDecimal(get(values, colIdx, "basal_e2", "40.0")));
                    p.setBasalP(new BigDecimal(get(values, colIdx, "basal_p", "0.3")));
                    p.setInfertilityYears(new BigDecimal(get(values, colIdx, "infertility_years", "3.0")));
                    p.setSourceType("EXCEL_IMPORT");
                    p.setCreatedAt(LocalDateTime.now());
                    p.setUpdatedAt(LocalDateTime.now());
                    p.setIsArchived(false);
                    patientMapper.insert(p);
                    success++;
                } catch (Exception e) {
                    failed++;
                    log.warn("第 {} 行失败: {}", lineNo, e.getMessage());
                }
            }
        } catch (Exception e) {
            log.error("CSV 读取失败", e);
            throw new RuntimeException(e.getMessage(), e);
        }

        long cost = System.currentTimeMillis() - t0;
        Map<String, Object> result = new HashMap<>();
        result.put("totalRows", success + failed + skipped);
        result.put("success", success);
        result.put("failed", failed);
        result.put("skipped", skipped);
        result.put("costMs", cost);
        result.put("file", filePath);
        log.info("导入完成: 成功={} 失败={} 跳过={} 耗时={}ms", success, failed, skipped, cost);
        return result;
    }

    @Override
    public Map<String, Object> importDefault() {
        return importPatientsFromCsv("data/patient_import.csv");
    }

    private String get(String[] values, Map<String, Integer> colIdx, String key, String def) {
        Integer idx = colIdx.get(key);
        if (idx == null || idx >= values.length) return def;
        String v = values[idx].trim();
        return v.isEmpty() ? def : v;
    }

    @Override
    public void run(String... args) {
        initMockVisits();
    }

    /**
     * 为每个患者生成 1 个 cycle + 4 个 mock visit（如果还没有）
     */
    private void initMockVisits() {
        java.util.List<Patient> patients = patientMapper.selectList(null);
        int count = 0;
        for (Patient p : patients) {
            // 检查是否已有 cycle
            Long existing = cycleMapper.selectCount(
                new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<Cycle>()
                    .eq("patient_pk", p.getPatientPk())
            );
            if (existing != null && existing > 0) continue;

            // 创建 cycle
            Cycle cycle = new Cycle();
            cycle.setPatientPk(p.getPatientPk());
            cycle.setCycleNo(1);
            cycle.setCycleStartDate(java.time.LocalDate.now().minusDays(20));
            cycle.setCycleStatus("ACTIVE");
            cycle.setReserveGrade("C");
            cycle.setOhssRiskLevel("LOW");
            cycle.setCreatedAt(java.time.LocalDateTime.now());
            cycleMapper.insert(cycle);

            // 创建 4 个 visit
            int[] stimDays = {1, 7, 9, 12};
            double[] e2s = {11.0, 16.0, 68.0, 757.0};
            int[] totals = {9, 7, 8, 12};
            for (int i = 0; i < 4; i++) {
                Visit v = new Visit();
                v.setCyclePk(cycle.getCyclePk());
                v.setVisitNo(i + 1);
                v.setStimulationDay(stimDays[i]);
                v.setDaysSinceLastVisit(i == 0 ? 0 : stimDays[i] - stimDays[i-1]);
                v.setVisitDate(cycle.getCycleStartDate().plusDays(stimDays[i] - 1));
                v.setE2(java.math.BigDecimal.valueOf(e2s[i]));
                v.setLh(java.math.BigDecimal.valueOf(0.3 - i * 0.1));
                v.setP(java.math.BigDecimal.valueOf(0.29));
                v.setFsh(java.math.BigDecimal.valueOf(1.23 + i * 10));
                v.setEndometriumThickness(java.math.BigDecimal.valueOf(3.2 + i * 1.6));
                v.setFollicleTotalCount(totals[i]);
                v.setFollicleLeftCount(4);
                v.setFollicleRightCount(totals[i] - 4);
                v.setFollicleMaxDiameter(java.math.BigDecimal.valueOf(4.0 + i * 3));
                v.setFollicleAvgDiameter(java.math.BigDecimal.valueOf(3.61 + i * 2.17));
                v.setFollicleSizeUnder10(totals[i]);
                v.setFollicleSize10_12(0);
                v.setFollicleSize13_15(0);
                v.setFollicleSize16_18(0);
                v.setFollicleSizeAbove18(0);
                v.setFshDose(java.math.BigDecimal.valueOf(150 + i * 50));
                v.setLhDose(java.math.BigDecimal.valueOf(i >= 2 ? 75 : 0));
                v.setHmgDose(java.math.BigDecimal.valueOf(i == 0 ? 0 : 75));
                v.setCreatedAt(java.time.LocalDateTime.now());
                visitMapper.insert(v);
            }
            count++;
        }
        if (count > 0) log.info("已为 {} 个患者生成 mock visit 数据", count);
    }
}