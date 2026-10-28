import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000
})

export interface AnalysisRequest {
  patient: Record<string, any>
  records: Record<string, any>[]
}

export interface DoseResult {
  label: string
  display: string
  dose: number
  probability: number
  probabilities?: Record<string, number>
  actualDose: number
  category: string
}

export interface AnalysisSummary {
  fsh: DoseResult
  lh: DoseResult
  hmg: DoseResult
  oocytes: number
  mii: number
  ohssRisk: number
  ohssRiskPercent: number
  ohssRiskLevel: string
}

export interface CandidateResult {
  name: string
  rank: number
  fsh: number
  lh: number
  hmg: number
  fshCategory?: string
  oocytes: number
  ohssRisk: number
  candidateRole?: string
  candidate_role?: string
  balance_rank?: number
}

export interface CurvePoint {
  dose: number
  oocytes: number
  ohssRisk: number
  recommended: boolean
}

export interface ExplanationItem {
  feature: string
  mean_shap: number
  mean_abs_shap?: number
  value_label?: string
  feature_value?: number
}

export interface ExplanationBlock {
  baselinePrediction?: number
  prediction?: number
  currentProbability?: number
  baselineProbability?: number
  items: ExplanationItem[]
}

export interface AnalysisResult {
  status: string
  source: string
  model: Record<string, string>
  summary: AnalysisSummary
  candidates: CandidateResult[]
  curves: Record<'fsh' | 'lh' | 'hmg', CurvePoint[]>
  explanations: {
    dose: Record<'fsh' | 'lh' | 'hmg', ExplanationBlock>
    oocytes: ExplanationBlock
    ohss: ExplanationBlock
    knn: {
      status: string
      items: Record<string, Array<{
        case: string
        dose: string
        case_count: number
        selection_rate: string
        success_rate: string
      }>>
    }
  }
  warnings: string[]
}

export interface AnalysisRunResponse {
  runId: string
  status: string
  result: AnalysisResult
  errorMessage?: string | null
}

export const analysisApi = {
  create(request: AnalysisRequest) {
    return api.post<any, { data: AnalysisRunResponse }>('/recommendation-runs', request)
  },
  get(runId: string) {
    return api.get<any, { data: AnalysisRunResponse }>(`/recommendation-runs/${runId}`)
  },
  health() {
    return api.get<any, { data: Record<string, any> }>('/recommendation-runs/runtime/health')
  }
}

export default api
