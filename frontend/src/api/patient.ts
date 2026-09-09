import axios from ''axios''

const api = axios.create({
  baseURL: ''/api/v1'',
  timeout: 10000
})

export interface VisitDto {
  visitNo: number
  stimulationDay: number
  daysSinceLastVisit: number
  visitDate?: string
  e2Current: number
  lhCurrent: number
  pCurrent: number
  fshCurrent: number
  endometriumThickness: number
  follicleTotalCount: number
  follicleLeftCount?: number
  follicleRightCount?: number
  follicleMaxDiameter: number
  follicleAvgDiameter: number
  follicleSizeUnder10: number
  follicleSize10_12: number
  follicleSize13_15: number
  follicleSize16_18: number
  follicleSizeAbove18: number
  fshDose: number
  lhDose: number
  hmgDose: number
}

export interface PatientDto {
  patientUuid: string
  caseNo?: string
  caseNoMasked: string
  age: number
  bmi: number
  amh: number
  afc: number
  basalFsh: number
  basalLh: number
  basalE2: number
  basalP: number
  infertilityYears?: number
  protocolCode?: string
  infertilityTypeCode?: string
  latestCycle?: {
    cyclePk: number
    cycleNo: number
    cycleStatus: string
    reserveGrade?: string
    ohssRiskLevel?: string
    visits: VisitDto[]
  }
}

export const patientApi = {
  search(keyword: string, page = 1, size = 20) {
    return api.get<any, { data: { total: number; items: PatientDto[] } }>(''/patients/search'', {
      params: { keyword, page, size }
    })
  },

  detail(uuid: string) {
    return api.get<any, { data: PatientDto }>(`/patients/${uuid}`)
  },

  oneClickFill(caseNo: string) {
    return api.get<any, { data: PatientDto }>(''/patients/one-click-fill'', {
      params: { caseNo }
    })
  }
}

export default patientApi
