import { defineStore } from 'pinia'
import type { AnalysisRequest, AnalysisResult, AnalysisRunResponse } from '@/api/analysis'

const DRAFT_STORAGE_KEY = 'predicting-ovarian.analysis-draft.v1'

function loadDraft(): AnalysisRequest | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(DRAFT_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AnalysisRequest
    if (parsed?.patient && Array.isArray(parsed.records)) return parsed
    window.sessionStorage.removeItem(DRAFT_STORAGE_KEY)
  } catch {
    window.sessionStorage.removeItem(DRAFT_STORAGE_KEY)
  }
  return null
}

function persistDraft(request: AnalysisRequest | null) {
  if (typeof window === 'undefined') return
  try {
    if (request) {
      window.sessionStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(request))
    } else {
      window.sessionStorage.removeItem(DRAFT_STORAGE_KEY)
    }
  } catch {
    // Storage can be unavailable in restricted browser environments.
  }
}

/**
 * 一次分析运行由一个 runId 统一承载，三个结果页面共享同一份数据。
 * 页面切换只重新渲染，不重复调用模型。
 */
export const usePredictionStore = defineStore('prediction', {
  state: () => ({
    analysis: null as AnalysisResult | null,
    runId: '',
    request: null as AnalysisRequest | null,
    draft: loadDraft(),
    patient: {} as Record<string, any>,
    records: [] as Record<string, any>[],
    generated: false,
    generatedAt: ''
  }),

  getters: {
    result: (state) => state.analysis,
    summary: (state) => state.analysis?.summary ?? null,
    candidates: (state) => state.analysis?.candidates ?? [],
    curves: (state) => state.analysis?.curves ?? null,
    explanations: (state) => state.analysis?.explanations ?? null,
    generationRequest: (state) => state.draft ?? state.request,
    fshDose: (state) => state.analysis?.summary.fsh.actualDose ?? 0,
    lhDose: (state) => state.analysis?.summary.lh.actualDose ?? 0,
    hmgDose: (state) => state.analysis?.summary.hmg.actualDose ?? 0
  },

  actions: {
    setDraft(request: AnalysisRequest | null) {
      this.draft = request
      persistDraft(request)
    },

    setAnalysis(response: AnalysisRunResponse, request: AnalysisRequest) {
      if (response.status !== 'OK' || !response.result) {
        throw new Error(response.errorMessage || '模型未返回有效结果')
      }
      this.analysis = response.result
      this.runId = response.runId
      this.request = request
      this.patient = request.patient
      this.records = request.records
      this.generated = true
      this.generatedAt = new Date().toISOString()
    },

    clear() {
      this.analysis = null
      this.runId = ''
      this.request = null
      this.draft = null
      this.patient = {}
      this.records = []
      this.generated = false
      this.generatedAt = ''
      persistDraft(null)
    }
  }
})
