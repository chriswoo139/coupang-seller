# Coupang 选品研究工具

这是一个面向韩国 Coupang 平台的选品研究工具，聚焦女性内衣、内衣配件、洗护配件等类目。当前版本已经同时支持：

- 本地 Streamlit 工作台
- 本地 FastAPI 数据接口
- React + Vite 中文前端控制台
- Vercel 预览部署，便于在外网访问

## 当前能力

- 手动录入竞品
- 上传 CSV / Excel
- 从页面文本中提取结构化字段
- 价格分析、竞争分析、机会分析
- 1 / 2 / 3 / 6 件装利润测算
- 产品机会评分
- 生成韩语标题、关键词、详情页结构建议
- 导出 Excel / CSV / Markdown 报告
- 为自有店铺预留 Coupang Open API 接入层

## 合规边界

- 不绕过登录限制
- 不抓取需要登录权限的数据
- 不破解反爬机制
- 不采集个人信息
- Coupang Open API 仅用于你自己的店铺商品、类目、同步和上架流程

## 本地运行

安装依赖：

```bash
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

启动 Streamlit：

```bash
streamlit run app.py
```

启动本地 API：

```bash
uvicorn backend_api:app --reload --port 8010
```

启动 React 前端：

```bash
cd frontend
npm run dev
```

## 公网部署

项目已经补齐 Vercel 部署结构：

- 前端会构建到 `frontend/dist`
- 云端接口走 `api/index.py` 和 `api/[...path].py`
- 线上前端会自动请求同域 `/api`

如果直接用 Vercel 预览部署脚本，部署后可以得到一个外网访问链接。

## 数据存储说明

- 本地运行时使用 `data/competitors.db`
- 如果设置了 `DATABASE_PATH`，会优先使用自定义数据库路径
- 在 Vercel 这类无状态环境中，数据库会退回到临时可写目录 `/tmp/competitors.db`

这意味着：

- 线上版本适合演示、查看样例数据、远程打开和测试流程
- 如果要长期稳定保存远程录入数据，下一步建议接入云数据库，例如 Supabase / Neon / PostgreSQL

## 目录结构

```text
coupang_product_research_tool/
  app.py
  backend_api.py
  package.json
  vercel.json
  requirements.txt
  README.md
  data/
  modules/
  pages/
  api/
  frontend/
```

## 说明

- 首次运行时，如果数据库为空，会自动导入 `data/sample_competitors.csv`
- 本地 API 默认端口是 `8010`
- React 前端开发模式默认连接 `http://127.0.0.1:8010`
- 生产部署时 React 会自动切换到同域 `/api`
