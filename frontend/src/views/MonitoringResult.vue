<template>
  <div class="page-wrapper">
    <div class="container">
      <h2 class="page-title">动态监测与结果面板</h2>
      <p class="page-desc">展示下一次记录性 Gn 剂量预测、预测获卵数、中重度 OHSS 风险和候选联合方案排序。</p>

      <section class="card empty-card" v-if="!analysis">
        <div class="alert-warn">
          尚未生成监测结果。请先在患者录入页填写当前患者信息，或使用下方按钮直接计算。
        </div>
        <el-button type="primary" size="large" class="generate-btn" :loading="loading" @click="generate">
          生成最新监测结果
        </el-button>
      </section>

      <section v-if="analysis && summary">
        <section class="summary-cards">
          <div class="summary-card">
            <div class="summary-label">
              <span>模型推荐 FSH</span>
              <el-tag type="success" size="small">获卵数 / OHSS 平衡</el-tag>
            </div>
            <div class="summary-value">
              <span class="value">{{ summary.fsh.category }}</span>
            </div>
            <div class="summary-sub">实际推荐 {{ summary.fsh.actualDose }} IU/天</div>
          </div>
          <div class="summary-card">
            <div class="summary-label"><span>模型推荐 LH</span></div>
            <div class="summary-value">
              <span class="value">{{ summary.lh.actualDose }}</span>
              <span class="unit">IU/天</span>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-label"><span>模型推荐 HMG</span></div>
            <div class="summary-value">
              <span class="value">{{ summary.hmg.actualDose }}</span>
              <span class="unit">IU/天</span>
            </div>
          </div>
          <div class="summary-card oocyte-card">
            <div class="summary-label"><span>预测获卵数</span></div>
            <div class="summary-value">
              <span class="value">{{ formatNumber(summary.oocytes) }}</span>
              <span class="unit">个</span>
            </div>
          </div>
          <div class="summary-card ohss-card">
            <div class="summary-label"><span>中重度 OHSS 风险</span></div>
            <div class="summary-value">
              <span class="value" :class="ohssClass">{{ summary.ohssRiskPercent.toFixed(2) }}%</span>
            </div>
            <div class="ohss-tag">
              <el-tag :type="ohssTagType" effect="dark">{{ summary.ohssRiskLevel }}</el-tag>
            </div>
          </div>
        </section>

        <section class="model-strip">
          <span>分析运行 ID：{{ store.runId }}</span>
          <span>模型状态：OK</span>
        </section>

        <section class="monitoring-table-card">
          <div class="monitoring-table-header" @click="tableCollapsed = !tableCollapsed">
            <span class="caret" :class="{ collapsed: tableCollapsed }">▼</span>
            <span>横向动态监测窗</span>
          </div>

          <table v-show="!tableCollapsed" class="monitoring-table">
            <thead>
              <tr>
                <th>日期</th>
                <th v-for="record in historyRecords" :key="record.visit_uid || record.visit">
                  第 {{ record.stim_day }} 天 / 第 {{ record.visit }} 次监测
                </th>
                <th class="today">第 {{ todayRecord?.stim_day ?? '—' }} 天（今日）</th>
                <th class="highlight">下一次记录性预测</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="row-label blue">FSH</td>
                <td v-for="record in historyRecords" :key="`fsh-${record.visit_uid || record.visit}`">
                  {{ doseCategory('fsh', record.current_fsh) }}
                </td>
                <td class="today">—</td>
                <td class="highlight">{{ summary.fsh.category }} <span class="badge">预测</span></td>
              </tr>
              <tr>
                <td class="row-label blue">LH</td>
                <td v-for="record in historyRecords" :key="`lh-${record.visit_uid || record.visit}`">
                  {{ doseCategory('lh', record.current_lh) }}
                </td>
                <td class="today">—</td>
                <td class="highlight">{{ summary.lh.actualDose }} <span class="badge">预测</span></td>
              </tr>
              <tr>
                <td class="row-label blue">HMG</td>
                <td v-for="record in historyRecords" :key="`hmg-${record.visit_uid || record.visit}`">
                  {{ doseCategory('hmg', record.current_hmg) }}
                </td>
                <td class="today">—</td>
                <td class="highlight">{{ summary.hmg.actualDose }} <span class="badge">预测</span></td>
              </tr>
              <tr>
                <td class="row-label red">激素 E2</td>
                <td v-for="record in historyRecords" :key="`e2-${record.visit_uid || record.visit}`">{{ fmt(record.e2) }}</td>
                <td class="today">{{ fmt(todayRecord?.e2) }}</td>
                <td>—</td>
              </tr>
              <tr>
                <td class="row-label red">激素 LH</td>
                <td v-for="record in historyRecords" :key="`lh-h-${record.visit_uid || record.visit}`">{{ fmt(record.lh_value) }}</td>
                <td class="today">{{ fmt(todayRecord?.lh_value) }}</td>
                <td>—</td>
              </tr>
              <tr>
                <td class="row-label red">激素 P</td>
                <td v-for="record in historyRecords" :key="`p-${record.visit_uid || record.visit}`">{{ fmt(record.p) }}</td>
                <td class="today">{{ fmt(todayRecord?.p) }}</td>
                <td>—</td>
              </tr>
              <tr>
                <td class="row-label red">获卵数</td>
                <td v-for="record in historyRecords" :key="`o-${record.visit_uid || record.visit}`">—</td>
                <td class="today">—</td>
                <td class="highlight">{{ formatNumber(summary.oocytes) }} <span class="badge">预测</span></td>
              </tr>
              <tr>
                <td class="row-label red">中重度 OHSS 风险</td>
                <td v-for="record in historyRecords" :key="`r-${record.visit_uid || record.visit}`">—</td>
                <td class="today">—</td>
                <td class="highlight">
                  {{ summary.ohssRiskPercent.toFixed(2) }}% · {{ summary.ohssRiskLevel }}
                  <span class="badge">预测</span>
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <div class="bottom-alert">
          AI 仅提供风险分层、候选方案比较和辅助解释；建议结合临床判断、E2、卵泡负荷和患者个体情况综合评估。
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { analysisApi } from '@/api/analysis'
import { usePredictionStore } from '@/stores/prediction'

