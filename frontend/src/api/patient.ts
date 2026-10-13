import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

export interface VisitDto {
  visitNo: number
  stimulationDay: number
  daysSinceLastVisit: number
  visitDate?: string
  e2: number
  lh: number
  p: number
  fsh: number
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

export interface CycleDto {
  cyclePk?: number
  patientUuid?: string
  cycleNo?: number
  cycleStartDate?: string
  cycleStatus?: string
  reserveGrade?: string
  reserveIndex?: string
  riskDecline?: string
  expectedOocytes?: number
  ohssRiskLevel?: string
  visits?: VisitDto[]
}

export interface PredictionDto {
  visitPk?: number | null
  predictedFshDose: number
  predictedLhDose: number
  predictedHmgDose: number
  confidenceScore: number
  modelVersion: string
  inferenceTimeMs: number
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
    return api.get<any, { data: { total: number; items: PatientDto[] } }>('/patients/search', {
      params: { keyword, page, size }
    })
  },
  detail(uuid: string) {
    return api.get<any, { data: PatientDto }>(`/patients/${uuid}`)
  },
  oneClickFill(caseNo: string) {
    return api.get<any, { data: PatientDto }>('/patients/one-click-fill', {
      params: { caseNo }
    })
  }
}

export const cycleApi = {
  createWithVisits(patientUuid: string, cycle: CycleDto) {
    return api.post<any, { data: CycleDto }>(`/patients/${patientUuid}/cycles`, cycle)
  },
  detail(cyclePk: number) {
    return api.get<any, { data: CycleDto }>(`/cycles/${cyclePk}`)
  },
  listByPatient(patientUuid: string) {
    return api.get<any, { data: CycleDto[] }>(`/patients/${patientUuid}/cycles`)
  }
}

export const visitApi = {
  create(cyclePk: number, visit: VisitDto) {
    return api.post<any, { data: VisitDto }>(`/cycles/${cyclePk}/visits`, visit)
  },
  batchCreate(cyclePk: number, visits: VisitDto[]) {
    return api.post<any, { data: VisitDto[] }>(`/cycles/${cyclePk}/visits/batch`, visits)
  },
  update(visitPk: number, visit: VisitDto) {
    return api.put<any, { data: VisitDto }>(`/visits/${visitPk}`, visit)
  },
  delete(visitPk: number) {
    return api.delete<any, any>(`/visits/${visitPk}`)
  }
}

export const predictionApi = {
  predict(features: VisitDto) {
    return api.post<any, { data: PredictionDto }>('/predict', features)
  },
  predictByVisit(visitPk: number) {
    return api.post<any, { data: PredictionDto }>(`/predict/visit/${visitPk}`)
  }
}

export default api
