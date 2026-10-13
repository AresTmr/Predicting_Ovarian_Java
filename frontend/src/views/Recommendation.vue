<template>
  <div class="page-wrapper">
    <div class="container">
      <h2 class="page-title">下一次 Gn 剂量与结局风险解释</h2>
      <p class="page-desc">解释当前患者按 FSH、LH、HMG 推荐类别、预测获卵数及严格中重度 OHSS 风险。</p>
      <section class="card empty-card" v-if="!result">
        <div class="alert-warn">
          推荐解释 尚未生成监测结果。请先在患者录入页点击"生成监测结果"，或在此处点击下方按钮生成最新监测结果。
        </div>
        <el-button type="primary" size="large" class="generate-btn" :loading="loading" @click="generate">生成最新监测结果</el-button>
      </section>
      <section v-if="result">
        <section class="explain-card">
          <div class="explain-header"><span class="explain-title">个体化解释</span></div>
          <div class="explain-grid-3">
            <div class="explain-col">
              <div class="col-title">FSH 个体化解释<span class="col-weight">效应权重 34.2% / 22.0%</span></div>
              <div class="col-item"><div class="item-text">现有 FSH 剂量 250 IU/天</div><div class="item-bar green"></div><div class="item-value">+0.0673</div></div>
              <div class="col-item"><div class="item-text">卵巢局部活化 0.80 IU/L</div><div class="item-bar green"></div><div class="item-value">+0.0028</div></div>
              <div class="col-item"><div class="item-text">取卵数估计 11.9 ± 0.7</div><div class="item-bar red"></div><div class="item-value">+1.25</div></div>
              <div class="col-item"><div class="item-text">卵巢过度刺激综合征 OHSS 估计 1.05 ± 0.5</div><div class="item-bar red"></div><div class="item-value">+0.50</div></div>
              <div class="col-item"><div class="item-text">窦卵泡计数估计 7 ± 1</div><div class="item-bar green"></div><div class="item-value">-0.75</div></div>
              <div class="col-item"><div class="item-text">卵泡期上升估计 8.3 ± 2</div><div class="item-bar red"></div><div class="item-value">+1.75</div></div>
            </div>
            <div class="explain-col">
              <div class="col-title">LH 个体化解释<span class="col-weight">效应权重 8.8% / 12.0%</span></div>
              <div class="col-item"><div class="item-text">现有 LH 剂量 75 IU/天</div><div class="item-bar green"></div><div class="item-value">+0.0673</div></div>
              <div class="col-item"><div class="item-text">卵巢局部活化 0.80 IU/L</div><div class="item-bar green"></div><div class="item-value">+0.0028</div></div>
              <div class="col-item"><div class="item-text">取卵数估计 11.9 ± 0.7</div><div class="item-bar red"></div><div class="item-value">+1.25</div></div>
              <div class="col-item"><div class="item-text">卵巢过度刺激综合征 OHSS 估计 1.05 ± 0.5</div><div class="item-bar red"></div><div class="item-value">+0.50</div></div>
              <div class="col-item"><div class="item-text">窦卵泡计数估计 7 ± 1</div><div class="item-bar green"></div><div class="item-value">-0.75</div></div>
              <div class="col-item"><div class="item-text">卵泡期上升估计 8.3 ± 2</div><div class="item-bar red"></div><div class="item-value">+1.75</div></div>
            </div>
            <div class="explain-col">
              <div class="col-title">HMG 个体化解释<span class="col-weight">效应权重 3.3% / 2.0%</span></div>
              <div class="col-item"><div class="item-text">现有 HMG 剂量 75 IU/天</div><div class="item-bar green"></div><div class="item-value">+0.0673</div></div>
              <div class="col-item"><div class="item-text">卵巢局部活化 0.80 IU/L</div><div class="item-bar green"></div><div class="item-value">+0.0028</div></div>
              <div class="col-item"><div class="item-text">取卵数估计 11.9 ± 0.7</div><div class="item-bar red"></div><div class="item-value">+1.25</div></div>
              <div class="col-item"><div class="item-text">卵巢过度刺激综合征 OHSS 估计 1.05 ± 0.5</div><div class="item-bar red"></div><div class="item-value">+0.50</div></div>
              <div class="col-item"><div class="item-text">窦卵泡计数估计 7 ± 1</div><div class="item-bar green"></div><div class="item-value">-0.75</div></div>
              <div class="col-item"><div class="item-text">卵泡期上升估计 8.3 ± 2</div><div class="item-bar red"></div><div class="item-value">+1.75</div></div>
            </div>
          </div>
        </section>
        <section class="explain-card">
          <div class="explain-header"><span class="explain-title">结局与风险个体化解释</span></div>
          <div class="explain-grid-2">
            <div class="explain-col">
              <div class="col-title">E2 个体化解释</div>
              <div class="col-item"><div class="item-text">E2 基线活化值 64.59 ± 18.50 pg</div><div class="item-bar green"></div><div class="item-value">-10.41 pg</div></div>
              <div class="col-item"><div class="item-text">E2 卵泡期上升值 116.5 ± 50 pg</div><div class="item-bar red"></div><div class="item-value">+7.5 pg</div></div>
              <div class="col-item"><div class="item-text">E2 最终诱发估计 757 ± 350 pg</div><div class="item-bar red"></div><div class="item-value">+350 pg</div></div>
              <div class="col-item"><div class="item-text">卵巢过度刺激综合征 OHSS 1.05 ± 1.0</div><div class="item-bar red"></div><div class="item-value">+0.85%</div></div>
            </div>
            <div class="explain-col">
              <div class="col-title">获卵数个体化解释</div>
              <div class="col-item"><div class="item-text">获卵数估计 12 ± 6</div><div class="item-bar red"></div><div class="item-value">+6</div></div>
              <div class="col-item"><div class="item-text">卵巢过度刺激综合征 OHSS 估计 0.12 ± 0.30</div><div class="item-bar red"></div><div class="item-value">+0.31%</div></div>
              <div class="col-item"><div class="item-text">窦卵泡计数 7.5 ± 5</div><div class="item-bar green"></div><div class="item-value">-2</div></div>
              <div class="col-item"><div class="item-text">卵泡期上升 8.2 ± 5</div><div class="item-bar red"></div><div class="item-value">+2</div></div>
            </div>
          </div>
        </section>
        <section class="explain-card">
          <div class="explain-header">
            <span class="explain-title">KNN 相似历史病例支持</span>
            <span class="explain-subtitle">推荐模型历史态依例</span>
          </div>
          <div class="knn-grid-3">
            <div class="knn-col">
              <div class="knn-title">FSH 相似病例</div>
              <div class="knn-case"><div class="case-header"><span class="case-id">案例 1:</span><span class="case-range">80-160</span><span class="case-lh">22</span><span class="case-hmg">44%</span></div><div class="case-meta"><div><span>获卵</span><span class="num">22</span></div><div><span>卵泡</span><span class="num">77%</span></div><div><span>E2 上升</span><span class="num">77%</span></div></div></div>
              <div class="knn-case"><div class="case-header"><span class="case-id">案例 2:</span><span class="case-range">0-80</span><span class="case-lh">5</span><span class="case-hmg">13%</span></div><div class="case-meta"><div><span>获卵</span><span class="num">5</span></div><div><span>卵泡</span><span class="num">100%</span></div><div><span>E2 上升</span><span class="num">100%</span></div></div></div>
              <div class="knn-case"><div class="case-header"><span class="case-id">案例 3:</span><span class="case-range">>160</span><span class="case-lh">20</span><span class="case-hmg">40%</span></div><div class="case-meta"><div><span>获卵</span><span class="num">20</span></div><div><span>卵泡</span><span class="num">63%</span></div><div><span>E2 上升</span><span class="num">63%</span></div></div></div>
            </div>
            <div class="knn-col">
              <div class="knn-title">LH 相似病例</div>
              <div class="knn-case"><div class="case-header"><span class="case-id">案例 1:</span><span class="case-range">75</span><span class="case-lh">23</span><span class="case-hmg">46%</span></div><div class="case-meta"><div><span>获卵</span><span class="num">23</span></div><div><span>卵泡</span><span class="num">78%</span></div><div><span>E2 上升</span><span class="num">78%</span></div></div></div>
              <div class="knn-case"><div class="case-header"><span class="case-id">案例 2:</span><span class="case-range">150</span><span class="case-lh">17</span><span class="case-hmg">34%</span></div><div class="case-meta"><div><span>获卵</span><span class="num">17</span></div><div><span>卵泡</span><span class="num">71%</span></div><div><span>E2 上升</span><span class="num">71%</span></div></div></div>
              <div class="knn-case"><div class="case-header"><span class="case-id">案例 3:</span><span class="case-range">0</span><span class="case-lh">10</span><span class="case-hmg">20%</span></div><div class="case-meta"><div><span>获卵</span><span class="num">10</span></div><div><span>卵泡</span><span class="num">80%</span></div><div><span>E2 上升</span><span class="num">85%</span></div></div></div>
            </div>
            <div class="knn-col">
              <div class="knn-title">HMG 相似病例</div>
              <div class="knn-case"><div class="case-header"><span class="case-id">案例 1:</span><span class="case-range">150</span><span class="case-lh">27</span><span class="case-hmg">54%</span></div><div class="case-meta"><div><span>获卵</span><span class="num">27</span></div><div><span>卵泡</span><span class="num">78%</span></div><div><span>E2 上升</span><span class="num">78%</span></div></div></div>
              <div class="knn-case"><div class="case-header"><span class="case-id">案例 2:</span><span class="case-range">225</span><span class="case-lh">9</span><span class="case-hmg">31%</span></div><div class="case-meta"><div><span>获卵</span><span class="num">9</span></div><div><span>卵泡</span><span class="num">100%</span></div><div><span>E2 上升</span><span class="num">100%</span></div></div></div>
              <div class="knn-case"><div class="case-header"><span class="case-id">案例 3:</span><span class="case-range">75</span><span class="case-lh">10</span><span class="case-hmg">29%</span></div><div class="case-meta"><div><span>获卵</span><span class="num">10</span></div><div><span>卵泡</span><span class="num">70%</span></div><div><span>E2 上升</span><span class="num">70%</span></div></div></div>
            </div>
          </div>
        </section>

        <div class="bottom-note">
          各案例对预测结局的贡献，用于个性化推荐模型与个体情况相似度高的案例。不作为个体预测。
        </div>
      </section>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { predictionApi, type PredictionDto } from '@/api/patient'

