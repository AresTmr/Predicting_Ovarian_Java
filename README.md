# Predicting Ovarian Java

卵巢储备评估与促排方案 AI 辅助系统

> Spring Boot 3.2 + Vue 3 + H2 + MyBatis-Plus + ONNX Runtime Java
> v2.2 / 2026-09-02

## 项目结构

```
Predicting_Ovarian_Java/
├── pom.xml                                  # Maven 单模块配置
├── README.md / 开发文档.md / 服务方案.md / 合规与边界.md
│
├── src/main/java/com/hospital/ovarian/
│   ├── OvarianApplication.java              # 主入口
│   ├── annotation/                          # 自定义注解
│   ├── config/                              # Spring 配置类
│   ├── controller/                          # REST Controller
│   ├── dao/                                 # MyBatis Mapper
│   ├── entity/                              # 实体
│   │   └── dto/                             # DTO
│   ├── exception/                           # 异常与全局处理
│   ├── inference/                           # ONNX 推理引擎
│   ├── interceptor/                         # 拦截器（病历号审计）
│   ├── service/                             # 业务服务
│   │   └── impl/
│   ├── task/                                # 定时任务
│   └── utils/                               # 工具类
│
├── src/main/resources/
│   ├── application.yml
│   ├── schema-h2.sql                        # H2 数据库初始化脚本
│   └── models/                              # ONNX 模型文件
│
└── frontend/                                # Vue 3 + Element Plus 前端
    └── src/views/PatientEntry.vue           # 患者录入主页面
```

## 快速启动

### 后端

```bash
cd Predicting_Ovarian_Java
mvn clean package -DskipTests
java -jar target/predicting-ovarian.jar
```

访问：
- 主应用：http://127.0.0.1:18501/
- Swagger UI：http://127.0.0.1:18501/swagger-ui.html
- H2 Console：http://127.0.0.1:18501/h2-console（JDBC URL: jdbc:h2:file:./data/predicting_ovarian）

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问：http://127.0.0.1:5173/（自动代理 /api 到后端 18501）

## 患者标识策略

- ✅ 仅入库**病历号（case_no）** = 原始 Excel 中的"总编号"
- ❌ 不存储姓名、身份证号、手机号、详细地址
- ✅ 病历号列表展示脱敏（`***5801`）
- ✅ 所有访问均写审计日志

详见 `合规与边界.md`。
