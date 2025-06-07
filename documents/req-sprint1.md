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
| plan_id      | INTEGER PK  | ✓    | 计划ID (主键)                |
| book_id      | INTEGER     | ✓    | 关联图书ID (外键)             |
| planner      | TEXT        | ✓    | 计划人姓名                    |
| description  | TEXT        | ✗    | 计划描述 (≤200字符)           |
| start_date   | DATE        | ✓    | 计划开始日期                  |
| end_date     | DATE        | ✗    | 计划结束日期                  |
| status       | TEXT        | ✓    | 状态: 未开始/进行中/已完成/已取消 |
| progress     | INTEGER     | ✗    | 进度百分比 (0-100)            |
| priority     | TEXT        | ✗    | 优先级: 高/中/低              |

#### 计划跟踪表 (plan_tasks)
| 字段         | 类型        | 必填 | 说明                          |
|--------------|-------------|------|-------------------------------|
| task_id      | INTEGER PK  | ✓    | 任务ID (主键)                |
| plan_id      | INTEGER     | ✓    | 关联计划ID (外键)             |
| start_time   | DATETIME    | ✗    | 任务开始时间                  |
| end_time     | DATETIME    | ✗    | 任务结束时间                  |
| description  | TEXT        | ✓    | 任务描述 (≤100字符)           |
| status       | TEXT        | ✓    | 状态: 未开始/进行中/已完成/已取消 |
| executor     | TEXT        | ✗    | 执行人姓名                    |

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

### 用户故事5：查看阅读计划日历  
**As a** 时间管理者  
**I want to** 按日历视图查看阅读计划  
**So that** 我能直观了解阅读时间安排  

**验收标准:**  
1. **日历视图展示**  
   - *Given* 用户进入"计划日历"页面  
   - *When* 选择某个月份  
   - *Then* 按日期显示当天计划的任务数量  
   
2. **日期详情查看**  
   - *Given* 用户点击日历中的某一天  
   - *When* 弹出详情窗口  
   - *Then* 显示当天所有任务的详细列表  

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
| 计划日历视图     | 按日历展示任务分布        | 全尺寸日历组件     |
| 任务管理弹窗     | 任务创建/编辑             | 模态框表单         |

### 3. 交互优化
1. 图书封面支持拖拽上传
2. 计划时间线可视化展示
3. 任务状态支持看板式拖拽管理

---

## 注入Bug清单（独立文档）

### 图书管理模块
1. 封面图片路径未做存在性校验（可输入无效路径）
2. 购买时间允许早于图书发行时间
3. 关联图书未防止循环引用（A关联B，B又关联A）

### 计划管理模块
1. 计划结束日期允许早于开始日期
2. 任务状态更新后计划进度不重新计算
3. 删除计划时未删除关联任务

### 界面交互
1. 日历视图中跨月任务显示不全
2. 任务看板拖拽后状态不保存
3. 封面预览图在暗黑模式下显示异常

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
3. 独立的BUG清单.md（包含12个注入缺陷）
4. 初始化脚本：创建带5本示例图书和3个阅读计划
5. API文档更新（OpenAPI格式）

> ⏱️ **迭代周期**：2周  
> 🔧 **技术重点**：前端日历组件集成、文件上传处理、状态联动逻辑  
> 🐞 **测试焦点**：状态转换验证、时间冲突检测、文件路径处理