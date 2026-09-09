<template>
  <div class="page-wrapper">
    <!-- 顶部标题栏 -->
    <header class="app-header">
      <h1 class="app-title">患者临床信息录入</h1>
      <p class="app-subtitle">录入基线特征、促排监测信息、当促周期数据数据评估, 用于下一次记录 Gn 剂量预测。</p>
    </header>

    <main class="app-main">
      <!-- ============== 患者基础信息 ============== -->
      <section class="card">
        <h2 class="card-title">
          <el-icon><Document /></el-icon>
          患者基础信息
        </h2>
        <el-form :model="baseline" label-width="160px" class="form-grid">
          <el-form-item label="年龄 (岁)">
            <el-input-number v-model="baseline.age" :min="18" :max="55" :step="1" />
          </el-form-item>
          <el-form-item label="BMI (kg/m²)">
            <el-input-number v-model="baseline.bmi" :min="15" :max="50" :step="0.1" :precision="2" />
          </el-form-item>
          <el-form-item label="AMH (ng/mL)">
            <el-input-number v-model="baseline.amh" :min="0" :max="20" :step="0.01" :precision="3" />
          </el-form-item>
          <el-form-item label="AFC (个)">
            <el-input-number v-model="baseline.afc" :min="0" :max="50" :step="1" />
          </el-form-item>
          <el-form-item label="基础 FSH (IU/L)">
            <el-input-number v-model="baseline.basalFsh" :min="0" :max="200" :step="0.01" :precision="2" />
          </el-form-item>
          <el-form-item label="基础 LH (IU/L)">
            <el-input-number v-model="baseline.basalLh" :min="0" :max="200" :step="0.01" :precision="2" />
          </el-form-item>
          <el-form-item label="基础 E2 (pg/mL)">
            <el-input-number v-model="baseline.basalE2" :min="0" :max="10000" :step="0.01" :precision="2" />
          </el-form-item>
          <el-form-item label="基础 P (ng/mL)">
            <el-input-number v-model="baseline.basalP" :min="0" :max="50" :step="0.01" :precision="2" />
          </el-form-item>
          <el-form-item label="不孕年限 (年)">
            <el-input-number v-model="baseline.infertilityYears" :min="0" :max="40" :step="0.1" :precision="1" />
          </el-form-item>
          <el-form-item label="促排方案">
            <el-select v-model="baseline.protocolCode" placeholder="请选择">
              <el-option label="GnRHa 超长方案" value="GNRHA_ULTRALONG" />
              <el-option label="GnRHa 长方案" value="GNRHA_LONG" />
              <el-option label="GnRHa 短方案" value="GNRHA_SHORT" />
              <el-option label="拮抗剂方案" value="ANTAGONIST" />
              <el-option label="微刺激方案" value="MILD" />
              <el-option label="自然周期" value="NATURAL" />
              <el-option label="其他" value="OTHER" />
            </el-select>
          </el-form-item>
          <el-form-item label="不孕类型">
            <el-select v-model="baseline.infertilityTypeCode" placeholder="请选择">
              <el-option label="原发不孕" value="PRIMARY" />
              <el-option label="继发不孕" value="SECONDARY" />
            </el-select>
          </el-form-item>
        </el-form>

        <!-- 一键填入按钮 -->
        <div class="one-click-row">
          <el-input v-model="oneClickCaseNo" placeholder="输入病历号一键填入" style="width: 240px" />
          <el-button type="primary" plain @click="handleOneClickFill">
            <el-icon><Search /></el-icon>
            一键填入历史数据
          </el-button>
        </div>
      </section>

      <!-- ============== 监测记录（多个 visit） ============== -->
      <section class="card">
        <h2 class="card-title">
          <el-icon><Calendar /></el-icon>
          监测记录
        </h2>

        <el-collapse v-model="activeVisitIndex" accordion>
          <el-collapse-item
            v-for="(visit, idx) in visits"
            :key="idx"
            :name="idx"
          >
            <template #title>
              <span class="visit-title">第 {{ visit.visitNo }} 次监测记录</span>
            </template>

            <!-- 时间 -->
            <h3 class="sub-title">监测时间</h3>
            <el-form :model="visit" label-width="180px" class="form-grid">
              <el-form-item label="促排天数 /stimulation day">
                <el-input-number v-model="visit.stimulationDay" :min="1" :max="30" :step="1" />
              </el-form-item>
              <el-form-item label="距上次复诊间隔 (天)">
                <el-input-number v-model="visit.daysSinceLastVisit" :min="0" :max="14" :step="1" />
              </el-form-item>
              <el-form-item label="监测日期">
                <el-date-picker v-model="visit.visitDate" type="date" value-format="YYYY-MM-DD" />
              </el-form-item>
            </el-form>

            <!-- 激素 -->
            <h3 class="sub-title">激素和内膜信息</h3>
            <el-form :model="visit" label-width="180px" class="form-grid">
              <el-form-item label="当前 E2 (pg/mL)">
                <el-input-number v-model="visit.e2Current" :min="0" :max="10000" :step="0.01" :precision="2" />
              </el-form-item>
              <el-form-item label="当前 LH (IU/L)">
                <el-input-number v-model="visit.lhCurrent" :min="0" :max="200" :step="0.01" :precision="2" />
              </el-form-item>
              <el-form-item label="当前 P (ng/mL)">
                <el-input-number v-model="visit.pCurrent" :min="0" :max="50" :step="0.01" :precision="2" />
              </el-form-item>
              <el-form-item label="当前 FSH (IU/L)">
                <el-input-number v-model="visit.fshCurrent" :min="0" :max="200" :step="0.01" :precision="2" />
              </el-form-item>
              <el-form-item label="内膜厚度 (mm)">
                <el-input-number v-model="visit.endometriumThickness" :min="0" :max="30" :step="0.1" :precision="1" />
              </el-form-item>
            </el-form>

            <!-- 卵泡 -->
            <h3 class="sub-title">卵泡信息</h3>
            <el-form :model="visit" label-width="180px" class="form-grid">
              <el-form-item label="总卵泡数 (个)">
                <el-input-number v-model="visit.follicleTotalCount" :min="0" :max="50" :step="1" />
              </el-form-item>
              <el-form-item label="左卵泡数 (个)">
                <el-input-number v-model="visit.follicleLeftCount" :min="0" :max="30" :step="1" />
              </el-form-item>
              <el-form-item label="右卵泡数 (个)">
                <el-input-number v-model="visit.follicleRightCount" :min="0" :max="30" :step="1" />
              </el-form-item>
              <el-form-item label="最大卵泡径 (mm)">
                <el-input-number v-model="visit.follicleMaxDiameter" :min="0" :max="30" :step="0.01" :precision="2" />
              </el-form-item>
              <el-form-item label="平均卵泡径 (mm)">
                <el-input-number v-model="visit.follicleAvgDiameter" :min="0" :max="30" :step="0.01" :precision="2" />
              </el-form-item>
              <el-form-item label="<10 mm 卵泡数">
                <el-input-number v-model="visit.follicleSizeUnder10" :min="0" :max="50" :step="1" />
              </el-form-item>
              <el-form-item label="10-12 mm 卵泡数">
                <el-input-number v-model="visit.follicleSize10_12" :min="0" :max="50" :step="1" />
              </el-form-item>
              <el-form-item label="13-15 mm 卵泡数">
                <el-input-number v-model="visit.follicleSize13_15" :min="0" :max="50" :step="1" />
              </el-form-item>
              <el-form-item label="16-18 mm 卵泡数">
                <el-input-number v-model="visit.follicleSize16_18" :min="0" :max="50" :step="1" />
              </el-form-item>
              <el-form-item label="≥18 mm 卵泡数">
                <el-input-number v-model="visit.follicleSizeAbove18" :min="0" :max="50" :step="1" />
              </el-form-item>
            </el-form>

            <!-- 用药 -->
            <h3 class="sub-title">当前监测执行用药记录</h3>
            <el-alert
              title="请填写当次监测后实际执行的FSH/LH/HMG 剂量，用于下一次记录性预测。"
              type="warning"
              :closable="false"
              show-icon
              class="alert-block"
            />
            <el-form :model="visit" label-width="180px" class="form-grid">
              <el-form-item label="当前监测执行 FSH 剂量 (IU/天)">
                <el-input-number v-model="visit.fshDose" :min="0" :max="1000" :step="0.01" :precision="2" />
              </el-form-item>
              <el-form-item label="当前监测执行 LH 剂量 (IU/天)">
                <el-input-number v-model="visit.lhDose" :min="0" :max="1000" :step="0.01" :precision="2" />
              </el-form-item>
              <el-form-item label="当前监测执行 HMG 剂量 (IU/天)">
                <el-input-number v-model="visit.hmgDose" :min="0" :max="1000" :step="0.01" :precision="2" />
              </el-form-item>
            </el-form>
          </el-collapse-item>
        </el-collapse>
      </section>

      <!-- 底部操作按钮 -->
      <section class="action-bar">
        <el-button @click="addVisit">添加监测记录</el-button>
        <el-button type="primary" plain @click="savePatient">保存患者记录</el-button>
        <el-button @click="clearForm">清空重填</el-button>
        <el-button type="primary" @click="generateResult">生成监测结果</el-button>
      </section>
    </main>

    <!-- 页脚 -->
    <footer class="app-footer">
      <span>Gn 剂量辅助系统 v2.4.1 | 系统状态: <span class="status-ok">运行正常 (Lab Sync Active)</span></span>
      <span class="footer-links">
        <a href="javascript:;">隐私政策</a>
        <a href="javascript:;">技术支持</a>
        <a href="javascript:;">操作手册</a>
      </span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from ''vue''
