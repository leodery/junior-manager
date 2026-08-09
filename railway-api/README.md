# WorkBuddy API

Railway + PostgreSQL 后端服务

## 部署

1. Railway → New Project → Deploy from GitHub → 选 junior-manager
2. Root Directory 设为 `railway-api`
3. Add PostgreSQL 数据库
4. 添加变量 `ALLOWED_ORIGIN=https://leodery.github.io`
5. Deploy

## API

- `GET /health` — 健康检查
- `GET /api/data/:familyId/:appName` — 读取数据
- `PUT /api/data/:familyId/:appName` — 保存数据
- `DELETE /api/data/:familyId/:appName` — 删除数据
