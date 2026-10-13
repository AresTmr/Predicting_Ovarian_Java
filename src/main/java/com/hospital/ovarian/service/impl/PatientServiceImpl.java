package com.hospital.ovarian.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hospital.ovarian.dao.CycleMapper;
import com.hospital.ovarian.dao.PatientMapper;
import com.hospital.ovarian.dao.VisitMapper;
import com.hospital.ovarian.entity.Cycle;
import com.hospital.ovarian.entity.Patient;
import com.hospital.ovarian.entity.Visit;
import com.hospital.ovarian.entity.dto.PatientDto;
import com.hospital.ovarian.entity.dto.VisitDto;
import com.hospital.ovarian.exception.BusinessException;
import com.hospital.ovarian.service.PatientService;
import com.hospital.ovarian.utils.PageResult;
import com.hospital.ovarian.utils.SensitiveMasker;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 患者服务（MyBatis-Plus + H2 实现）
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PatientServiceImpl implements PatientService {

    private final PatientMapper patientMapper;
    private final CycleMapper cycleMapper;
    private final VisitMapper visitMapper;

    @Override
    public PageResult<PatientDto> searchPatients(String keyword, int page, int size) {
        Page<Patient> pageReq = new Page<>(page, size);
        LambdaQueryWrapper<Patient> wrapper = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.eq(Patient::getCaseNo, keyword);
        }
        wrapper.orderByDesc(Patient::getCreatedAt);

        Page<Patient> result = patientMapper.selectPage(pageReq, wrapper);
        List<PatientDto> items = result.getRecords().stream().map(this::toDto).collect(Collectors.toList());
        return new PageResult<>(result.getTotal(), items);
    }

    @Override
    public PatientDto getPatientDetail(String patientUuid) {
        Patient p = patientMapper.selectOne(
                new LambdaQueryWrapper<Patient>().eq(Patient::getPatientUuid, patientUuid)
        );
        if (p == null) throw BusinessException.notFound("患者");
        PatientDto dto = toDto(p);
        // 查最新 cycle + visit
        Cycle latest = cycleMapper.selectOne(
                new LambdaQueryWrapper<Cycle>().eq(Cycle::getPatientPk, p.getPatientPk())
                        .orderByDesc(Cycle::getCycleNo).last("LIMIT 1")
        );
        if (latest != null) {
            PatientDto.CycleDto cycleDto = new PatientDto.CycleDto();
            cycleDto.setCyclePk(latest.getCyclePk());
            cycleDto.setCycleNo(latest.getCycleNo());
            cycleDto.setCycleStatus(latest.getCycleStatus());
            cycleDto.setReserveGrade(latest.getReserveGrade());
            cycleDto.setOhssRiskLevel(latest.getOhssRiskLevel());
            java.util.List<Visit> visits = visitMapper.selectList(
                    new LambdaQueryWrapper<Visit>().eq(Visit::getCyclePk, latest.getCyclePk())
                            .orderByAsc(Visit::getVisitNo)
            );
            java.util.List<VisitDto> visitDtos = new java.util.ArrayList<>();
            for (Visit v : visits) {
                VisitDto vd = new VisitDto();
                vd.setVisitNo(v.getVisitNo());
                vd.setStimulationDay(v.getStimulationDay());
                vd.setDaysSinceLastVisit(v.getDaysSinceLastVisit());
                vd.setVisitDate(v.getVisitDate());
                vd.setE2(v.getE2());
                vd.setLh(v.getLh());
                vd.setP(v.getP());
                vd.setFsh(v.getFsh());
                vd.setEndometriumThickness(v.getEndometriumThickness());
                vd.setFollicleTotalCount(v.getFollicleTotalCount());
                vd.setFollicleLeftCount(v.getFollicleLeftCount());
                vd.setFollicleRightCount(v.getFollicleRightCount());
                vd.setFollicleMaxDiameter(v.getFollicleMaxDiameter());
                vd.setFollicleAvgDiameter(v.getFollicleAvgDiameter());
                vd.setFollicleSizeUnder10(v.getFollicleSizeUnder10());
                vd.setFollicleSize10_12(v.getFollicleSize10_12());
                vd.setFollicleSize13_15(v.getFollicleSize13_15());
                vd.setFollicleSize16_18(v.getFollicleSize16_18());
                vd.setFollicleSizeAbove18(v.getFollicleSizeAbove18());
                vd.setFshDose(v.getFshDose());
                vd.setLhDose(v.getLhDose());
                vd.setHmgDose(v.getHmgDose());
                visitDtos.add(vd);
            }
            cycleDto.setVisits(visitDtos);
            dto.setLatestCycle(cycleDto);
        }
        return dto;
    }

    @Override
    public PatientDto oneClickFill(String caseNo) {
        Patient p = patientMapper.selectOne(
                new LambdaQueryWrapper<Patient>().eq(Patient::getCaseNo, caseNo)
        );
        if (p == null) {
            log.info("一键填入：病历号 {} 未命中", SensitiveMasker.maskCaseNo(caseNo));
            return null;
        }
        return getPatientDetail(p.getPatientUuid());
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
}