const store = usePredictionStore()
const analysis = computed(() => store.analysis)
const summary = computed(() => store.summary)
const loading = ref(false)
const tableCollapsed = ref(false)
const historyRecords = computed(() => store.records.slice(0, -1))
const todayRecord = computed(() => store.records.length ? store.records[store.records.length - 1] : null)
const ohssTagType = computed((): 'success' | 'warning' | 'danger' => {
  const level = summary.value?.ohssRiskLevel ?? ''
  if (level.includes('高')) return 'danger'
  if (level.includes('中')) return 'warning'
  return 'success'
})
const ohssClass = computed(() => summary.value?.ohssRiskLevel?.includes('高') ? 'red' : 'green')

function fmt(value: unknown): string {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return Math.abs(number - Math.round(number)) < 1e-9 ? String(Math.round(number)) : number.toFixed(2)
}

function formatNumber(value: unknown): string {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return Number.isInteger(number) ? String(number) : number.toFixed(2)
}

function doseCategory(drug: 'fsh' | 'lh' | 'hmg', value: unknown): string {
  const dose = Number(value)
  if (!Number.isFinite(dose)) return '—'
  if (drug === 'fsh') {
    if (dose < 80) return '0-80'
    if (dose <= 160) return '80-160'
    return '>160'
  }
  if (drug === 'lh') {
    if (dose <= 0) return '0'
    if (dose < 150) return '75'
    return '≥150'
  }
  if (dose <= 0) return '0'
  if (dose < 150) return '75'
  if (dose < 225) return '150'
  return '≥225'
}

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
    ElMessage.success('监测结果已重新生成')
  } catch (e: any) {
    ElMessage.error('生成失败：' + (e?.response?.data?.message || e?.message || '模型服务不可用'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page-wrapper { padding: 24px 0; }
.container { max-width: 1240px; margin: 0 auto; padding: 0 32px; }
.page-title { font-size: 28px; font-weight: 600; color: #1f2d3d; margin: 0 0 8px; }
.page-desc { font-size: 13px; color: #909399; margin: 0 0 24px; }
.card { background: #fff; border-radius: 8px; padding: 32px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.alert-warn { background: #fdf6ec; color: #e6a23c; padding: 14px 18px; border-radius: 4px; margin-bottom: 24px; font-size: 14px; }
.generate-btn { width: 100%; height: 48px; font-size: 15px; }
.summary-cards { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
.summary-card { background: #fff; border-radius: 8px; padding: 20px; border: 1px solid #ebeef5; border-top: 3px solid #409eff; min-height: 112px; }
.summary-card:nth-child(4) { border-top-color: #67c23a; }
.summary-card:nth-child(5) { border-top-color: #e6a23c; }
.summary-label { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #909399; margin-bottom: 12px; }
.summary-value { display: flex; align-items: baseline; gap: 8px; }
.summary-value .value { font-size: 30px; font-weight: 700; color: #1f2d3d; }
.summary-value .value.green { color: #67c23a; }
.summary-value .value.red { color: #f56c6c; }
.summary-value .unit { font-size: 13px; color: #909399; }
.summary-sub { color: #909399; font-size: 11px; margin-top: 6px; }
.ohss-tag { margin-top: 8px; }
.model-strip { display: flex; justify-content: space-between; gap: 16px; background: #ecf5ff; color: #409eff; padding: 10px 16px; border-radius: 6px; font-size: 12px; margin-bottom: 12px; }
.monitoring-table-card { background: #fff; border-radius: 8px; padding: 0; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); border-top: 2px solid #409eff; overflow: hidden; }
.monitoring-table-header { display: flex; align-items: center; gap: 8px; padding: 16px 20px; font-size: 15px; font-weight: 600; color: #409eff; cursor: pointer; user-select: none; background: #fafbfc; }
.monitoring-table-header .caret { display: inline-block; transition: transform 0.2s; font-size: 12px; }
.monitoring-table-header .caret.collapsed { transform: rotate(-90deg); }
.monitoring-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.monitoring-table th, .monitoring-table td { padding: 14px 12px; text-align: center; border-bottom: 1px solid #f0f0f0; }
.monitoring-table th { background: #fafbfc; color: #1f2d3d; font-weight: 600; }
.monitoring-table th.highlight { background: #ecf5ff; color: #409eff; }
.monitoring-table td.today { background: #f8fafc; }
.monitoring-table .row-label { font-weight: 600; text-align: left; padding-left: 20px; }
.monitoring-table .row-label.blue { color: #409eff; }
.monitoring-table .row-label.red { color: #f56c6c; }
.monitoring-table td.highlight { background: #ecf5ff; color: #409eff; font-weight: 600; }
.monitoring-table .badge { display: inline-block; background: #409eff; color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 3px; margin-left: 4px; vertical-align: middle; }
.bottom-alert { background: #ecf5ff; color: #409eff; padding: 12px 18px; border-radius: 4px; font-size: 13px; margin-top: 16px; }
@media (max-width: 980px) {
  .summary-cards { grid-template-columns: repeat(2, 1fr); }
  .monitoring-table { min-width: 980px; }
  .monitoring-table-card { overflow-x: auto; }
}
</style>
