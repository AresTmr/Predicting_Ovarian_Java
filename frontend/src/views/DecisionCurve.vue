<template>
  <div class="page-wrapper">
    <div class="container">
      <h2 class="page-title">决策曲线</h2>
      <p class="page-desc">比较候选剂量下的预测获卵数与中重度 OHSS 风险。</p>

      <section class="card empty-card" v-if="!analysis">
        <div class="alert-warn">
          尚未生成决策曲线。请在患者录入页填写当前患者信息后，直接使用下方按钮计算。
        </div>
        <el-button type="primary" size="large" class="generate-btn" :loading="loading" @click="generate">
          生成最新监测结果
        </el-button>
      </section>

      <section v-if="analysis && summary">
        <div class="top-alert">
          固定其他患者变量，仅改变单种 Gn 剂量进行条件情景分析；虚线和实心点标出模型推荐剂量及其预测结果。
        </div>

        <section class="charts-section">
          <div v-for="chart in charts" :key="chart.key" class="chart-card">
            <div class="chart-header">
              <div class="chart-title">
                <span class="chart-name">{{ chart.name }}</span>
                <span class="model-rec">模型推荐 <span class="rec-value">{{ chart.recValue }}</span></span>
              </div>
              <div class="chart-meta">
                <span>获卵数 <span class="meta-value">{{ chart.oocytes }}</span></span>
                <span>OHSS 率 <span class="meta-value">{{ chart.ohssRate }}</span></span>
              </div>
            </div>
            <div :ref="(el: any) => (chartRefs[chart.key] = el)" class="chart-canvas"></div>
          </div>
        </section>

        <section class="scenarios-card">
          <div class="scenarios-header">
            <span>候选剂量情景分析</span>
            <span class="model-tag">获卵数 / OHSS 平衡排序</span>
          </div>
          <table class="scenarios-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>候选情景</th>
                <th>FSH 范围</th>
                <th>LH</th>
                <th>HMG</th>
                <th>预测获卵数</th>
                <th>中重度 OHSS 风险</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in scenarios" :key="s.rank" :class="{ best: s.rank === 1 }">
                <td><span class="rank-circle">{{ s.rank }}</span></td>
                <td>{{ s.name }}<span v-if="s.rank === 1" class="recommended-chip">模型推荐剂量</span></td>
                <td>{{ s.fsh }}</td>
                <td>{{ s.lh }}</td>
                <td>{{ s.hmg }}</td>
                <td>{{ s.oocytes }}</td>
                <td>{{ s.ohss }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { analysisApi, type CandidateResult, type CurvePoint } from '@/api/analysis'
import { usePredictionStore } from '@/stores/prediction'

type DrugKey = 'fsh' | 'lh' | 'hmg'

const store = usePredictionStore()
const analysis = computed(() => store.analysis)
const summary = computed(() => store.summary)
const loading = ref(false)
const chartRefs = ref<Record<string, any>>({})
let chartInstances: Record<string, echarts.ECharts> = {}

const charts = computed(() => {
  const current = summary.value
  if (!current) return []
  return [
    { key: 'fsh' as DrugKey, name: 'FSH', recValue: current.fsh.category, oocytes: formatNumber(current.oocytes), ohssRate: `${current.ohssRiskPercent.toFixed(2)}%` },
    { key: 'lh' as DrugKey, name: 'LH', recValue: String(current.lh.actualDose), oocytes: formatNumber(current.oocytes), ohssRate: `${current.ohssRiskPercent.toFixed(2)}%` },
    { key: 'hmg' as DrugKey, name: 'HMG', recValue: String(current.hmg.actualDose), oocytes: formatNumber(current.oocytes), ohssRate: `${current.ohssRiskPercent.toFixed(2)}%` }
  ]
})

const scenarios = computed(() => {
  const rows = [...store.candidates].sort((a, b) => (a.rank ?? a.balance_rank ?? 99) - (b.rank ?? b.balance_rank ?? 99))
  return rows.map((candidate: CandidateResult, index: number) => ({
    rank: candidate.rank ?? index + 1,
    name: candidate.name || `情景 ${String.fromCharCode(65 + index)}`,
    fsh: candidate.fshCategory || formatDose(candidate.fsh),
    lh: formatNumber(candidate.lh),
    hmg: formatNumber(candidate.hmg),
    oocytes: formatNumber(candidate.oocytes),
    ohss: `${(Number(candidate.ohssRisk) * 100).toFixed(2)}%`
  }))
})

function formatNumber(value: unknown): string {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return Math.abs(number - Math.round(number)) < 1e-9 ? String(Math.round(number)) : number.toFixed(2)
}

function formatDose(value: number): string {
  return formatNumber(value)
}

function makeChartOption(key: DrugKey) {
  const points: CurvePoint[] = store.curves?.[key] ?? []
  const doses = points.map(point => String(point.dose))
  const oocytes = points.map(point => point.oocytes)
  const ohss = points.map(point => Number((point.ohssRisk * 100).toFixed(3)))
  const recommended = points.find(point => point.recommended)
  const recCategory = recommended ? String(recommended.dose) : doses[0]
  const recOocytes = recommended?.oocytes ?? (oocytes.length ? oocytes[0] : 0)

  return {
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['获卵数', '中重度 OHSS 风险'],
      top: 0,
      left: 'center',
      itemGap: 18,
      textStyle: { fontSize: 11 }
    },
    grid: { left: 70, right: 70, bottom: 44, top: 52 },
    xAxis: {
      type: 'category',
      data: doses,
      boundaryGap: false,
      name: `${key.toUpperCase()} 剂量（IU/天）`,
      nameLocation: 'middle',
      nameGap: 26,
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisTick: { show: false },
      axisLabel: { color: '#909399', fontSize: 11 }
    },
    yAxis: [
      {
        type: 'value',
        position: 'left',
        scale: true,
        min: (value: any) => value.min - Math.max(0.02, (value.max - value.min) * 0.12),
        max: (value: any) => value.max + Math.max(0.02, (value.max - value.min) * 0.12),
        axisLabel: { color: '#909399', fontSize: 11, formatter: (value: number) => value.toFixed(2) },
        name: '预测获卵数（个）',
        nameLocation: 'middle',
        nameRotate: 90,
        nameGap: 48,
        nameTextStyle: { color: '#909399', fontSize: 11, align: 'center', verticalAlign: 'middle' },
        splitLine: { lineStyle: { color: '#f0f0f0' } }
      },
      {
        type: 'value',
        position: 'right',
        scale: true,
        axisLabel: { color: '#909399', fontSize: 11, formatter: (value: number) => `${value.toFixed(2)}%` },
        name: '中重度 OHSS 风险（%）',
        nameLocation: 'middle',
        nameRotate: -90,
        nameGap: 48,
        nameTextStyle: { color: '#909399', fontSize: 11, align: 'center', verticalAlign: 'middle' },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '获卵数',
        type: 'line',
        data: oocytes,
        symbol: 'circle',
        symbolSize: 7,
        itemStyle: { color: '#0fbf9f' },
        lineStyle: { color: '#0fbf9f', width: 3 },
        markPoint: {
          symbol: 'circle',
          symbolSize: 11,
          itemStyle: { color: '#0fbf9f' },
          data: recCategory ? [{ coord: [recCategory, recOocytes] }] : []
        },
        markLine: {
          symbol: 'none',
          lineStyle: { color: '#7c6cf6', type: 'dashed', width: 2 },
          data: recCategory ? [{ xAxis: recCategory }] : []
        }
      },
      {
        name: '中重度 OHSS 风险',
        type: 'line',
        yAxisIndex: 1,
        data: ohss,
        symbol: 'circle',
        symbolSize: 7,
        itemStyle: { color: '#ff9f2e' },
        lineStyle: { color: '#ff9f2e', width: 3, type: 'dashed' }
      }
    ]
  }
}