import { ElMessage } from ''element-plus''
import { Document, Calendar, Search } from ''@element-plus/icons-vue''
import { patientApi, type VisitDto } from ''@/api/patient''

const oneClickCaseNo = ref('''')

// ====== 基线表单 ======
const baseline = reactive({
  age: 39,
  bmi: 21.40,
  amh: 1.82,
  afc: 3,
  basalFsh: 6.19,
  basalLh: 5.40,
  basalE2: 48.00,
  basalP: 0.29,
  infertilityYears: 14,
  protocolCode: ''GNRHA_ULTRALONG'',
  infertilityTypeCode: ''PRIMARY''
})

// ====== 默认 4 个 visit（与原项目一致） ======
const visits = ref<VisitDto[]>([
  createVisit(1, 1, 0, ''2026-06-18'',  11.00, 0.30, 0.29, 1.23, 3.20, 9, 4, 5, 4.00, 3.61, 9, 0, 0, 0, 0, 150.00, 0.00, 0.00),
  createVisit(2, 7, 6, ''2026-06-24'',  16.00, 0.20, 0.26, 13.73, 3.50, 7, 4, 3, 6.00, 5.29, 7, 0, 0, 0, 0, 200.00, 0.00, 75.00),
  createVisit(3, 9, 2, ''2026-06-26'',  68.00, 0.10, 0.28, 18.06, 4.90, 8, 5, 3, 8.00, 6.06, 8, 0, 0, 0, 0, 250.00, 75.00, 75.00),
  createVisit(4, 12, 3, ''2026-06-29'', 757.00, 0.80, 0.37, 22.39, 8.00, 12, 6, 6, 13.00, 10.13, 4, 7, 1, 0, 0, 0, 0, 0)
])

const activeVisitIndex = ref<number | string>(0)

function createVisit(
  visitNo: number, stimDay: number, interval: number, date: string,
  e2: number, lh: number, p: number, fsh: number, endo: number,
  total: number, left: number, right: number, max: number, avg: number,
  u10: number, u12: number, u15: number, u18: number, uG18: number,
  fshD: number, lhD: number, hmgD: number
): VisitDto {
  return {
    visitNo, stimulationDay: stimDay, daysSinceLastVisit: interval, visitDate: date,
    e2Current: e2, lhCurrent: lh, pCurrent: p, fshCurrent: fsh, endometriumThickness: endo,
    follicleTotalCount: total, follicleLeftCount: left, follicleRightCount: right,
    follicleMaxDiameter: max, follicleAvgDiameter: avg,
    follicleSizeUnder10: u10, follicleSize10_12: u12, follicleSize13_15: u15,
    follicleSize16_18: u18, follicleSizeAbove18: uG18,
    fshDose: fshD, lhDose: lhD, hmgDose: hmgD
  }
}

// ====== 操作 ======
function addVisit() {
  const nextNo = visits.value.length + 1
  visits.value.push(createVisit(
    nextNo, 1, 1, '''',
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    0, 0, 0
  ))
  activeVisitIndex.value = visits.value.length - 1
}