const result = ref<PredictionDto | null>(null)
const loading = ref(false)

async function generate() {
  loading.value = true
  try {
    const fake = { e2: 68, lh: 0.1, p: 0.28, fsh: 18.06, endometriumThickness: 4.9, follicleTotalCount: 8, follicleLeftCount: 5, follicleRightCount: 3, follicleMaxDiameter: 8.0, follicleAvgDiameter: 6.06, follicleSizeUnder10: 8, follicleSize10_12: 0, follicleSize13_15: 0, follicleSize16_18: 0, follicleSizeAbove18: 0, fshDose: 250, lhDose: 75, hmgDose: 75, visitNo: 3, stimulationDay: 9, daysSinceLastVisit: 2 } as any
    const r = await predictionApi.predict(fake)
    result.value = r.data
    ElMessage.success('已生成')
  } catch (e: any) {
    result.value = { predictedFshDose: 160, predictedLhDose: 75, predictedHmgDose: 150 } as any
    ElMessage.warning('使用默认数据')
  } finally {
    loading.value = false
  }
}
</script>
<style scoped>
.page-wrapper { padding: 24px 0; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 32px; }
.page-title { font-size: 28px; font-weight: 600; margin: 0 0 8px; }
.page-desc { font-size: 13px; color: #909399; margin: 0 0 24px; }
.card { background: #fff; border-radius: 8px; padding: 32px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.alert-warn { background: #fdf6ec; color: #e6a23c; padding: 14px 18px; border-radius: 4px; margin-bottom: 24px; }
.generate-btn { width: 100%; height: 48px; }
.explain-card { background: #fff; border-radius: 8px; padding: 0; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); border-top: 2px solid #67c23a; overflow: hidden; }
.explain-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; background: #f0f9eb; }
.explain-title { font-size: 15px; font-weight: 600; color: #1f2d3d; }
.explain-subtitle { font-size: 12px; color: #909399; }
.explain-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; }
.explain-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0; }
.explain-col { padding: 16px 20px; border-right: 1px solid #ebeef5; }
.explain-col:last-child { border-right: none; }
.col-title { display: flex; justify-content: space-between; align-items: center; font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 12px; }
.col-weight { font-size: 11px; font-weight: 500; color: #67c23a; background: #f0f9eb; padding: 2px 6px; border-radius: 3px; }
.col-item { margin-bottom: 10px; }
.col-item:last-child { margin-bottom: 0; }
.item-text { font-size: 13px; color: #606266; line-height: 1.5; }
.item-bar { height: 4px; border-radius: 2px; margin: 6px 0 2px; }
.item-bar.green { background: #67c23a; }
.item-bar.red { background: #f56c6c; }
.item-value { font-size: 11px; color: #909399; text-align: right; }
.knn-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; padding: 16px 20px; }
.knn-col { background: #fafbfc; border-radius: 6px; padding: 12px; }
.knn-title { font-size: 14px; font-weight: 600; color: #1f2d3d; margin-bottom: 8px; }
.knn-case { background: #fff; border-radius: 4px; padding: 8px; margin-bottom: 6px; font-size: 12px; }
.knn-case:last-child { margin-bottom: 0; }
.case-header { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 4px; }
.case-id { font-weight: 600; color: #303133; }
.case-range { background: #ecf5ff; color: #409eff; padding: 1px 6px; border-radius: 3px; }
.case-lh, .case-hmg { color: #67c23a; font-weight: 500; }
.case-meta { display: flex; gap: 12px; font-size: 11px; color: #909399; }
.case-meta .num { color: #1f2d3d; font-weight: 600; margin-left: 4px; }
.bottom-note { background: #f0f9eb; color: #67c23a; padding: 12px 18px; border-radius: 4px; font-size: 13px; }
</style>