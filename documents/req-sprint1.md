# 个人图书管理系统 - 迭代1 (Sprint1) 需求文档  
**版本**：v1.0.1  
**目标**：扩展图书管理功能，增加阅读计划管理模块  

---

## 核心功能扩展

### 1. 图书信息扩展
| 新增字段         | 类型        | 必填 | 说明                          |
|------------------|-------------|------|-------------------------------|
| 购买时间         | DATE        | ✗    | 用户购买图书的日期            |
| 图书封面         | TEXT        | ✗    | 封面图片存储路径              |
| 购买者           | TEXT        | ✗    | 图书购买人姓名                |

### 2. 在库状态扩展
```diff
+ 待购买
在库
借入
借出
归档
```

### 3. 新增阅读计划模块
#### 读书计划表 (reading_plans)
| 字段         | 类型        | 必填 | 说明                          |
|--------------|-------------|------|-------------------------------|
| id           | INTEGER PK  | ✓    | 计划ID (主键)                |
| book_id      | INTEGER     | ✓    | 关联图书ID (外键)             |
| planner      | TEXT        | ✓    | 计划人姓名                    |
| description  | TEXT        | ✗    | 计划描述                      |
| start_date   | TEXT        | ✓    | 计划开始日期                  |
| end_date     | TEXT        | ✗    | 计划结束日期                  |
| status       | TEXT        | ✓    | 状态: 进行中/已完成/已取消    |
| progress     | INTEGER     | ✗    | 进度百分比 (0-100)            |
| priority     | TEXT        | ✗    | 优先级: 高/中/低              |
| created_at   | TIMESTAMP   | ✓    | 创建时间                      |
| updated_at   | TIMESTAMP   | ✓    | 更新时间                      |

#### 任务表 (tasks)
| 字段         | 类型        | 必填 | 说明                          |
|--------------|-------------|------|-------------------------------|
| id           | INTEGER PK  | ✓    | 任务ID (主键)                |
| plan_id      | INTEGER     | ✓    | 关联计划ID (外键)             |
| title        | TEXT        | ✓    | 任务标题                      |
| description  | TEXT        | ✗    | 任务描述                      |
| due_date     | TEXT        | ✗    | 任务截止日期                  |
| status       | TEXT        | ✓    | 任务状态                      |
| priority     | TEXT        | ✗    | 任务优先级                    |
| created_at   | TIMESTAMP   | ✓    | 创建时间                      |
| updated_at   | TIMESTAMP   | ✓    | 更新时间                      |

---

## 用户故事

### 用户故事1：扩展图书信息管理  
**As a** 图书收藏者  
**I want to** 记录图书的购买信息和封面数据  
**So that** 我能全面管理图书资产  

**验收标准:**  
1. **新增字段展示**  
   - *Given* 用户查看图书详情页  
   - *When* 页面加载完成  
   - *Then* 显示购买时间、购买者、封面预览  
   
2. **封面预览功能**  
   - *Given* 图书封面路径有效  
   - *When* 用户查看图书详情  
   - *Then* 显示封面缩略图（200×300px）  

### 用户故事2：管理待购买状态  
**As a** 图书收藏者  
**I want to** 标记图书为"待购买"状态  
**So that** 我能区分已购和计划购买的书籍  

**验收标准:**  
1. **状态筛选功能**  
   - *Given* 用户进入图书列表页  
   - *When* 选择"待购买"筛选条件  
   - *Then* 仅显示状态为"待购买"的图书  
   
2. **状态转换限制**  
   - *Given* 图书状态为"待购买"  
   - *When* 用户尝试借出该书  
   - *Then* 显示错误提示"待购买图书不可借出"  

### 用户故事3：创建读书计划  
**As a** 图书爱好者  
**I want to** 为图书创建阅读计划  
**So that** 我能合理安排阅读时间  

**验收标准:**  
1. **计划创建流程**  
   - *Given* 用户进入"读书计划"页面  
   - *When* 填写必填字段（图书、计划人、开始日期）并提交  
   - *Then* 系统创建计划并显示在计划列表  
   
2. **进度自动计算**  
   - *Given* 计划包含3个任务  
   - *When* 完成2个任务  
   - *Then* 计划进度自动更新为66%  

### 用户故事4：管理计划任务  
**As a** 阅读计划执行者  
**I want to** 分解计划为可执行任务  
**So that** 我能分步完成阅读目标  

**验收标准:**  
1. **任务添加功能**  
   - *Given* 用户选择某个读书计划  
   - *When* 添加新任务并设置执行人  
   - *Then* 任务显示在计划详情页的任务列表中  
   
2. **任务状态联动**  
   - *Given* 计划包含多个任务  
   - *When* 所有任务标记为"已完成"  
   - *Then* 计划状态自动更新为"已完成"  

