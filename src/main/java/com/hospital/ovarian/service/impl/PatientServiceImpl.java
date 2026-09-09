package com.hospital.ovarian.service.impl;

import com.hospital.ovarian.entity.Cycle;
import com.hospital.ovarian.entity.Patient;
import com.hospital.ovarian.entity.Visit;
import com.hospital.ovarian.entity.dto.PatientDto;
import com.hospital.ovarian.entity.dto.VisitDto;
import com.hospital.ovarian.exception.BusinessException;
import com.hospital.ovarian.service.PatientService;
import com.hospital.ovarian.utils.CaseNoHasher;
import com.hospital.ovarian.utils.PageResult;
import com.hospital.ovarian.utils.SensitiveMasker;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * 精简编译版本 - 使用内存 Map 模拟持久化
 * 真实部署需替换为 MyBatis-Plus + H2 实现
 */
@Slf4j
@Service
public class PatientServiceImpl implements PatientService {

    private final Map<Long, Patient> patientMap = new HashMap<>();
    private final Map<Long, Cycle> cycleMap = new HashMap<>();
    private final Map<Long, Visit> visitMap = new HashMap<>();
    private final AtomicLong patientPkSeq = new AtomicLong(1);
    private final AtomicLong cyclePkSeq = new AtomicLong(1);
    private final AtomicLong visitPkSeq = new AtomicLong(1);

    @PostConstruct
    public void initMockData() {
        // 注入 2 个示例患者（含 1 个多 visit 周期），用于一键填入验证
        Patient p1 = newPatient("P001", "15801", 39, "21.40", "1.82", 3,
                "6.19", "5.40", "48.00", "0.29", 14);
        Long p1Pk = savePatient(p1);

        Cycle c1 = newCycle(p1Pk, 1, LocalDate.of(2026, 6, 18));
        saveCycle(c1);

        Visit v1 = newVisit(c1.getCyclePk(), 1, 1, 0, LocalDate.of(2026, 6, 18),
                "11.00", "0.30", "0.29", "1.23", "3.20",
                9, 4, 5, "4.00", "3.61", 9, 0, 0, 0, 0,
                "150.00", "0.00", "0.00");
        saveVisit(v1);

        Visit v2 = newVisit(c1.getCyclePk(), 2, 7, 6, LocalDate.of(2026, 6, 24),
                "16.00", "0.20", "0.26", "13.73", "3.50",
                7, 4, 3, "6.00", "5.29", 7, 0, 0, 0, 0,
                "200.00", "0.00", "75.00");
        saveVisit(v2);

        Visit v3 = newVisit(c1.getCyclePk(), 3, 9, 2, LocalDate.of(2026, 6, 26),
                "68.00", "0.10", "0.28", "18.06", "4.90",
                8, 5, 3, "8.00", "6.06", 8, 0, 0, 0, 0,
                "250.00", "75.00", "75.00");
        saveVisit(v3);

        Visit v4 = newVisit(c1.getCyclePk(), 4, 12, 3, LocalDate.of(2026, 6, 29),
                "757.00", "0.80", "0.37", "22.39", "8.00",
                12, 6, 6, "13.00", "10.13", 4, 7, 1, 0, 0,
                "0", "0", "0");
        saveVisit(v4);

        log.info("Mock 数据初始化完成：1 个患者，1 个周期，4 条复诊");
    }

    @Override
    public PageResult<PatientDto> searchPatients(String keyword, int page, int size) {
        List<PatientDto> all = patientMap.values().stream()
                .filter(p -> keyword == null || keyword == null || keyword.isEmpty() || p.getCaseNo().contains(keyword))
                .sorted(Comparator.comparing(Patient::getCreatedAt).reversed())
                .map(this::toDto)
                .collect(Collectors.toList());

        int total = all.size();
        int from = Math.min((page - 1) * size, total);
        int to = Math.min(from + size, total);
        List<PatientDto> items = all.subList(from, to);

        return new PageResult<>(total, items);
    }

