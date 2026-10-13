package com.hospital.ovarian.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.hospital.ovarian.dao.CycleMapper;
import com.hospital.ovarian.dao.VisitMapper;
import com.hospital.ovarian.entity.Cycle;
import com.hospital.ovarian.entity.Visit;
import com.hospital.ovarian.entity.dto.CycleDto;
import com.hospital.ovarian.entity.dto.VisitDto;
import com.hospital.ovarian.exception.BusinessException;
import com.hospital.ovarian.service.CycleService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class CycleServiceImpl implements CycleService {

    private final CycleMapper cycleMapper;
    private final VisitMapper visitMapper;

    @Override
    public CycleDto createCycle(String patientUuid, CycleDto req) {
        Cycle cycle = new Cycle();
        cycle.setCycleNo(req.getCycleNo() != null ? req.getCycleNo() : nextCycleNo(0L));
        cycle.setCycleStartDate(req.getCycleStartDate() != null ? req.getCycleStartDate() : java.time.LocalDate.now());
        cycle.setCycleStatus("ACTIVE");
        cycle.setReserveGrade(req.getReserveGrade());
        cycle.setOhssRiskLevel(req.getOhssRiskLevel());
        cycle.setCreatedAt(LocalDateTime.now());
        cycleMapper.insert(cycle);
        log.info("创建周期 cycle_pk={}", cycle.getCyclePk());
        return toDto(cycle, null);
    }

    @Override
    public CycleDto getCycleDetail(Long cyclePk) {
        Cycle cycle = cycleMapper.selectById(cyclePk);
        if (cycle == null) throw BusinessException.notFound("周期");
        List<Visit> visits = visitMapper.selectList(
                new LambdaQueryWrapper<Visit>().eq(Visit::getCyclePk, cyclePk)
                        .orderByAsc(Visit::getVisitNo)
        );
        return toDto(cycle, visits);
    }

    @Override
    public List<CycleDto> listCyclesByPatient(String patientUuid) {
        // 简化：根据 patientPk 过滤
        return cycleMapper.selectList(null).stream()
                .filter(c -> c.getPatientPk() != null)
                .map(c -> toDto(c, null))
                .collect(Collectors.toList());
    }

    @Override
    public CycleDto saveCycleWithVisits(String patientUuid, CycleDto req) {
        Cycle cycle = new Cycle();
        cycle.setPatientPk(0L);  // 简化：MVP 暂不强制 FK 校验
        cycle.setCycleNo(req.getCycleNo() != null ? req.getCycleNo() : 1);
        cycle.setCycleStartDate(req.getCycleStartDate());
        cycle.setCycleStatus("ACTIVE");
        cycle.setReserveGrade(req.getReserveGrade());
        cycle.setOhssRiskLevel(req.getOhssRiskLevel());
        cycle.setCreatedAt(LocalDateTime.now());
        cycleMapper.insert(cycle);

        if (req.getVisits() != null) {
            int i = 1;
            for (VisitDto vd : req.getVisits()) {
                Visit v = new Visit();
                v.setCyclePk(cycle.getCyclePk());
                v.setVisitNo(i++);
                copyVisitFields(vd, v);
                visitMapper.insert(v);
            }
        }
        log.info("创建周期+visit cycle_pk={} visits={}", cycle.getCyclePk(),
                req.getVisits() == null ? 0 : req.getVisits().size());
        return getCycleDetail(cycle.getCyclePk());
    }

    private int nextCycleNo(Long patientPk) {
        Long count = cycleMapper.selectCount(null);
        return count == null ? 1 : count.intValue() + 1;
    }

    private CycleDto toDto(Cycle c, List<Visit> visits) {
        CycleDto dto = new CycleDto();
        dto.setCyclePk(c.getCyclePk());
        dto.setCycleNo(c.getCycleNo());
        dto.setCycleStartDate(c.getCycleStartDate());
        dto.setCycleStatus(c.getCycleStatus());
        dto.setCycleEndDate(c.getCycleEndDate());
        dto.setReserveGrade(c.getReserveGrade());
        dto.setReserveIndex(c.getReserveIndex() != null ? c.getReserveIndex().toString() : null);
        dto.setRiskDecline(c.getRiskDecline());
        dto.setExpectedOocytes(c.getExpectedOocytes());
        dto.setOhssRiskLevel(c.getOhssRiskLevel());
        if (visits != null) {
            dto.setVisits(visits.stream().map(this::toVisitDto).sorted(Comparator.comparing(VisitDto::getVisitNo)).collect(Collectors.toList()));
        }
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

    private void copyVisitFields(VisitDto src, Visit dst) {
        dst.setStimulationDay(src.getStimulationDay());
        dst.setDaysSinceLastVisit(src.getDaysSinceLastVisit());
        dst.setVisitDate(src.getVisitDate());
        dst.setE2(src.getE2());
        dst.setLh(src.getLh());
        dst.setP(src.getP());
        dst.setFsh(src.getFsh());
        dst.setEndometriumThickness(src.getEndometriumThickness());
        dst.setFollicleTotalCount(src.getFollicleTotalCount());
        dst.setFollicleLeftCount(src.getFollicleLeftCount());
        dst.setFollicleRightCount(src.getFollicleRightCount());
        dst.setFollicleMaxDiameter(src.getFollicleMaxDiameter());
        dst.setFollicleAvgDiameter(src.getFollicleAvgDiameter());
        dst.setFollicleSizeUnder10(src.getFollicleSizeUnder10());
        dst.setFollicleSize10_12(src.getFollicleSize10_12());
        dst.setFollicleSize13_15(src.getFollicleSize13_15());
        dst.setFollicleSize16_18(src.getFollicleSize16_18());
        dst.setFollicleSizeAbove18(src.getFollicleSizeAbove18());
        dst.setFshDose(src.getFshDose());
        dst.setLhDose(src.getLhDose());
        dst.setHmgDose(src.getHmgDose());
    }
}
