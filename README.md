# Kael CMDB & Webshell Gateway

Kael 是一个基于 Python Django (5.1) + Django REST Framework (DRF) + Django Channels (WebSocket) 开发的高性能 **CMDB（配置管理数据库）资产管理系统与 Kubernetes Webshell 网关**。

系统主要面向运维开发（DevOps）场景，提供：
1. **CMDB 资源同步与管理**：支持从外部 CMDB API 自动同步用户、业务线、产品线及应用服务数据，并提供完备的 REST APIs 及 Swagger 文档。
2. **Kubernetes Webshell 交互式终端**：基于 WebSocket 协议，直接代理并建立与 Kubernetes Pod 内容器的交互式 Shell 连接，支持 dynamic 终端窗口尺寸调整（Resize）与输入/输出流的双向实时传输。
3. **工单审批流引擎底层设计**：提供灵活的工单模板、动态表单及多级审批流的数据模型支持。

---

## 🛠️ 技术栈

* **核心框架**：Python >= 3.13, Django 5.1, Django REST Framework >= 3.17
* **异步与网络协议**：Django Channels 4.3 (ASGI 驱动，支持 WebSocket 双向通信)
* **数据库/缓存**：SQLite (db.sqlite3), Redis (支持哨兵模式 Sentinel)
* **K8s 集群对接**：Kubernetes Python Client (支持 Exec Stream 交互)
* **包管理器与运行时**：`uv` (高速 Python 依赖管理)
* **接口文档**：`drf-spectacular` (自动生成 OpenAPI 3.0 规范，提供 Swagger UI 和 ReDoc)

---

## 📂 项目目录结构

```text
Kael/
├── Kael/                   # 项目全局配置目录
│   ├── settings.py         # Django 核心配置文件（数据库、缓存、中间件、应用注册等）
│   ├── config.py           # 环境变量解析配置（dotenv 模式加载）
│   ├── urls.py             # 核心 HTTP API 路由入口
│   ├── asgi.py             # ASGI 异步路由入口 (HTTP + WebSocket 分流)
│   └── wsgi.py             # WSGI 同步服务入口
├── project/                # CMDB 项目与应用资产管理应用
│   ├── models.py           # 业务线 (Businesses)、产品线 (Products)、应用服务 (Application) 数据库模型
│   ├── views.py            # DRF ViewSets 控制器 (支持数据检索与 CRUD)
│   ├── serializers.py      # REST 序列化器设计 (区分读/写序列化逻辑)
│   ├── jobs.py             # CMDB 业务数据后台同步任务 (Sync Jobs)
│   └── urls.py             # 应用内 HTTP API 路由定义
├── users/                  # 用户管理与认证应用
│   ├── models.py           # 用户数据库模型 (UsersModel)
│   ├── views.py            # 用户信息检索与登录认证 API
│   ├── jobs.py             # 外部 CMDB 用户数据后台同步任务 (Sync Job)
│   └── urls.py             # 应用内用户 API 路由定义
├── webshell/               # Kubernetes 交互式 Webshell 核心应用
│   ├── views.py            # SSHConsumer 继承自 Channels WebsocketConsumer，处理 WebSocket 连接
│   ├── utils.py            # K8SApiTools (Kubernetes Client封装) 和 K8SStreamThread (I/O 双向流多线程处理)
│   └── routing.py          # WebSocket 路由定义 (/ws/shell/)
├── order/                  # 工单审批流底层设计应用
│   └── models.py           # 工单表单 (Form)、审批流模板 (Template) 及实例 (Instance/Approval/Status) 数据库模型
├── utils/                  # 共享工具库与基础基类
│   ├── common.py           # 抽象基类 (CommonFields) 包含通用创建、更新时间等审计字段
│   ├── sync.py             # CMDB 外部数据同步基类 (SyncBaseInfo) 支持分页抓取与 JWT Token 鉴权
│   ├── pagination.py       # 自定义 API 标准分页组件 (StandardPagination)
│   └── cache.py, tools.py  # 缓存懒加载与 UUID 标识符生成等辅助工具
├── pyproject.toml          # 项目属性与 uv 依赖配置文件
├── requirements.txt        # 兼容传统 pip 部署的依赖列表
├── uv.lock                 # 确定的依赖锁定版本文件
└── .env.example            # 项目环境变量配置模板
```

---

## 🏗️ 系统架构设计

```mermaid
graph TD
    User([终端用户/前端]) -->|HTTP REST| API_Gateway[Django HTTP Engine]
    User -->|WebSocket| WS_Gateway[Django Channels ASGI Engine]

    %% HTTP
    subgraph Django HTTP Web Service
        API_Gateway --> AuthView[users.AuthViewSet - 登录验证]
        API_Gateway --> UserView[users.UsersViewSet - 用户信息查询]
        API_Gateway --> ResourceView[project.ViewSet - 业务/产品/应用管理]
        API_Gateway --> DocView[drf-spectacular - OpenAPI/Swagger文档]
    end

    %% WebSocket / K8s Webshell
    subgraph Django Channels Webshell Gateway
        WS_Gateway -->|/ws/shell/| WS_Consumer[webshell.SSHConsumer]
        WS_Consumer -->|1. 获取Token/参数| Pod_Validation[校验 Pod 命名空间/容器名]
        WS_Consumer -->|2. 建立 Exec Stream| K8s_API[Kubernetes Python SDK]
        K8s_API -->|3. 映射 PTY 到 Websocket| Stream_Thread[webshell.K8SStreamThread]
    end

    %% Backend Storage & Services
    subgraph 数据与缓存存储
        AuthView & UserView & ResourceView & WS_Consumer -->|读写数据| SQLite[(SQLite Database)]
        AuthView & UserView & ResourceView -->|全局缓存/Session| Redis[(Redis / Sentinel 集群)]
    end

    %% Sync Jobs
    subgraph 后台数据同步组件 (Jobs)
        Sync_User[users.jobs.SyncUserInfo] -->|定时调用外部 API| CMDB_API[外部 CMDB 服务平台]
        Sync_Project[project.jobs.ProjectSyncData] -->|定时调用外部 API| CMDB_API
        Sync_User -->|同步更新用户信息| SQLite
        Sync_Project -->|同步更新业务线/应用元数据| SQLite
    end

    %% Kubernetes Node
    Stream_Thread <-->|双向 Shell I/O| K8s_Pod[Kubernetes Container Pod]
```

