import { createRouter, createWebHistory } from "vue-router"
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/patient-entry" },
    { path: "/patient-entry", name: "PatientEntry", component: () => import("@/views/PatientEntry.vue"), meta: { title: "患者临床信息录入" } },
    { path: "/monitoring-result", name: "MonitoringResult", component: () => import("@/views/MonitoringResult.vue"), meta: { title: "动态监测与结果面板" } },
    { path: "/decision-curve", name: "DecisionCurve", component: () => import("@/views/DecisionCurve.vue"), meta: { title: "决策曲线" } },
    { path: "/recommendation", name: "Recommendation", component: () => import("@/views/Recommendation.vue"), meta: { title: "下一次 Gn 剂量与结局风险解释" } }
  ]
})
export default router
