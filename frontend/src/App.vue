<template>
  <el-config-provider>
    <div class="app-shell">
      <header class="app-header">
        <div class="header-inner">
          <div class="brand">
            <div class="brand-icon"><el-icon><Lightning /></el-icon></div>
            <div class="brand-text">
              <h1 class="brand-title">Gn 剂量辅助系统</h1>
              <p class="brand-subtitle">医生端临床辅助决策界面</p>
            </div>
          </div>
          <nav class="nav-tabs">
            <router-link to="/patient-entry" class="nav-tab" active-class="active">患者录入</router-link>
            <router-link to="/monitoring-result" class="nav-tab" active-class="active">监测结果</router-link>
            <router-link to="/decision-curve" class="nav-tab" active-class="active">决策曲线</router-link>
            <router-link to="/recommendation" class="nav-tab" active-class="active">推荐解释</router-link>
          </nav>
        </div>
      </header>
      <main class="app-main"><router-view /></main>
      <footer class="app-footer">
        <div class="footer-inner">
          <span>Gn 剂量辅助系统 v2.4.1 | 系统状态: <span class="status-ok">运行正常 (Lab Sync Active)</span></span>
          <span class="footer-links">
            <a href="javascript:void(0);">隐私政策</a>
            <a href="javascript:void(0);">技术支持</a>
            <a href="javascript:void(0);">操作手册</a>
          </span>
        </div>
      </footer>
    </div>
  </el-config-provider>
</template>
<script setup lang="ts">
import { Lightning } from "@element-plus/icons-vue"
</script>
<style>
html, body, #app { height: 100%; margin: 0; font-family: -apple-system, "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f7fa; }
.app-shell { min-height: 100vh; display: flex; flex-direction: column; }
.app-header { background: #fff; border-bottom: 1px solid #ebeef5; position: sticky; top: 0; z-index: 10; }
.header-inner { max-width: 1200px; margin: 0 auto; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }
.brand { display: flex; align-items: center; gap: 12px; }
.brand-icon { width: 36px; height: 36px; background: linear-gradient(135deg, #409eff, #36cfc9); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 20px; }
.brand-text { display: flex; flex-direction: column; }
.brand-title { font-size: 18px; font-weight: 600; color: #1f2d3d; margin: 0; }
.brand-subtitle { font-size: 12px; color: #909399; margin: 2px 0 0; }
.nav-tabs { display: flex; gap: 8px; }
.nav-tab { padding: 8px 18px; font-size: 14px; color: #606266; text-decoration: none; border-radius: 4px; transition: all 0.2s; }
.nav-tab:hover { color: #409eff; background: #f5f7fa; }
.nav-tab.active { color: #409eff; font-weight: 600; border-bottom: 2px solid #409eff; border-radius: 0; }
.app-main { flex: 1; }
.app-footer { background: #fff; border-top: 1px solid #ebeef5; padding: 12px 0; font-size: 12px; color: #909399; margin-top: 32px; }
.footer-inner { max-width: 1200px; margin: 0 auto; padding: 0 32px; display: flex; justify-content: space-between; align-items: center; }
.status-ok { color: #67c23a; font-weight: 500; }
.footer-links { display: flex; gap: 24px; }
.footer-links a { color: #909399; text-decoration: none; }
.footer-links a:hover { color: #409eff; }
</style>