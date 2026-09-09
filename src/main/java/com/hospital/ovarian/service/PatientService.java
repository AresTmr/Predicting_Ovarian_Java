package com.hospital.ovarian.service;

import com.hospital.ovarian.entity.dto.PatientDto;
import com.hospital.ovarian.utils.PageResult;

public interface PatientService {

    PageResult<PatientDto> searchPatients(String keyword, int page, int size);

    PatientDto getPatientDetail(String patientUuid);

    PatientDto oneClickFill(String caseNo);
}
