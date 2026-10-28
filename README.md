# Predicting Ovarian Java

面向生殖医学临床辅助场景的卵巢储备评估与促排卵辅助决策系统。本项目将原有 Python/Streamlit 原型迁移为 Java 后端与 Vue 前端分离的院内单机应用，用于验证患者数据录入、模型推理、动态监测、决策曲线和个体化解释的完整流程。

> 当前版本：2.2.0
> 当前技术栈：Spring Boot 2.3.7、JDK 8、MyBatis-Plus、H2、Vue 3、Element Plus、Vite、Python 3.11 模型运行时

## 一、项目背景

医院现有原型系统验证了卵巢储备、促排卵剂量和结局风险相关模型的可行性，但原实现不适合直接作为 Java 院内系统交付。本项目的主要目标包括：

- 保留原项目的核心模型输入、输出和三个结果页面展示逻辑。
- 将业务接口、数据持久化和前端展示迁移到 Java Web 技术栈。
- 支持医院内网本地运行，不依赖外部云端模型服务。
- 将模型推理与 Java 业务、Vue 展示解耦，便于后续替换模型。
- 在模型不可用时明确返回服务不可用，不生成 mock 临床结果。

系统输出仅用于临床辅助参考，最终诊疗和用药决策应由执业医师结合患者实际情况作出。

## 二、项目现状

### 已实现功能

- 患者基础信息、病历号、监测记录和用药记录录入。
- 按病历号一键载入患者信息及最近周期的监测记录。
- 患者录入数据在当前浏览器标签页内保留，刷新后可继续生成结果。
- 统一分析接口生成一次 `runId`，三个结果页面共享同一份模型结果。
- 动态监测与结果面板。
- FSH、LH、HMG 候选剂量决策曲线。
- 预测获卵数、MII 和中重度 OHSS 风险展示。
- Gn 剂量与结局风险的个体化贡献解释。
- KNN 相似历史病例支持信息展示。
- H2 文件数据库保存分析请求、结果和运行状态。
- 模型服务健康检查与 Java 后端健康检查。

### 当前技术状态

| 项目 | 当前实现 |
|---|---|
| 后端 | Spring Boot 2.3.7，JDK 8 |
| ORM | MyBatis-Plus 3.4.3.2，部分分析运行记录使用 JdbcTemplate |
| 数据库 | H2 文件数据库 |
| 前端 | Vue 3 + Element Plus + ECharts + Pinia |
| 模型服务 | 本地 Python HTTP 服务 |
| Java 到模型服务 | HTTP JSON 调用 `/analyze` |
| 模型失败策略 | 返回 HTTP 503，不使用 mock 临床结果 |
| 部署形态 | Windows 单机本地运行 |

### 当前边界

- 当前使用 H2，尚未切换至 MySQL 8.0。
- 尚未接入医院门诊、电子病历、LIS 等院内系统接口。
- 模型服务和 Java 后端默认仅监听本机地址，适用于当前单机验证阶段。
- ONNX 推理目前只有接口预留，尚未完成可直接交付的 Java ONNX 推理实现。
- 尚未完成医院正式环境所需的统一认证、集中审计、容灾和生产级安全加固。

## 三、项目结构

```text
Predicting_Ovarian_Java/
├── pom.xml
├── README.md
├── start-all.ps1                    # 一键启动模型、后端和前端
├── stop-all.ps1                     # 停止三个服务
├── data/
│   └── patient_import.csv           # 一键填入功能使用的数据文件
├── src/main/java/com/hospital/ovarian/
│   ├── controller/                  # REST 接口
│   ├── service/                     # 分析运行和业务服务
│   ├── inference/                   # 模型运行器抽象
│   ├── model/                       # 模型配置
│   ├── entity/dto/                  # 请求与响应 DTO
│   └── config/                      # 数据库初始化等配置
├── src/main/resources/
│   ├── application.yml
│   └── schema.sql
├── frontend/                        # Vue 3 前端
└── model-runtime/                   # Python 模型服务与模型资产
```

## 四、环境要求

当前项目在 Windows 环境下验证，主要依赖如下：

- JDK 8
- Maven 3.8+
- Node.js 18+ 与 npm
- Python 3.11
- PowerShell 5.1+

首次从 Git 获取项目后，需要安装前端依赖、创建 Python 虚拟环境，并重新构建 Java JAR。

## 五、启动方式

### 1. 安装前端依赖

```powershell
cd frontend
npm ci
cd ..
```

### 2. 创建模型运行环境

```powershell
python -m venv model-runtime\.venv
.\model-runtime\.venv\Scripts\python.exe -m pip install `
  torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
.\model-runtime\.venv\Scripts\python.exe -m pip install `
  -r model-runtime\requirements.txt
```

### 3. 构建 Java 后端

```powershell
$env:JAVA_HOME = "D:\Java\JDK"
mvn clean package
```

`JAVA_HOME` 需替换为本机 JDK 8 的实际路径。

