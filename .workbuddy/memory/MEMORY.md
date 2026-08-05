# 项目长期记忆

## 用户画像
- 准大一新生，专业：经济学
- 家庭结构：夫妻 + 2 个孩子
- 沟通风格：简洁，常以"可以"等简短确认推进，期待 AI 自主衔接下一步，不需反复确认
- 使用场景：跟 AI 助手协作做 PPT + 做网站 + 学 Python，云端跑代码不算本地算力
- 笔记本：ThinkPad T14 Gen3 AMD 版 (R7-6850U)，计划自己加内存到 32GB

## 项目1：家庭理财工作台（CloudBase 版）
- 原版：本地 HTML + Supabase，因国内访问慢 + 邮箱验证收不到而迁移
- 改造为腾讯云 CloudBase（匿名登录 + 邀请码加入家庭）
- CloudBase 环境 ID：leoderyyang-d9gc0pfwpbdac9915
- 部署 URL：https://leoderyyang-d9gc0pfwpbdac9915-1462506307.tcloudbaseapp.com/家庭理财工作台.html
- SDK：cloudbase.full.js 本地内联（旧 CDN imgcache.qq.com 已 404，新地址 static.cloudbase.net）
- 已完成：PWA 标签、移动端 CSS 全适配、底部导航条、微信 X5 内核适配、浏览器引导提示
- 单文件版 index.html：约 1MB（SDK 内联 + 移动端优化 + PWA）
- 文件位置：cloudbase-family-finance/index.html

## 项目2：蒙特卡洛期权定价演示
- 用途：测试 WorkBuddy 高负载代码能力 + 经济学教学
- 5000 万条路径 MC 模拟 + BS 解析解对比 + 希腊字母计算
- Python 3.13 venv + numpy/scipy/matplotlib
- 20 核 CPU，5000 万路径 4.45 秒，速率 11.24M/s，误差 0.000155
- 文件：monte-carlo-demo/mc_option_pricing.py + convergence.png

## 待办
- 家庭理财工作台：用户需确认是否已上传 index.html 到 CloudBase 静态托管
- 家庭理财工作台：确认匿名登录已开启 + 3 个数据库集合已创建
- 生成家人扫码二维码 + 微信群发文案（等用户确认新版登录面板正常后）