function renderCharts() {
  charts.value.forEach(chart => {
    const element = chartRefs.value[chart.key]
    if (!element) return
    if (!chartInstances[chart.key]) {
      chartInstances[chart.key] = echarts.init(element)
    }
    chartInstances[chart.key].setOption(makeChartOption(chart.key), true)
  })
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
    await nextTick()
    renderCharts()
    ElMessage.success('决策曲线已重新生成')
  } catch (e: any) {
    ElMessage.error('生成失败：' + (e?.response?.data?.message || e?.message || '模型服务不可用'))
  } finally {
    loading.value = false
  }
}

function handleResize() {
  Object.values(chartInstances).forEach(chart => chart.resize())
}

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  if (analysis.value) {
    await nextTick()
    renderCharts()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  Object.values(chartInstances).forEach(chart => chart.dispose())
  chartInstances = {}
})

watch(() => analysis.value, async () => {
  await nextTick()
  renderCharts()
})
</script>

<style scoped>
.page-wrapper { padding: 24px 0; }
.container { max-width: 1280px; margin: 0 auto; padding: 0 32px; }
.page-title { font-size: 28px; font-weight: 600; margin: 0 0 8px; }
.page-desc { font-size: 13px; color: #909399; margin: 0 0 24px; }
.card { background: #fff; border-radius: 8px; padding: 32px; margin-bottom: 16px; }
.alert-warn { background: #fdf6ec; color: #e6a23c; padding: 14px 18px; border-radius: 4px; margin-bottom: 24px; }
.generate-btn { width: 100%; height: 48px; }
.top-alert { background: #ecf5ff; color: #409eff; padding: 14px 18px; border-radius: 4px; margin-bottom: 16px; font-size: 13px; }
.charts-section { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-bottom: 16px; }
.chart-card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); border-top: 2px solid #409eff; min-width: 0; }
.chart-header { margin-bottom: 8px; }
.chart-title { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 18px; font-weight: 600; }
.chart-name { color: #1f2d3d; }
.model-rec { font-size: 12px; color: #909399; white-space: nowrap; }
.model-rec .rec-value { background: #ecf5ff; color: #409eff; padding: 2px 8px; border-radius: 3px; margin-left: 4px; }
.chart-meta { display: flex; gap: 16px; font-size: 12px; color: #909399; margin-bottom: 4px; }
.chart-meta .meta-value { color: #409eff; font-weight: 600; margin-left: 4px; }
.chart-canvas { width: 100%; height: 280px; }
.scenarios-card { background: #fff; border-radius: 8px; padding: 0; box-shadow: 0 1px 4px rgba(0,0,0,0.04); border-top: 2px solid #67c23a; overflow: hidden; margin-bottom: 16px; }
.scenarios-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #f0f9eb; font-size: 15px; font-weight: 600; color: #1f2d3d; }
.scenarios-header .model-tag { background: #67c23a; color: #fff; padding: 2px 8px; border-radius: 3px; font-size: 12px; font-weight: 500; }
.scenarios-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.scenarios-table th, .scenarios-table td { padding: 12px; text-align: center; border-bottom: 1px solid #f0f0f0; }
.scenarios-table th { background: #fafbfc; font-weight: 600; color: #1f2d3d; }
.scenarios-table tr.best { background: #f0f9eb; }
.scenarios-table tr.best td { color: #67c23a; font-weight: 600; }
.rank-circle { display: inline-block; width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 50%; background: #409eff; color: #fff; font-size: 12px; font-weight: 600; }
.scenarios-table tr.best .rank-circle { background: #67c23a; }
.recommended-chip { display: inline-block; margin-left: 6px; padding: 1px 6px; border-radius: 3px; background: #ecf5ff; color: #409eff; font-size: 11px; }
@media (max-width: 1100px) { .charts-section { grid-template-columns: 1fr; } }
</style>
