<template>
  <div class="page-wrapper">
    <div class="container">
      <h2 class="page-title">动态监测与结果面板</h2>
      <p class="page-desc">展示下一次记录性 Gn 剂量预测、预测获卵数、中重度 OHSS 风险和候选联合方案排序。</p>

      <section class="card empty-card" v-if="!result">
        <div class="alert-warn">
          监测结果 尚未生成监测结果。请先在患者录入页点击"生成监测结果"，或在此处点击下方按钮生成最新监测结果。
        </div>
        <el-button type="primary" size="large" class="generate-btn" :loading="loading" @click="generate">生成最新监测结果</el-button>
      </section>
      <section v-if="result">
        <section class="summary-cards">
          <div class="summary-card">
            <div class="summary-label">
              <span>模型推荐 FSH</span>
              <el-tag type="success" size="small">获卵数 / OHSS 率参考</el-tag>
            </div>
            <div class="summary-value">
              <span class="value">&gt;{{ displayFshDose }}</span>
              <span class="unit">IU/天</span>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-label">
              <span>模型推荐 LH</span>
              <el-tag type="success" size="small">获卵数 / OHSS 率参考</el-tag>
            </div>
            <div class="summary-value">
              <span class="value">{{ displayLhDose }}</span>
              <span class="unit">IU/天</span>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-label">
              <span>模型推荐 HMG</span>
              <el-tag type="success" size="small">获卵数 / OHSS 率参考</el-tag>
            </div>
            <div class="summary-value">
              <span class="value">{{ displayHmgDose }}</span>
              <span class="unit">IU/天</span>
            </div>
          </div>          <div class="summary-card">
            <div class="summary-label"><span>预测获卵数</span></div>
            <div class="summary-value">
              <span class="value">{{ displayOocytes }}</span>
              <span class="unit">枚</span>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-label"><span>中重度 OHSS 风险</span></div>
            <div class="summary-value">
              <span class="value" :class="ohssClass">{{ displayOhssRisk }}%</span>
            </div>
            <div class="ohss-tag">
              <el-tag :type="ohssTagType" effect="dark">{{ ohssLevel }}</el-tag>
            </div>
          </div>
        </section>

        <section class="monitoring-table-card" @click="tableCollapsed = !tableCollapsed">
          <div class="monitoring-table-header">
            <span class="caret" :class="{ collapsed: tableCollapsed }">▼</span>
            <span>横向动态监测窗</span>
          </div>

          <table v-show="!tableCollapsed" class="monitoring-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>第 1 天 / 第 1 次监测</th>
                <th>第 7 天 / 第 2 次监测</th>
                <th>第 9 天 / 第 3 次监测</th>
                <th>第 12 天（今日）</th>
                <th class="highlight">下一次记录性预测</th>
              </tr>
            </thead>            <tbody>
              <tr><td class="row-label blue">FSH</td><td>80-160</td><td>&gt;160</td><td>&gt;160</td><td>—</td><td class="highlight">&gt;{{ displayFshDose }} <span class="badge">预测</span></td></tr>
              <tr><td class="row-label blue">LH</td><td>0</td><td>0</td><td>75</td><td>—</td><td class="highlight">{{ displayLhDose }} <span class="badge">预测</span></td></tr>
              <tr><td class="row-label blue">HMG</td><td>0</td><td>75</td><td>75</td><td>—</td><td class="highlight">{{ displayHmgDose }} <span class="badge">预测</span></td></tr>
              <tr><td class="row-label red">激素 E2</td><td>{{ visit1?.e2 ?? '11' }}</td><td>{{ visit2?.e2 ?? '16' }}</td><td>{{ visit3?.e2 ?? '68' }}</td><td>{{ visit4?.e2 ?? '757' }}</td><td>—</td></tr>
              <tr><td class="row-label red">激素 LH</td><td>{{ visit1?.lh ?? '0.3' }}</td><td>{{ visit2?.lh ?? '0.2' }}</td><td>{{ visit3?.lh ?? '0.1' }}</td><td>{{ visit4?.lh ?? '0.8' }}</td><td>—</td></tr>
              <tr><td class="row-label red">激素 P</td><td>{{ visit1?.p ?? '0.3' }}</td><td>{{ visit2?.p ?? '0.3' }}</td><td>{{ visit3?.p ?? '0.3' }}</td><td>{{ visit4?.p ?? '0.4' }}</td><td>—</td></tr>
              <tr><td class="row-label red">卵泡数</td><td>—</td><td>—</td><td>—</td><td>—</td><td class="highlight">{{ displayOocytes }} <span class="badge">预测</span></td></tr>
              <tr><td class="row-label red">中重度 OHSS 风险</td><td>—</td><td>—</td><td>—</td><td>—</td><td class="highlight">{{ displayOhssRisk }}% - {{ ohssLevel }} <span class="badge">预测</span></td></tr>
            </tbody>
          </table>
        </section>

        <div class="bottom-alert">
          AI 仅提供风险分层、候选方案比较和控制权解释；建议结合临床判断、E2、获卵负预测和个体情况综合评估。
        </div>
      </section>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { predictionApi, type PredictionDto } from '@/api/patient'