### 4. 一键启动

```powershell
.\start-all.ps1 -JavaHome $env:JAVA_HOME
```

默认启动以下服务：

| 服务 | 地址 |
|---|---|
| Vue 前端 | http://127.0.0.1:5173 |
| Java 后端 | http://127.0.0.1:18502 |
| Python 模型服务 | http://127.0.0.1:8001 |

停止全部服务：

```powershell
.\stop-all.ps1
```

### 5. 手动启动

模型服务：

```powershell
.\model-runtime\run-service.ps1
```

Java 后端：

```powershell
$env:JAVA_HOME = "D:\Java\JDK"
java -jar target\predicting-ovarian.jar
```

前端：

```powershell
cd frontend
npm run dev
```

### 6. 运行验证

```powershell
.\model-runtime\run-day5.ps1
```

后端健康检查：

```text
GET http://127.0.0.1:18502/api/v1/recommendation-runs/runtime/health
```

模型服务健康检查：

```text
GET http://127.0.0.1:8001/health
```

## 六、核心接口

```text
POST /api/v1/recommendation-runs
GET  /api/v1/recommendation-runs/{runId}
GET  /api/v1/recommendation-runs/runtime/health
```

一次成功请求会创建一个 `runId`，并将请求、结果和运行状态保存到 H2 表 `analysis_run`。监测结果、决策曲线和推荐解释页面共用该结果。

模型服务内部接口：

```text
GET  /health
GET  /models
POST /analyze
```

## 七、数据和患者标识

- H2 数据文件默认位于 `data/ovarian.mv.db`，该文件不应提交到 Git。
- 一键填入数据位于 `data/patient_import.csv`。
- 仅使用病历号作为业务查询标识，不保存姓名、身份证号、手机号和详细地址。
- 列表展示使用脱敏病历号，完整病历号仅用于授权业务查询。
- 分析运行会保存必要的请求与结果数据，用于追溯和结果复用。

## 八、模型更换说明

### 当前调用关系

```text
Vue 前端
   ↓ HTTP
Java 后端 /api/v1/recommendation-runs
   ↓ POST /analyze
Python 模型服务 model-runtime/service.py
   ↓
模型资产与预处理参数
```

Java 后端地址由 `src/main/resources/application.yml` 中的 `model.rpc-url` 配置，默认值为：

```yaml
model:
  rpc-url: http://127.0.0.1:8001
```

### 推荐方式：保持同一契约替换模型包

模型替换后，只要输入字段、单位、任务语义、类别含义和输出结构保持不变，Java 与 Vue 代码无需修改。

当前主要模型资产：

```text
model-runtime/assets/models/dose/{fsh,lh,hmg}.pt
model-runtime/assets/preprocessing/{fsh,lh,hmg}.json
model-runtime/assets/models/dose-calibration/{fsh,lh,hmg}_temperature.json
model-runtime/assets/models/candidate/efficacy/bundle.joblib
model-runtime/assets/models/candidate/safety/bundle.joblib
model-runtime/assets/knn/
```

输入字段及单位定义见：

```text
model-runtime/assets/preprocessing/feature-contract.json
```

模型版本与来源记录见：

```text
model-runtime/manifest/day1-models.json
```

替换步骤：

1. 备份现有 `model-runtime/assets` 和模型清单。
2. 替换同任务、同输入输出契约的模型文件及对应预处理参数。
3. 更新模型清单中的版本、来源、SHA-256 和任务说明。
4. 如 KNN 解释数据依赖旧模型，同步更新 `model-runtime/assets/knn/`。
5. 重启 Python 模型服务。
6. 执行 `.\model-runtime\run-day5.ps1`，核对代表病例、低储备病例和高反应病例结果。
7. 通过前端三个结果页面确认汇总值、曲线、候选方案、个体化解释和 KNN 展示均正常。

必须保持的契约：

- `/analyze` 请求仍包含 `patient` 对象和 `records` 数组。
- 输入字段名称、单位和缺失值语义不变。
- FSH、LH、HMG 的剂量类别含义不变。
- 获卵数、MII、OHSS 风险的概率或数值语义不变。
- 响应中的 `summary`、`candidates`、`curves`、`explanations` 和 `warnings` 结构不变。
- 模型失败必须返回错误，不得返回 mock 临床结果。

### 替换为其他运行时

如需将 Python 服务替换为其他 HTTP 服务，只要继续实现 `/health`、`/models` 和 `/analyze` 三个接口并保持响应契约，Java 和 Vue 无需修改。

如需改用 ONNX，可选择：

- 保留 Python 服务作为统一模型网关，由 Python 加载 ONNX。
- 实现 Java ONNX 推理适配层，但继续对外提供统一的 Java 分析接口和前端结果结构。

当前 `OnnxModelRunner` 仅为预留桩实现，不能作为可交付的 ONNX 推理后端直接启用。

更详细的模型运行说明见 `model-runtime/README.md`。
