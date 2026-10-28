<template>
  <div class="page-wrapper">
    <div class="container">
      <h2 class="page-title">下一次 Gn 剂量与结局风险解释</h2>
      <p class="page-desc">解释当前患者快照下 FSH、LH、HMG 推荐类别、预测获卵数及严格中重度 OHSS 风险的真实模型归因。</p>

      <section class="card empty-card" v-if="!result">
        <div class="alert-warn">
          尚未生成推荐解释。请在患者录入页填写当前患者信息后，直接使用下方按钮计算。
        </div>
        <el-button type="primary" size="large" class="generate-btn" :loading="loading" @click="generate">
          生成最新监测结果
        </el-button>
      </section>

      <section v-if="result">
        <div class="run-strip">分析运行 ID：{{ store.runId }} · 模型状态：OK</div>

        <section class="explain-card">
          <div class="explain-header">
            <span class="explain-heading">
              <span class="explain-icon">±</span>
              <span class="explain-title">个体化贡献</span>
            </span>
          </div>

          <section v-for="group in cardGroups" :key="group.key" class="explanation-group">
            <div class="section-title">{{ group.title }}</div>
            <div class="explain-grid" :class="group.columns === 2 ? 'explain-grid-2' : 'explain-grid-3'">
              <article
                v-for="card in group.cards"
                :key="card.title"
                class="bd-card"
                :class="{ 'outcome-card': group.key === 'outcome' }"
              >
                <div class="bd-head">
                  <div>
                    <div class="bd-title">{{ card.title }}</div>
                    <div class="bd-target">预测目标：{{ card.target }}</div>
                  </div>
                  <div class="bd-prob-flow">
                    <div class="bd-base">
                      <span>基准预测值</span>
                      <strong>{{ card.baseline }}</strong>
                    </div>
                    <span class="bd-arrow">→</span>
                    <span class="bd-final">{{ card.final }}</span>
                  </div>
                </div>

                <div class="bd-stack">
                  <div v-for="item in card.items" :key="`${card.title}-${item.label}`" class="bd-row">
                    <div>
                      <div class="bd-lab">{{ item.label }}</div>
                      <div class="bd-val">{{ item.value }}</div>
                    </div>
                    <div class="bd-track">
                      <div class="bd-fill" :class="item.tone" :style="{ width: `${item.width}%` }"></div>
                    </div>
                    <div class="bd-meta">
                      <span class="bd-chip" :class="item.tone">{{ item.chip }}</span>
                      <span class="bd-score">{{ item.score }}</span>
                    </div>
                  </div>

                  <div class="bd-row other">
                    <div>
                      <div class="bd-lab">其他因素总和</div>
                      <div class="bd-val">其余 {{ card.otherCount }} 个录入变量的贡献合计</div>
                    </div>
                    <div class="bd-track">
                      <div class="bd-fill" :class="card.other.tone" :style="{ width: `${card.other.width}%` }"></div>
                    </div>
                    <div class="bd-meta">
                      <span class="bd-chip" :class="card.other.tone">{{ card.other.chip }}</span>
                      <span class="bd-score">{{ card.other.score }}</span>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </section>

        <section class="explain-card knn-card">
          <div class="explain-header">
            <span class="explain-title">KNN 相似历史病例支持</span>
            <span class="explain-subtitle">推荐解释与历史校验</span>
          </div>
          <div class="knn-grid-3">
            <div v-for="group in knnGroups" :key="group.drug" class="knn-col">
              <div class="knn-title">{{ group.drug }} 相似病例</div>
              <div class="knn-table-wrap">
                <table class="knn-table">
                  <thead>
                    <tr>
                      <th>病例</th>
                      <th>剂量</th>
                      <th>病例数</th>
                      <th>选择率</th>
                      <th>成功率</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in group.rows" :key="`${group.drug}-${row.case}`">
                      <td class="case-id">{{ row.case }}</td>
                      <td>{{ row.dose }}</td>
                      <td>{{ row.cases }}</td>
                      <td>{{ row.selectionRate }}</td>
                      <td>{{ row.successRate }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="knn-note">
            各药物按选择率与成功率等权综合排序；仅用于解释和历史证据校验，不参与推荐剂量选择。
          </div>
        </section>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { analysisApi, type ExplanationBlock, type ExplanationItem } from '@/api/analysis'
import { usePredictionStore } from '@/stores/prediction'

type Tone = 'safe' | 'risk'
type DrugKey = 'fsh' | 'lh' | 'hmg'
type OutcomeKey = 'oocytes' | 'ohss'

interface ContributionItem {
  label: string
  value: string
  width: number
  chip: string
  score: string
  tone: Tone
}

interface ExplanationCard {
  title: string
  target: string
  baseline: string
  final: string
  items: ContributionItem[]
  other: ContributionItem
  otherCount: number
}

interface ExplanationGroup {
  key: string
  title: string
  columns: 2 | 3
  cards: ExplanationCard[]
}

const store = usePredictionStore()
const result = computed(() => store.analysis)
const loading = ref(false)

const featureLabels: Record<string, string> = {
  age: '年龄',
  bmi: 'BMI',
  amh: 'AMH',
  afc: 'AFC',
  basal_fsh: '基础 FSH',
  basal_lh: '基础 LH',
  basal_e2: '基础 E2',
  basal_p: '基础 P',
  infertility_duration: '不孕年限',
  Day: '促排天数',
  gn_day: '促排天数',
  days_since_previous_visit: '距上次监测天数',
  current_e2: '血清 E2',
  current_lh: '血清 LH',
  current_p: '血清 P',
  current_fsh: '血清 FSH',
  current_endometrium: '内膜厚度',
  previous_fsh_daily_dose: '既往 FSH 剂量',
  previous_lh_daily_dose: '既往 LH 剂量',
  previous_hmg_daily_dose: '既往 HMG 剂量',
  total_follicle_count: '总卵泡数',
  left_follicle_count: '左侧卵泡数',
  right_follicle_count: '右侧卵泡数',
  max_follicle_diameter: '最大卵泡直径',
  mean_follicle_diameter: '平均卵泡直径',
  mature_follicle_count: '≥14 mm 卵泡数',
  follicle_count_lt_10: '<10 mm 卵泡数',
  follicle_count_10_12: '10–12 mm 卵泡数',
  follicle_count_13_15: '13–15 mm 卵泡数',
  follicle_count_16_18: '16–18 mm 卵泡数',
  follicle_count_gt_18: '≥18 mm 卵泡数',
  growing_follicle_count: '生长卵泡数'
}

const latestRecord = computed(() => store.records.length ? store.records[store.records.length - 1] : {})
const previousRecord = computed(() => store.records.length > 1 ? store.records[store.records.length - 2] : {})

function featureValue(feature: string): unknown {
  const patient = store.patient
  const latest = latestRecord.value
  const previous = previousRecord.value
  const direct: Record<string, string> = {
    age: 'age',
    bmi: 'bmi',
    amh: 'amh',
    afc: 'afc',
    basal_fsh: 'basal_fsh',
    basal_lh: 'basal_lh',
    basal_e2: 'basal_e2',
    basal_p: 'basal_p',
    infertility_duration: 'years',
    Day: 'stim_day',
    gn_day: 'stim_day',
    days_since_previous_visit: 'days_since_previous_visit',
    current_e2: 'e2',
    current_lh: 'lh_value',
    current_p: 'p',
    current_fsh: 'serum_fsh',
    current_endometrium: 'current_endometrium',
    total_follicle_count: 'total_follicles',
    left_follicle_count: 'left_follicles',
    right_follicle_count: 'right_follicles',
    max_follicle_diameter: 'max_f',
    mean_follicle_diameter: 'mean_f',
    mature_follicle_count: 'mature_follicle_count',
    follicle_count_lt_10: 'f_lt10',
    follicle_count_10_12: 'f_10_12',
    follicle_count_13_15: 'f_13_15',
    follicle_count_16_18: 'f_16_18',
    follicle_count_gt_18: 'f_gt18'
  }
  if (feature === 'previous_fsh_daily_dose') return previous.current_fsh
  if (feature === 'previous_lh_daily_dose') return previous.current_lh
  if (feature === 'previous_hmg_daily_dose') return previous.current_hmg
  const source = direct[feature]
  if (!source) return undefined
  return source in latest ? latest[source] : patient[source]
}

function formatFeatureValue(feature: string): string {
  const value = Number(featureValue(feature))
  if (!Number.isFinite(value)) return '--'
  if (['previous_fsh_daily_dose', 'previous_lh_daily_dose', 'previous_hmg_daily_dose'].includes(feature)) {
    return `${formatNum(value)} IU/天`
  }
  if (['current_e2', 'basal_e2'].includes(feature)) return `${formatNum(value)} pg/mL`
  if (['current_lh', 'current_fsh', 'basal_lh', 'basal_fsh'].includes(feature)) return `${formatNum(value, 2)} IU/L`
  if (['current_p', 'basal_p'].includes(feature)) return `${formatNum(value, 2)} ng/mL`
  if (['current_endometrium', 'max_follicle_diameter', 'mean_follicle_diameter'].includes(feature)) {
    return `${formatNum(value, 1)} mm`
  }
  if (feature === 'age') return `${formatNum(value)} 岁`
  if (['Day', 'gn_day'].includes(feature)) return `${formatNum(value)} 天`
  if (feature === 'amh') return `${formatNum(value, 2)} ng/mL`
  if (feature === 'bmi') return `${formatNum(value, 1)} kg/m²`
  return formatNum(value)
}

function formatNum(value: number, digits = 1): string {
  return Math.abs(value - Math.round(value)) < 1e-9 ? String(Math.round(value)) : value.toFixed(digits)
}

function contributionItems(
  block: ExplanationBlock | undefined,
  mode: 'dose' | 'oocytes' | 'ohss',
): { items: ContributionItem[]; other: ContributionItem; count: number } {
  const grouped = new Map<string, ExplanationItem>()
  for (const item of block?.items ?? []) {
    const value = Number(item.mean_shap)
    if (!Number.isFinite(value) || Math.abs(value) <= 1e-12) continue
    const label = featureLabels[item.feature] ?? item.feature
    const existing = grouped.get(label)
    if (existing) {
      existing.mean_shap += value
      existing.mean_abs_shap = (existing.mean_abs_shap ?? 0) + Math.abs(value)
    } else {
      grouped.set(label, { ...item, mean_shap: value })
    }
  }
  const source = [...grouped.values()]
    .sort((a, b) => Math.abs(Number(b.mean_shap)) - Math.abs(Number(a.mean_shap)))
  const selected = source.slice(0, 6)
  const remainder = source.slice(6)
  const otherValue = remainder.reduce((sum, item) => sum + Number(item.mean_shap), 0)
  const maxAbs = Math.max(
    ...selected.map(item => Math.abs(Number(item.mean_shap))),
    Math.abs(otherValue),
    1e-12,
  )
  const makeItem = (item: ExplanationItem, value: number): ContributionItem => {
    const positive = value >= 0
    let chip = '局部正向'
    let tone: Tone = positive ? 'safe' : 'risk'
    let score = `${positive ? '+' : ''}${(value * 100).toFixed(3)} pp`
    if (mode === 'oocytes') {
      chip = positive ? '增加预测' : '降低预测'
      score = `${positive ? '+' : ''}${value.toFixed(3)} 个`
    } else if (mode === 'ohss') {
      chip = positive ? '增加风险' : '降低风险'
      tone = positive ? 'risk' : 'safe'
      score = `${positive ? '+' : ''}${(value * 100).toFixed(3)} pp`
    }
    return {
      label: featureLabels[item.feature] ?? item.feature,
      value: formatFeatureValue(item.feature),
      width: Math.max(18, Math.min(96, Math.round(28 + 64 * (Math.abs(value) / maxAbs)))),
      chip,
      score,
      tone,
    }
  }
  const items = selected.map(item => makeItem(item, Number(item.mean_shap)))
  const otherPositive = otherValue >= 0
  const other: ContributionItem = {
    label: '其他因素总和',
    value: '',
    width: Math.max(18, Math.min(96, Math.round(28 + 64 * (Math.abs(otherValue) / maxAbs)))),
    chip: mode === 'ohss'
      ? (otherPositive ? '增加风险' : '降低风险')
      : mode === 'oocytes'
        ? (otherPositive ? '增加预测' : '降低预测')
        : (otherPositive ? '局部正向' : '局部负向'),
    score: mode === 'oocytes'
      ? `${otherPositive ? '+' : ''}${otherValue.toFixed(3)} 个`
      : `${otherPositive ? '+' : ''}${(otherValue * 100).toFixed(3)} pp`,
    tone: mode === 'ohss' ? (otherPositive ? 'risk' : 'safe') : (otherPositive ? 'safe' : 'risk'),
  }
  return { items, other, count: remainder.length }
}

function doseCard(key: DrugKey): ExplanationCard {
  const block = result.value?.explanations.dose[key]
  const summary = result.value!.summary[key]
  const built = contributionItems(block, 'dose')
  return {
    title: `${key.toUpperCase()} 个体化贡献`,
    target: `${key.toUpperCase()} = ${summary.category}`,
    baseline: `${(Number(block?.baselineProbability ?? 0) * 100).toFixed(1)}%`,
    final: `${(Number(block?.currentProbability ?? summary.probability) * 100).toFixed(1)}%`,
    items: built.items,
    other: built.other,
    otherCount: built.count,
  }
}

function outcomeCard(key: OutcomeKey): ExplanationCard {
  const current = result.value!
  const block = current.explanations[key]
  const mode = key === 'oocytes' ? 'oocytes' : 'ohss'
  const built = contributionItems(block, mode)
  if (key === 'oocytes') {
    const prediction = Number(block.prediction ?? current.summary.oocytes)
    const baseline = Number(block.baselinePrediction ?? prediction)
    return {
      title: '获卵数个体化贡献',
      target: `预测获卵数 = ${prediction.toFixed(1)}`,
      baseline: `${baseline.toFixed(1)} 个`,
      final: `${prediction.toFixed(1)} 个`,
      items: built.items,
      other: built.other,
      otherCount: built.count,
    }
  }
  const prediction = Number(block.prediction ?? current.summary.ohssRisk)
  const baseline = Number(block.baselinePrediction ?? prediction)
  return {
    title: 'OHSS 个体化贡献',
    target: `中重度 OHSS 风险 / ${current.summary.ohssRiskLevel}`,
    baseline: `${(baseline * 100).toFixed(2)}%`,
    final: `${(prediction * 100).toFixed(2)}%`,
    items: built.items,
    other: built.other,
    otherCount: built.count,
  }
}

const cardGroups = computed<ExplanationGroup[]>(() => {
  if (!result.value) return []
  return [
    {
      key: 'dose',
      title: 'Gn 剂量个体化解释',
      columns: 3,
      cards: [doseCard('fsh'), doseCard('lh'), doseCard('hmg')],
    },
    {
      key: 'outcome',
      title: '结局与风险个体化解释',
      columns: 2,
      cards: [outcomeCard('oocytes'), outcomeCard('ohss')],
    },
  ]
})

const knnGroups = computed(() => {
  const items = result.value?.explanations.knn.items ?? {}
  return (['fsh', 'lh', 'hmg'] as const).map(drug => ({
    drug: drug.toUpperCase(),
    rows: (items[drug] ?? []).map(row => ({
      case: row.case.replace('Case', '病例'),
      dose: row.dose,
      cases: row.case_count,
      selectionRate: row.selection_rate,
      successRate: row.success_rate,
    })),
  }))
})

async function generate() {
  const request = store.generationRequest
  if (!request) {
    ElMessage.warning('请先在患者录入页填写患者基础信息和监测记录')
    return
  }
  loading.value = true
  try {
    const response = await analysisApi.create(request)
    store.setAnalysis(response.data, request)
    ElMessage.success('推荐解释已重新生成')
  } catch (e: any) {
    ElMessage.error('生成失败：' + (e?.response?.data?.message || e?.message || '模型服务不可用'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page-wrapper { padding: 24px 0; }
.container { max-width: 1280px; margin: 0 auto; padding: 0 32px; }
.page-title { font-size: 28px; font-weight: 600; margin: 0 0 8px; color: #1f2d3d; }
.page-desc { font-size: 13px; color: #909399; margin: 0 0 24px; }
.card { background: #fff; border-radius: 8px; padding: 32px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.alert-warn { background: #fdf6ec; color: #e6a23c; padding: 14px 18px; border-radius: 4px; margin-bottom: 24px; }
.generate-btn { width: 100%; height: 48px; }
.run-strip { background: #ecf5ff; color: #409eff; padding: 10px 16px; border-radius: 6px; font-size: 12px; margin-bottom: 16px; }
.explain-card { background: #fff; border-radius: 12px; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(15,23,42,0.04); border: 1px solid #e5e9f2; overflow: hidden; }
.explain-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #f7f9ff; border-bottom: 1px solid #e5e9f2; }
.explain-heading { display: inline-flex; align-items: center; gap: 10px; }
.explain-icon { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 8px; background: #eef0ff; color: #3525cd; font-size: 17px; font-weight: 800; }
.explain-title { font-size: 16px; font-weight: 700; color: #1f2d3d; }
.explain-subtitle { font-size: 12px; color: #909399; }
.explanation-group { padding: 0 18px; }
.explanation-group:last-child { padding-bottom: 18px; }
.section-title { margin: 20px 0 12px; padding-left: 10px; border-left: 3px solid #6f5df6; font-size: 14px; font-weight: 700; color: #334155; }
.explain-grid { display: grid; gap: 16px; }
.explain-grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.explain-grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.bd-card { display: flex; flex-direction: column; min-width: 0; padding: 17px; border: 1px solid #d8deeb; border-radius: 14px; background: #fff; box-shadow: 0 3px 10px rgba(15,23,42,0.035); }
.bd-card.outcome-card { border-color: #cfe8e5; background: #fcfefe; }
.bd-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; min-height: 54px; margin-bottom: 16px; padding-bottom: 13px; border-bottom: 1px solid #edf1f7; }
.bd-title { font-size: 15px; font-weight: 700; line-height: 1.35; color: #0b1c30; }
.bd-target { margin-top: 4px; font-size: 12px; line-height: 1.4; color: #64748b; }
.bd-prob-flow { display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex: 0 0 auto; }
.bd-base { display: flex; align-items: baseline; gap: 6px; font-size: 11px; font-weight: 600; color: #64748b; white-space: nowrap; }
.bd-base strong { font-size: 13px; font-weight: 700; color: #334155; }
.bd-arrow { color: #6366f1; font-size: 18px; font-weight: 800; line-height: 1; }
.bd-final { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 999px; border: 1px solid #d7d7ff; background: #eef0ff; color: #3525cd; font-size: 12px; font-weight: 700; white-space: nowrap; }
.bd-stack { display: flex; flex: 1; flex-direction: column; gap: 13px; }
.bd-row { display: grid; grid-template-columns: minmax(112px, 142px) minmax(0, 1fr); column-gap: 13px; row-gap: 5px; align-items: center; padding: 4px 0; border-radius: 6px; }
.bd-lab { font-size: 13px; font-weight: 700; line-height: 1.35; color: #0b1c30; }
.bd-val { margin-top: 2px; font-size: 12px; color: #64748b; }
.bd-track { height: 10px; overflow: hidden; border-radius: 999px; background: #e9eef6; box-shadow: inset 0 1px 2px rgba(15,23,42,0.06); }
.bd-fill { height: 100%; min-width: 4px; border-radius: 999px; background: linear-gradient(90deg, #20c9b4, #0ba895); }
.bd-fill.risk { background: linear-gradient(90deg, #f47b8b, #e84861); }
.bd-meta { grid-column: 2; display: flex; align-items: center; gap: 7px; margin-top: -2px; }
.bd-chip { display: inline-flex; padding: 3px 8px; border: 1px solid #a9eee4; border-radius: 999px; background: #dcfbf6; color: #04786e; font-size: 11px; font-weight: 650; white-space: nowrap; }
.bd-chip.risk { border-color: #fecdd3; background: #fff1f2; color: #b91c1c; }
.bd-score { color: #475569; font-size: 12px; font-weight: 650; white-space: nowrap; }
.bd-row.other { margin-top: 2px; padding-top: 13px; border-top: 1px solid #dfe6ef; }
.bd-row.other .bd-lab { color: #334155; }
.bd-row.other .bd-val { font-size: 11px; }
.knn-grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; padding: 16px 20px 0; }
.knn-col { min-width: 0; overflow: hidden; border: 1px solid #d8deeb; border-radius: 12px; background: #fff; }
.knn-title { padding: 14px 15px; border-bottom: 1px solid #e5eaf2; color: #0b1c30; font-size: 15px; font-weight: 700; }
.knn-table-wrap { overflow-x: auto; }
.knn-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.knn-table th { padding: 10px 7px; border: 0; background: #eef3ff; color: #475569; font-size: 11px; font-weight: 700; text-align: center; }
.knn-table td { padding: 11px 7px; border-top: 1px solid #edf1f7; color: #475569; font-size: 12px; font-weight: 600; text-align: center; white-space: nowrap; }
.knn-table td.case-id { color: #3525cd; font-weight: 700; }
.knn-note { padding: 12px 20px 18px; color: #64748b; font-size: 12px; line-height: 1.55; }
@media (max-width: 1100px) { .explain-grid-3, .knn-grid-3 { grid-template-columns: 1fr; } }
@media (max-width: 760px) { .container { padding: 0 16px; } .explain-grid-2 { grid-template-columns: 1fr; } .bd-head { flex-direction: column; } }
</style>
