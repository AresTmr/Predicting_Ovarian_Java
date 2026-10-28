package com.hospital.ovarian.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.hospital.ovarian.dao.VisitMapper;
import com.hospital.ovarian.entity.Visit;
import com.hospital.ovarian.entity.dto.VisitDto;
import com.hospital.ovarian.exception.BusinessException;
import com.hospital.ovarian.service.VisitService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class VisitServiceImpl implements VisitService {

    private final VisitMapper visitMapper;

    @Override
    public VisitDto getVisit(Long visitPk) {
        Visit v = visitMapper.selectById(visitPk);
        if (v == null) throw BusinessException.notFound("复诊");
        return toDto(v);
    }

    @Override
    public VisitDto createVisit(Long cyclePk, VisitDto req) {
        Visit v = new Visit();
        v.setCyclePk(cyclePk);
        v.setVisitNo(req.getVisitNo() != null ? req.getVisitNo() : nextVisitNo(cyclePk));
        copyFields(req, v);
        visitMapper.insert(v);
        return toDto(v);
    }

    @Override
    public List<VisitDto> batchCreateVisits(Long cyclePk, List<VisitDto> req) {
        int i = visitMapper.selectCount(
                new LambdaQueryWrapper<Visit>().eq(Visit::getCyclePk, cyclePk)
        ).intValue() + 1;
        for (VisitDto dto : req) {
            Visit v = new Visit();
            v.setCyclePk(cyclePk);
            v.setVisitNo(i++);
            copyFields(dto, v);
            visitMapper.insert(v);
        }
        return visitMapper.selectList(
                new LambdaQueryWrapper<Visit>().eq(Visit::getCyclePk, cyclePk)
                        .orderByAsc(Visit::getVisitNo)
        ).stream().map(this::toDto).collect(Collectors.toList());
    }

    @Override
    public VisitDto updateVisit(Long visitPk, VisitDto req) {
        Visit exist = visitMapper.selectById(visitPk);
        if (exist == null) throw BusinessException.notFound("复诊");
        copyFields(req, exist);
        visitMapper.updateById(exist);
        return toDto(exist);
    }

    @Override
    public void deleteVisit(Long visitPk) {
        Visit v = visitMapper.selectById(visitPk);
        if (v == null) throw BusinessException.notFound("复诊");
        visitMapper.deleteById(visitPk);
    }

    private int nextVisitNo(Long cyclePk) {
        return visitMapper.selectCount(
                new LambdaQueryWrapper<Visit>().eq(Visit::getCyclePk, cyclePk)
        ).intValue() + 1;
    }

    private VisitDto toDto(Visit v) {
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

    private void copyFields(VisitDto src, Visit dst) {
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