---

## 🚀 部署与运行指南

### 1. 克隆与环境配置

项目采用 `uv` 工具链管理。首先，请在项目根目录下根据模板创建你的 `.env` 配置文件：

```bash
cp .env.example .env
```

打开 `.env` 文件，完善你的配置信息：
* **Redis** 连接参数。
* **CMDB_DOMAIN** 与 **CMDB_TOKEN**（用以同步外部用户与应用元数据）。
* **K8S_HOST** 与相应的 **K8S_TOKEN**、**K8S_ADMIN_TOKEN**（用以调用 Kubernetes 凭证连接集群终端，支持 SSL 开关校验）。

### 2. 安装项目依赖

直接使用 `uv` 极速同步安装环境：

```bash
# 激活虚拟环境并安装所有依赖项
uv sync
```

若使用传统 `pip` 方式，可执行：
```bash
pip install -r requirements.txt
```

### 3. 初始化数据库

项目默认使用 SQLite3 进行本地资产存储，会自动在项目根目录下生成 `db.sqlite3` 数据库文件。无需配置 MySQL。

```bash
# 执行 Django 数据迁移以创建数据库表并初始化表结构
uv run python manage.py migrate
```

### 4. 运行后台同步任务

本地运行或配置 Crontab 定时运行 CMDB 后台数据同步任务，以拉取外部最新资源信息：

```bash
# 1. 同步并保存外部 CMDB 用户数据
uv run python users/jobs.py

# 2. 同步并保存外部 CMDB 业务线、产品线及应用数据
uv run python project/jobs.py
```

### 5. 启动开发服务器

通过 `ASGI` 模式运行服务，以便同时支持 HTTP 和 WebSocket 请求：

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

---

## 🔌 核心 API 与接口规约

### 1. API 接口文档 (Swagger / ReDoc)

服务运行后，可通过浏览器直接访问自动生成的交互式 API 文档页面：
* **Swagger UI 交互接口文档**: `http://127.0.0.1:8000/api/docs/`
* **Redoc 静态接口文档**: `http://127.0.0.1:8000/api/redoc/`
* **OpenAPI 3.0 Schema JSON**: `http://127.0.0.1:8000/api/schema/`

### 2. HTTP 关键路由列表

| 模块 | HTTP 方法 | API 路径 | 描述 |
| :--- | :--- | :--- | :--- |
| **认证管理** | `POST` | `/users/auth/login/` | 用户登录，验证用户名和密码 |
| **用户查询** | `GET` | `/users/users/` | 获取同步来的用户列表（支持模糊匹配查询） |
| **用户详情** | `GET` | `/users/users/<instance_id>/` | 根据 UUID 获取指定用户详情 |
| **业务线管理** | `GET`/`POST` | `/project/businesses/` | 获取/创建业务线 |
| **产品线管理** | `GET`/`POST` | `/project/products/` | 获取/创建产品线 |
| **应用管理** | `GET`/`POST` | `/project/applications/` | 获取/注册应用服务（关联语言/等级/容器类型/巡检状态等） |
| **应用更新** | `PUT`/`PATCH`/`DELETE` | `/project/applications/<instance_id>/` | 调整或下线应用服务 |

### 3. Webshell (WebSocket) 通信规约

客户端与 Kael 进行容器 WebShell 交互时，需使用以下协议参数：

* **连接地址**: `ws://<domain>:<port>/ws/shell/?namespace=<namespace>&pod_name=<pod_name>&container=<container>`
* **查询参数**:
  * `namespace` (选填): Kubernetes 命名空间，默认 `default`。
  * `pod_name` (必填): 目标 Pod 名称。
  * `container` (选填): 容器名称。若为空，默认与 Pod 名称一致。

#### 📥 客户端消息格式 (发送至服务端)
消息采用 JSON 字符串格式进行传递，格式如下：

* **命令输入 (stdin)**:
  ```json
  {
      "op": "stdin",
      "data": "ls -la\r"
  }
  ```
* **调整终端视口大小 (resize)**:
  ```json
  {
      "op": "resize",
      "data": {
          "rows": 40,
          "cols": 120
      }
  }
  ```

#### 📤 服务端消息格式 (发回客户端)
服务端向客户端发送的消息为**纯文本数据 (Plain Text)**，即直接将 K8s 容器控制台输出的二进制流解码为 UTF-8 字符串发送给客户端（包括 ANSI 终端颜色代码、退格等控制字符），前端配合 `xterm.js` 即可实现完美的交互式 Shell 体验。