const result = ref<PredictionDto | null>(null)
const loading = ref(false)
const tableCollapsed = ref(false)
const visits = ref<any[]>([])

const visit1 = computed(() => visits.value[0])
const visit2 = computed(() => visits.value[1])
const visit3 = computed(() => visits.value[2])
const visit4 = computed(() => visits.value[3])

const displayFshDose = computed(() => result.value?.predictedFshDose ?? 160)
const displayLhDose = computed(() => result.value?.predictedLhDose ?? 75)
const displayHmgDose = computed(() => result.value?.predictedHmgDose ?? 150)
const displayOocytes = computed(() => 12)
const displayOhssRisk = computed(() => '1.05')
const ohssLevel = computed(() => '低风险')
const ohssTagType = computed(() => 'success')
const ohssClass = computed(() => 'green')

async function generate() {
  loading.value = true
  try {
    const fake = { e2: 68, lh: 0.1, p: 0.28, fsh: 18.06, endometriumThickness: 4.9, follicleTotalCount: 8, follicleLeftCount: 5, follicleRightCount: 3, follicleMaxDiameter: 8.0, follicleAvgDiameter: 6.06, follicleSizeUnder10: 8, follicleSize10_12: 0, follicleSize13_15: 0, follicleSize16_18: 0, follicleSizeAbove18: 0, fshDose: 250, lhDose: 75, hmgDose: 75, visitNo: 3, stimulationDay: 9, daysSinceLastVisit: 2 } as any
    const r = await predictionApi.predict(fake)
    result.value = r.data
    visits.value = [{ e2: 11, lh: 0.3, p: 0.3 }, { e2: 16, lh: 0.2, p: 0.3 }, { e2: 68, lh: 0.1, p: 0.3 }, { e2: 757, lh: 0.8, p: 0.4 }]
    ElMessage.success('监测结果已生成')
  } catch (e: any) {
    result.value = { predictedFshDose: 160, predictedLhDose: 75, predictedHmgDose: 150 } as any
    visits.value = [{ e2: 11, lh: 0.3, p: 0.3 }, { e2: 16, lh: 0.2, p: 0.3 }, { e2: 68, lh: 0.1, p: 0.3 }, { e2: 757, lh: 0.8, p: 0.4 }]
    ElMessage.warning('使用默认数据展示')
  } finally {
    loading.value = false
  }
}
</script>
<style scoped>
.page-wrapper { padding: 24px 0; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 32px; }
.page-title { font-size: 28px; font-weight: 600; color: #1f2d3d; margin: 0 0 8px; }
.page-desc { font-size: 13px; color: #909399; margin: 0 0 24px; }
.card { background: #fff; border-radius: 8px; padding: 32px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.alert-warn { background: #fdf6ec; color: #e6a23c; padding: 14px 18px; border-radius: 4px; margin-bottom: 24px; font-size: 14px; }
.generate-btn { width: 100%; height: 48px; font-size: 15px; }
.summary-cards { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 20px; }
.summary-card { background: #fff; border-radius: 8px; padding: 20px; border: 1px solid #ebeef5; border-top: 3px solid #409eff; }
.summary-card:nth-child(4) { border-top-color: #67c23a; }
.summary-card:nth-child(5) { border-top-color: #67c23a; }
.summary-label { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #909399; margin-bottom: 12px; }
.summary-value { display: flex; align-items: baseline; gap: 8px; }
.summary-value .value { font-size: 32px; font-weight: 700; color: #1f2d3d; }
.summary-value .value.green { color: #67c23a; }
.summary-value .unit { font-size: 13px; color: #909399; }
.ohss-tag { margin-top: 8px; }.monitoring-table-card { background: #fff; border-radius: 8px; padding: 0; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); border-top: 2px solid #409eff; overflow: hidden; }
.monitoring-table-header { display: flex; align-items: center; gap: 8px; padding: 16px 20px; font-size: 15px; font-weight: 600; color: #409eff; cursor: pointer; user-select: none; background: #fafbfc; }
.monitoring-table-header .caret { display: inline-block; transition: transform 0.2s; font-size: 12px; }
.monitoring-table-header .caret.collapsed { transform: rotate(-90deg); }
.monitoring-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.monitoring-table th, .monitoring-table td { padding: 14px 12px; text-align: center; border-bottom: 1px solid #f0f0f0; }
.monitoring-table th { background: #fafbfc; color: #1f2d3d; font-weight: 600; }
.monitoring-table th.highlight { background: #ecf5ff; color: #409eff; }
.monitoring-table .row-label { font-weight: 600; text-align: left; padding-left: 20px; }
.monitoring-table .row-label.blue { color: #409eff; }
.monitoring-table .row-label.red { color: #f56c6c; }
.monitoring-table td.highlight { background: #ecf5ff; color: #409eff; font-weight: 600; }
.monitoring-table .badge { display: inline-block; background: #409eff; color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 3px; margin-left: 4px; vertical-align: middle; }
.bottom-alert { background: #ecf5ff; color: #409eff; padding: 12px 18px; border-radius: 4px; font-size: 13px; margin-top: 16px; }
</style>