    @Override
    public PatientDto getPatientDetail(String patientUuid) {
        Patient p = patientMap.values().stream()
                .filter(x -> patientUuid.equals(x.getPatientUuid()))
                .findFirst()
                .orElseThrow(() -> BusinessException.notFound("患者"));

        PatientDto dto = toDto(p);

        Cycle latest = cycleMap.values().stream()
                .filter(c -> c.getPatientPk().equals(p.getPatientPk()))
                .max(Comparator.comparing(Cycle::getCycleNo))
                .orElse(null);

        if (latest != null) {
            PatientDto.CycleDto cycleDto = new PatientDto.CycleDto();
            cycleDto.setCyclePk(latest.getCyclePk());
            cycleDto.setCycleNo(latest.getCycleNo());
            cycleDto.setCycleStatus(latest.getCycleStatus());
            cycleDto.setReserveGrade(latest.getReserveGrade());
            cycleDto.setOhssRiskLevel(latest.getOhssRiskLevel());

            List<VisitDto> visits = visitMap.values().stream()
                    .filter(v -> v.getCyclePk().equals(latest.getCyclePk()))
                    .sorted(Comparator.comparing(Visit::getVisitNo))
                    .map(this::toVisitDto)
                    .collect(Collectors.toList());
            cycleDto.setVisits(visits);
            dto.setLatestCycle(cycleDto);
        }
        return dto;
    }

    @Override
    public PatientDto oneClickFill(String caseNo) {
        Patient p = patientMap.values().stream()
                .filter(x -> caseNo.equals(x.getCaseNo()))
                .findFirst()
                .orElse(null);
        if (p == null) {
            log.info("一键填入：病历号 {} 未命中", SensitiveMasker.maskCaseNo(caseNo));
            return null;
        }
        return getPatientDetail(p.getPatientUuid());
    }

    // ====== 私有方法 ======

    private Long savePatient(Patient p) {
        if (p.getPatientPk() == null) {
            p.setPatientPk(patientPkSeq.getAndIncrement());
            p.setPatientPk(p.getPatientPk());
        }
        if (p.getCreatedAt() == null) p.setCreatedAt(LocalDateTime.now());
        p.setUpdatedAt(LocalDateTime.now());
        p.setCaseNoHash(CaseNoHasher.sha256(p.getCaseNo()));
        patientMap.put(p.getPatientPk(), p);
        return p.getPatientPk();
    }

    private Long saveCycle(Cycle c) {
        if (c.getCyclePk() == null) c.setCyclePk(cyclePkSeq.getAndIncrement());
        if (c.getCreatedAt() == null) c.setCreatedAt(LocalDateTime.now());
        c.setUpdatedAt(LocalDateTime.now());
        cycleMap.put(c.getCyclePk(), c);
        return c.getCyclePk();
    }

    private Long saveVisit(Visit v) {
        if (v.getVisitPk() == null) v.setVisitPk(visitPkSeq.getAndIncrement());
        if (v.getCreatedAt() == null) v.setCreatedAt(LocalDateTime.now());
        v.setUpdatedAt(LocalDateTime.now());
        visitMap.put(v.getVisitPk(), v);
        return v.getVisitPk();
    }

    private Patient newPatient(String uuid, String caseNo, int age, String bmi, String amh, int afc,
                               String fsh, String lh, String e2, String pValue, int infertilityYears) {
        Patient p = new Patient();
        p.setPatientUuid(uuid);
        p.setCaseNo(caseNo);
        p.setAge(age);
        p.setBmi(new BigDecimal(bmi));
        p.setAmh(new BigDecimal(amh));
        p.setAfc(afc);
        p.setBasalFsh(new BigDecimal(fsh));
        p.setBasalLh(new BigDecimal(lh));
        p.setBasalE2(new BigDecimal(e2));
        p.setBasalP(new BigDecimal(pValue));
        p.setInfertilityYears(new BigDecimal(infertilityYears));
        p.setProtocolId(1);
        p.setInfertilityTypeId(1);
        p.setSourceType("MOCK");
        p.setIsArchived(false);
        return p;
    }