### 用户故事5：首页概览展示
**As a** 系统使用者
**I want to** 在首页看到关键数据概览
**So that** 我能快速了解整体情况

**验收标准:**
1. **图书统计展示**
   - *Given* 用户进入首页
   - *When* 页面加载完成
   - *Then* 显示图书总数、在库数、借出数统计卡片
     * 点击卡片可跳转到对应图书列表
     * 数据实时更新

2. **计划进度概览**
   - *Given* 用户进入首页
   - *When* 页面加载完成
   - *Then* 显示计划总数、进行中计划数、已完成计划数
     * 显示整体完成率百分比环状图
     * 支持点击查看详情

3. **最近活动记录**
   - *Given* 用户进入首页
   - *When* 页面加载完成
   - *Then* 显示最近5条图书借阅/归还记录
     * 包含图书封面缩略图、操作类型和时间
     * 点击可跳转到对应图书详情

**技术实现要求:**
1. 使用Chart.js实现数据可视化
2. 通过WebSocket实现数据实时更新
3. 响应式布局适配不同设备

### 用户故事6：阅读统计与分析
**As a** 数据分析者
**I want to** 查看详细的阅读统计数据
**So that** 我能分析阅读习惯和效率

**验收标准:**
1. **月度阅读统计**
   - *Given* 用户进入统计页面
   - *When* 选择月份范围
   - *Then* 显示该时段内的阅读量折线图
     * 可按图书分类筛选
     * 显示平均阅读时长

2. **计划完成分析**
   - *Given* 用户进入统计页面
   - *When* 选择时间范围
   - *Then* 显示计划完成率柱状图
     * 区分不同优先级计划
     * 显示超期未完成计划数

3. **阅读习惯分析**
   - *Given* 用户进入统计页面
   - *When* 查看"阅读时段"标签
   - *Then* 显示24小时阅读热力图
     * 标识高频阅读时段
     * 显示各时段平均阅读时长

**技术实现要求:**
1. 使用ECharts实现复杂图表
2. 支持数据导出为CSV
3. 后端提供聚合查询接口
4. 移动端简化视图

---

## 前端修改需求

### 1. 图书管理页面
```diff
+ 添加页面：图书详情页
+ 添加字段：
   - 购买时间 (日期选择器)
   - 封面图片 (文件上传+预览)
   - 购买者 (文本输入)
+ 在库状态：增加"待购买"选项
```

### 2. 新增模块页面
| 页面             | 功能                      | 组件                |
|------------------|---------------------------|---------------------|
| 读书计划列表     | 计划CRUD + 状态筛选       | 表格+筛选栏        |
| 计划详情页       | 计划信息+任务管理         | 表单+任务卡片      |
| 任务管理弹窗     | 任务创建/编辑             | 模态框表单         |

### 3. 交互优化
1. 图书封面支持拖拽上传
2. 计划时间线可视化展示
3. 任务状态支持看板式拖拽管理

---


## 技术实现说明

### 后端API扩展
```python
# 图书API新增字段
class BookUpdate(BaseModel):
    purchase_date: Optional[date] = None
    cover_image: Optional[str] = None
    purchaser: Optional[str] = None
```

### 数据库变更
```sql
-- 图书表新增字段
ALTER TABLE books ADD COLUMN purchase_date DATE;
ALTER TABLE books ADD COLUMN cover_image TEXT;
ALTER TABLE books ADD COLUMN purchaser TEXT;

-- 创建新表
CREATE TABLE reading_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(book_id),
    planner TEXT NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    status TEXT NOT NULL CHECK(status IN ('未开始','进行中','已完成','已取消')),
    progress INTEGER CHECK(progress BETWEEN 0 AND 100),
    priority TEXT CHECK(priority IN ('高','中','低'))
);

CREATE TABLE plan_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL REFERENCES reading_plans(plan_id),
    start_time DATETIME,
    end_time DATETIME,
    description TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('未开始','进行中','已完成','已取消')),
    executor TEXT
);
```

### 前端组件库
```javascript
// 新增日历组件
import FullCalendar from '@fullcalendar/react';

// 任务看板组件
import { DragDropContext } from 'react-beautiful-dnd';

// 文件上传组件
import { FileUploader } from "react-drag-drop-files";
```

---

## 交付物要求
1. 完整可运行代码（含数据库迁移脚本）
2. 前端新增4个页面组件
3. 初始化脚本：创建带5本示例图书和3个阅读计划
4. API文档更新（OpenAPI格式）

> ⏱️ **迭代周期**：2周  
> 🔧 **技术重点**：文件上传处理、状态联动逻辑  
> 🐞 **测试焦点**：状态转换验证、时间冲突检测、文件路径处理
