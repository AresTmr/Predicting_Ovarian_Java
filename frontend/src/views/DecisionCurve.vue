<template>
  <div class="page-wrapper">
    <div class="container">
      <h2 class="page-title">决策曲线</h2>
      <p class="page-desc">比较候选剂量下的预测获卵数与中重度 OHSS 风险。</p>
      <section class="card empty-card" v-if="!result">
        <div class="alert-warn">
          决策曲线 尚未生成监测结果。请先在患者录入页点击"生成监测结果"，或在此处点击下方按钮生成最新监测结果。
        </div>
        <el-button type="primary" size="large" class="generate-btn" :loading="loading" @click="generate">生成最新监测结果</el-button>
      </section>
      <section v-if="result">
        <div class="top-alert">
          固定其他给药变量，仅改变某种 Gn 剂量进行条件敏感性分析；虚线代表中心点出处推荐剂量及其预测结局。
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
            <span class="model-tag">获卵数 / OHSS 率排序</span>
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
                <td>{{ s.name }}</td>
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
import { onMounted, ref, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { predictionApi, type PredictionDto } from '@/api/patient'

const result = ref<PredictionDto | null>(null)
const loading = ref(false)
const chartRefs = ref<Record<string, any>>({})
let chartInstances: Record<string, any> = {}

const charts = ref([
  { key: 'fsh', name: 'FSH', recValue: '>160', oocytes: 12, ohssRate: '1.05%' },
  { key: 'lh',  name: 'LH',  recValue: '75',   oocytes: 12, ohssRate: '1.05%' },
  { key: 'hmg', name: 'HMG', recValue: '150',  oocytes: 12, ohssRate: '1.05%' }
])

const scenarios = ref([
  { rank: 1, name: '情景 A：模型推荐剂量', fsh: '>160',  lh: 75, hmg: 150, oocytes: 12,   ohss: '1.05%' },
  { rank: 2, name: '情景 B',                fsh: '>160',  lh: 75, hmg: 225, oocytes: 12,   ohss: '1.06%' },
  { rank: 3, name: '情景 C',                fsh: '>160', lh: 150, hmg: 150, oocytes: 12,   ohss: '1.07%' },
  { rank: 4, name: '情景 D',                fsh: '>160',  lh: 0,  hmg: 150, oocytes: 11.9, ohss: '1.10%' },
  { rank: 5, name: '情景 E',                fsh: '>160',  lh: 75, hmg: 75,  oocytes: 11.9, ohss: '1.12%' },
  { rank: 6, name: '情景 F',                fsh: '>160',  lh: 75, hmg: 0,   oocytes: 11.9, ohss: '1.10%' },
  { rank: 7, name: '情景 G',                fsh: '80-160', lh: 75, hmg: 150, oocytes: 11.9, ohss: '1.13%' },
  { rank: 8, name: '情景 H',                fsh: '0-80',   lh: 75, hmg: 150, oocytes: 11.8, ohss: '1.16%' }
])

function makeChartOption(name: string) {
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['获卵数', '中重度 OHSS 风险'], top: 0, left: 'center' },
    grid: { left: 40, right: 50, bottom: 40, top: 36 },
    xAxis: { type: 'category', data: ['低', '中低', '中', '中高', '高', '推荐'] },
    yAxis: [
      { type: 'value', name: '获卵数', position: 'left' },
      { type: 'value', name: 'OHSS %', position: 'right' }
    ],
    series: [
      { name: '获卵数', type: 'line', data: [11.0, 11.5, 11.8, 12.0, 12.2, 12.0], smooth: true, itemStyle: { color: '#67c23a' }, lineStyle: { color: '#67c23a', width: 3 } },
      { name: '中重度 OHSS 风险', type: 'line', yAxisIndex: 1, data: [1.05, 1.05, 1.06, 1.06, 1.05, 1.05], smooth: true, itemStyle: { color: '#f56c6c' }, lineStyle: { color: '#f56c6c', width: 3, type: 'dashed' } }
    ]
  }
}
function renderCharts() {
  charts.value.forEach(chart => {
    const el = chartRefs.value[chart.key]
    if (!el) return
    if (!chartInstances[chart.key]) chartInstances[chart.key] = (echarts as any).init(el)
    chartInstances[chart.key].setOption(makeChartOption(chart.name))
  })
}

async function generate() {
  loading.value = true
  try {
    const fake = { e2: 68, lh: 0.1, p: 0.28, fsh: 18.06, endometriumThickness: 4.9, follicleTotalCount: 8, follicleLeftCount: 5, follicleRightCount: 3, follicleMaxDiameter: 8.0, follicleAvgDiameter: 6.06, follicleSizeUnder10: 8, follicleSize10_12: 0, follicleSize13_15: 0, follicleSize16_18: 0, follicleSizeAbove18: 0, fshDose: 250, lhDose: 75, hmgDose: 75, visitNo: 3, stimulationDay: 9, daysSinceLastVisit: 2 } as any
    const r = await predictionApi.predict(fake)
    result.value = r.data
    ElMessage.success('已生成')
    await nextTick(); renderCharts()
  } catch (e: any) {
    result.value = { predictedFshDose: 160, predictedLhDose: 75, predictedHmgDose: 150 } as any
    ElMessage.warning('使用默认数据')
    await nextTick(); renderCharts()
  } finally {
    loading.value = false
  }
}

onMounted(() => { window.addEventListener('resize', () => Object.values(chartInstances).forEach((c: any) => c?.resize())) })
watch(() => result.value, async () => { await nextTick(); renderCharts() })
</script>
<style scoped>
.page-wrapper { padding: 24px 0; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 32px; }
.page-title { font-size: 28px; font-weight: 600; margin: 0 0 8px; }
.page-desc { font-size: 13px; color: #909399; margin: 0 0 24px; }
.card { background: #fff; border-radius: 8px; padding: 32px; margin-bottom: 16px; }
.alert-warn { background: #fdf6ec; color: #e6a23c; padding: 14px 18px; border-radius: 4px; margin-bottom: 24px; }
.generate-btn { width: 100%; height: 48px; }
.top-alert { background: #ecf5ff; color: #409eff; padding: 14px 18px; border-radius: 4px; margin-bottom: 16px; font-size: 13px; }
.charts-section { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px; }
.chart-card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); border-top: 2px solid #409eff; }
.chart-header { margin-bottom: 8px; }
.chart-title { display: flex; justify-content: space-between; align-items: center; font-size: 18px; font-weight: 600; }
.chart-name { color: #1f2d3d; }
.model-rec { font-size: 12px; color: #909399; }
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
</style>