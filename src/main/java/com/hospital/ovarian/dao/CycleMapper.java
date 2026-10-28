package com.hospital.ovarian.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hospital.ovarian.entity.Cycle;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CycleMapper extends BaseMapper<Cycle> {
}
