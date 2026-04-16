# Auto Clips Frontend

基于 React + TypeScript + Vite + Ant Design 的视频自动切片前端应用。

## 功能特性

### 🎯 核心功能
- **视频上传**: 支持拖拽上传视频文件和字幕文件
- **智能处理**: AI 自动提取视频精彩片段
- **片段管理**: 查看、编辑、下载视频片段
- **合集创建**: AI 推荐合集 + 手动创建合集
- **实时监控**: 处理进度实时反馈

### 🎨 用户界面
- **现代化设计**: 基于 Ant Design 组件库
- **响应式布局**: 支持桌面和移动端
- **直观操作**: 拖拽排序、一键下载
- **状态反馈**: 清晰的处理状态和进度显示

## 技术栈

- **前端框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 组件**: Ant Design
- **状态管理**: Zustand
- **路由**: React Router DOM
- **HTTP 客户端**: Axios
- **拖拽功能**: React Beautiful DnD
- **视频播放**: React Player
- **文件上传**: React Dropzone

## 快速开始

### 环境要求
- Node.js >= 16
- npm 或 yarn

### 安装依赖
```bash
npm install
# 或
yarn install
```

### 启动开发服务器
```bash
npm run dev
# 或
yarn dev
```

访问 http://localhost:3000

### 构建生产版本
```bash
npm run build
# 或
yarn build
```

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 可复用组件
│   │   ├── Header.tsx      # 页面头部
│   │   ├── FileUpload.tsx  # 文件上传组件
│   │   ├── ProjectCard.tsx # 项目卡片
│   │   ├── ClipCard.tsx    # 视频片段卡片
│   │   └── CollectionCard.tsx # 合集卡片
│   ├── pages/              # 页面组件
│   │   ├── HomePage.tsx    # 项目首页
│   │   └── ProjectDetailPage.tsx # 项目详情页
│   ├── services/           # API 服务
│   │   └── api.ts          # API 接口定义
│   ├── store/              # 状态管理
│   │   └── useProjectStore.ts # 项目状态
│   ├── App.tsx             # 应用主组件
│   ├── main.tsx            # 应用入口
│   └── index.css           # 全局样式
├── package.json
├── vite.config.ts          # Vite 配置
├── tsconfig.json           # TypeScript 配置
└── README.md
```

## 页面说明

### 项目首页 (`/`)
- 项目列表展示
- 搜索和筛选功能
- 新建项目（文件上传）
- 项目状态监控

### 项目详情页 (`/project/:id`)
- 项目信息和处理状态
- 视频片段管理
- AI 合集展示
- 手动创建合集
- 下载和导出功能

## 组件说明

### FileUpload
- 支持拖拽和点击上传
- 文件类型验证
- 上传进度显示
- 自动创建项目

### ProjectCard
- 项目信息展示
- 状态指示器
- 快捷操作按钮
- 进度条显示

### ClipCard
- 视频片段信息
- 在线预览功能
- 编辑和下载
- 添加到合集

### CollectionCard
- 合集信息展示
- 片段列表管理
- 拖拽排序
- 生成合集视频

## API 接口

前端通过 `/api` 代理与后端通信，主要接口包括：

- `GET /api/projects` - 获取项目列表
- `POST /api/projects` - 创建新项目
- `GET /api/projects/:id` - 获取项目详情
- `POST /api/projects/:id/upload` - 上传文件
- `POST /api/projects/:id/process` - 开始处理
- `GET /api/projects/:id/status` - 获取处理状态
- `PUT /api/projects/:id/clips/:clipId` - 更新片段
- `PUT /api/projects/:id/collections/:collectionId` - 更新合集
- `GET /api/projects/:id/download` - 下载视频

## 开发说明

### 状态管理
使用 Zustand 进行轻量级状态管理，主要管理：
- 项目列表和当前项目
- 视频片段和合集数据
- 加载状态和错误信息

### 样式规范
- 使用 Ant Design 主题色彩
- 响应式设计，支持移动端
- 统一的间距和圆角规范
- 自定义滚动条和悬停效果

### 类型定义
所有数据结构都有完整的 TypeScript 类型定义，确保类型安全。

## 部署说明

### 开发环境
```bash
npm run dev
```

### 生产环境
```bash
npm run build
npm run preview
```

### Docker 部署
```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 后续优化

### 功能增强
- [ ] 视频在线编辑
- [ ] 批量操作
- [ ] 导出多种格式
- [ ] 用户权限管理
- [ ] 云端存储集成

### 性能优化
- [ ] 虚拟滚动
- [ ] 图片懒加载
- [ ] 代码分割
- [ ] 缓存策略

### 用户体验
- [ ] 快捷键支持
- [ ] 主题切换
- [ ] 国际化
- [ ] 无障碍访问

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License