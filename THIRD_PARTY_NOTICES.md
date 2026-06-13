# Third Party Notices

本项目新的桌面端前端部分 UI、样式、布局或组件实现参考 / 改写自：

1. Achilng/floral-notepaper
   - GitHub: https://github.com/Achilng/floral-notepaper
   - License: MIT
   - 改写来源：
     - `src/App.css` -> `frontend/desktop/src/styles/theme.css`、`frontend/desktop/src/styles/paper.css`
       - 改写内容：纸张色板、柔和阴影、噪声纹理、纸张编辑区、便签卡片、Markdown 预览区域。
     - `src/App.tsx` -> `frontend/desktop/src/App.tsx`、`frontend/desktop/src/layout/AppShell.tsx`
       - 改写内容：桌面应用壳层、全局错误隔离和主内容区组织方式。
     - `src/components/BackgroundLayer.tsx` -> `frontend/desktop/src/styles/globals.css`
       - 改写内容：背景层的柔和叠加思路，改为纯 CSS 的低饱和背景和纸张噪声。

2. Cang-yun/Mnemo
   - GitHub: https://github.com/Cang-yun/Mnemo
   - License: MIT
   - 改写来源：
     - `electron/main.ts`、`electron/preload.cts` -> `frontend/desktop/electron/main.ts`、`frontend/desktop/electron/preload.ts`
       - 改写内容：BrowserWindow 可调整大小、最大化、隐藏标题栏、窗口控制 IPC。
     - `src/ui/ErrorBoundary.tsx` -> `frontend/desktop/src/components/ui/ErrorBoundary.tsx`
       - 改写内容：React 错误边界结构，改成本项目的错误卡片样式。
     - `src/ui/TodayOverview.tsx` -> `frontend/desktop/src/pages/SchedulePage.tsx`
       - 改写内容：今日任务分区、筛选按钮、任务状态和复习反馈区域。
     - `src/ui/MonthPage.tsx` -> `frontend/desktop/src/components/schedule/CalendarSkeleton.tsx`
       - 改写内容：月历标题、月份控制、星期标题、日期格子结构。
     - `src/styles/global.css` -> `frontend/desktop/src/styles/paper.css`
       - 改写内容：日程页三栏布局、今日任务列表、月历网格、状态标签和桌面端滚动容器。

本轮没有整文件复制上述项目源码；以上目标文件为针对本项目后端接口、主功能和 Windows 本地桌面端重新实现后的改写版本。