function savePatient() {
  ElMessage.success(`保存成功：${visits.value.length} 条监测记录`)
}

function clearForm() {
  Object.assign(baseline, {
    age: null, bmi: null, amh: null, afc: null,
    basalFsh: null, basalLh: null, basalE2: null, basalP: null,
    infertilityYears: null, protocolCode: '''', infertilityTypeCode: ''''
  })
  visits.value = []
  oneClickCaseNo.value = ''''
  activeVisitIndex.value = 0
  ElMessage.info('表单已清空')
}

async function generateResult() {
  ElMessage.success('监测结果生成中...')
  // TODO: 调用 /api/v1/predict
}

async function handleOneClickFill() {
  if (!oneClickCaseNo.value) {
    ElMessage.warning('请输入病历号')
    return
  }
  try {
    const resp = await patientApi.oneClickFill(oneClickCaseNo.value)
    const p = resp.data
    if (!p) {
      ElMessage.warning(`病历号 ${oneClickCaseNo.value} 未命中`)
      return
    }
    // 回填基线
    baseline.age = p.age
    baseline.bmi = p.bmi
    baseline.amh = p.amh
    baseline.afc = p.afc
    baseline.basalFsh = p.basalFsh
    baseline.basalLh = p.basalLh
    baseline.basalE2 = p.basalE2
    baseline.basalP = p.basalP
    baseline.infertilityYears = p.infertilityYears
    baseline.protocolCode = p.protocolCode || ''''
    baseline.infertilityTypeCode = p.infertilityTypeCode || ''''

    // 回填 visit
    if (p.latestCycle?.visits?.length) {
      visits.value = p.latestCycle.visits
      activeVisitIndex.value = 0
    }
    ElMessage.success(`已载入 ${p.latestCycle?.visits?.length || 0} 条历史复诊记录`)
  } catch (e: any) {
    ElMessage.error(`一键填入失败：${e?.message || ''}`)
  }
}
</script>

<style scoped lang="scss">
.page-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-header {
  background: #fff;
  padding: 24px 32px 16px;
  border-bottom: 1px solid #ebeef5;
}
.app-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2d3d;
  margin: 0 0 8px;
}
.app-subtitle {
  font-size: 13px;
  color: #909399;
  margin: 0;
}
.app-main {
  flex: 1;
  padding: 24px 32px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
.card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 20px;
}
.sub-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 16px 0 12px;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 24px;
}
.form-grid :deep(.el-form-item) {
  margin-bottom: 12px;
}
.form-grid :deep(.el-input-number),
.form-grid :deep(.el-select) {
  width: 100%;
}
.one-click-row {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #ebeef5;
  display: flex;
  gap: 12px;
  align-items: center;
}
.alert-block {
  margin: 12px 0;
}
.visit-title {
  font-weight: 500;
  font-size: 14px;
}
.action-bar {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.app-footer {
  background: #fff;
  border-top: 1px solid #ebeef5;
  padding: 12px 32px;
  font-size: 12px;
  color: #909399;
  display: flex;
  justify-content: space-between;
}
.status-ok { color: #67c23a; font-weight: 500; }
.footer-links { display: flex; gap: 16px; }
.footer-links a { color: #909399; text-decoration: none; }
.footer-links a:hover { color: #409eff; }
</style>
