import { createRouter, createWebHistory } from ''vue-router''

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: ''/'',
      redirect: ''/patient-entry''
    },
    {
      path: ''/patient-entry'',
      name: ''PatientEntry'',
      component: () => import(''@/views/PatientEntry.vue''),
      meta: { title: ''患者临床信息录入'' }
    }
  ]
})

export default router