    private Cycle newCycle(Long patientPk, int cycleNo, LocalDate startDate) {
        Cycle c = new Cycle();
        c.setPatientPk(patientPk);
        c.setCycleNo(cycleNo);
        c.setCycleStartDate(startDate);
        c.setCycleStatus("ACTIVE");
        c.setReserveGrade("C");
        c.setOhssRiskLevel("LOW");
        return c;
    }

    private Visit newVisit(Long cyclePk, int visitNo, int stimDay, int interval, LocalDate date,
                           String e2, String lh, String p, String fsh, String endo,
                           int total, int left, int right, String max, String avg,
                           int u10, int u12, int u15, int u18, int uG18,
                           String fshD, String lhD, String hmgD) {
        Visit v = new Visit();
        v.setCyclePk(cyclePk);
        v.setVisitNo(visitNo);
        v.setStimulationDay(stimDay);
        v.setDaysSinceLastVisit(interval);
        v.setVisitDate(date);
        v.setE2(new BigDecimal(e2));
        v.setLh(new BigDecimal(lh));
        v.setP(new BigDecimal(p));
        v.setFsh(new BigDecimal(fsh));
        v.setEndometriumThickness(new BigDecimal(endo));
        v.setFollicleTotalCount(total);
        v.setFollicleLeftCount(left);
        v.setFollicleRightCount(right);
        v.setFollicleMaxDiameter(new BigDecimal(max));
        v.setFollicleAvgDiameter(new BigDecimal(avg));
        v.setFollicleSizeUnder10(u10);
        v.setFollicleSize10_12(u12);
        v.setFollicleSize13_15(u15);
        v.setFollicleSize16_18(u18);
        v.setFollicleSizeAbove18(uG18);
        v.setFshDose(new BigDecimal(fshD));
        v.setLhDose(new BigDecimal(lhD));
        v.setHmgDose(new BigDecimal(hmgD));
        return v;
    }

    private PatientDto toDto(Patient p) {
        PatientDto dto = new PatientDto();
        dto.setPatientUuid(p.getPatientUuid());
        dto.setCaseNo(p.getCaseNo());
        dto.setCaseNoMasked(SensitiveMasker.maskCaseNo(p.getCaseNo()));
        dto.setAge(p.getAge());
        dto.setBmi(p.getBmi());
        dto.setAmh(p.getAmh());
        dto.setAfc(p.getAfc());
        dto.setBasalFsh(p.getBasalFsh());
        dto.setBasalLh(p.getBasalLh());
        dto.setBasalE2(p.getBasalE2());
        dto.setBasalP(p.getBasalP());
        dto.setInfertilityYears(p.getInfertilityYears());
        return dto;
    }

    private VisitDto toVisitDto(Visit v) {
        VisitDto dto = new VisitDto();
        dto.setVisitNo(v.getVisitNo());
        dto.setStimulationDay(v.getStimulationDay());
        dto.setDaysSinceLastVisit(v.getDaysSinceLastVisit());
        dto.setVisitDate(v.getVisitDate());
        dto.setE2(v.getE2());
        dto.setLh(v.getLh());
        dto.setP(v.getP());
        dto.setFsh(v.getFsh());
        dto.setEndometriumThickness(v.getEndometriumThickness());
        dto.setFollicleTotalCount(v.getFollicleTotalCount());
        dto.setFollicleLeftCount(v.getFollicleLeftCount());
        dto.setFollicleRightCount(v.getFollicleRightCount());
        dto.setFollicleMaxDiameter(v.getFollicleMaxDiameter());
        dto.setFollicleAvgDiameter(v.getFollicleAvgDiameter());
        dto.setFollicleSizeUnder10(v.getFollicleSizeUnder10());
        dto.setFollicleSize10_12(v.getFollicleSize10_12());
        dto.setFollicleSize13_15(v.getFollicleSize13_15());
        dto.setFollicleSize16_18(v.getFollicleSize16_18());
        dto.setFollicleSizeAbove18(v.getFollicleSizeAbove18());
        dto.setFshDose(v.getFshDose());
        dto.setLhDose(v.getLhDose());
        dto.setHmgDose(v.getHmgDose());
        return dto;
    }
}


