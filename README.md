[![testing](https://img.shields.io/badge/topic-testing-blue)]()
[![bug-hunting](https://img.shields.io/badge/topic-bug__hunting-red)]()
[![python](https://img.shields.io/badge/topic-python-green)]()



# 个人图书管理系统

测试练习项目 | 包含注入缺陷的图书管理系统 | FastAPI + SQLite 实现 | 适合 QA 培训使用

这是一个用于测试练习的个人图书管理系统项目。该项目故意注入了一些典型的 Bug，用于测试人员练习 Bug 发现和验证。

## 项目特点

- 基础功能完整：实现了图书的增删改查等基本功能
- 典型 Bug 注入：包含多个常见的问题场景
- 技术栈简单：使用主流但轻量级的技术组合
- 适合测试练习：Bug 类型多样，重现步骤清晰

## 功能特点

- 图书的增删改查
- 按书名和作者搜索
- 阅读状态管理
- 响应式界面设计

## 技术栈

- 后端：FastAPI (Python 3.10+)
- 数据库：SQLite
- 前端：Bootstrap 5 + Vanilla JS
- 模板引擎：Jinja2

## 项目结构

```
.
├── main.py          # FastAPI应用入口（包含数据库操作）
├── requirements.txt # 项目依赖
├── static/          # 静态资源
│   └── style.css    # 样式文件
└── templates/       # 模板文件
    ├── index.html   # 首页
    ├── add.html     # 添加页面
    └── edit.html    # 编辑页面
```

## 安装和运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动应用：
```bash
python main.py
```

3. 访问应用：
打开浏览器访问 http://localhost:8000

## 测试说明

本项目包含以下类型的 Bug 供测试练习：

1. 删除功能相关
   - 删除确认缺失

2. 数据验证相关
   - 日期验证缺失
   - 价格验证缺失
   - 字段长度验证缺失

3. 搜索功能相关
   - 搜索清空问题
   - 搜索匹配问题

4. 状态更新相关
   - 状态更新不刷新

5. 功能缺失相关
   - 空状态处理缺失

## 注意事项

- 本项目主要用于测试练习，不建议用于生产环境
- 所有 Bug 都是故意注入的，用于测试练习
- 项目代码中不会标注 Bug 的位置，需要测试人员自行发现

## 测试目标

1. 验证所有注入的 Bug 是否可重现
2. 练习 Bug 报告编写
3. 熟悉常见 Web 应用问题
4. 提高测试用例设计能力

---

注入的Bug清单可关注我的公众号：**秋草说测试**
![秋草说测试](https://github.com/user-attachments/assets/bf1177a9-5eeb-4079-a118-a22fe2e511dd)

欢迎大家提issue反馈更多发现更多Bug ^-^
