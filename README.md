[![testing](https://img.shields.io/badge/topic-testing-blue)]()
[![bug-hunting](https://img.shields.io/badge/topic-bug__hunting-red)]()
[![python](https://img.shields.io/badge/topic-python-green)]()



# 个人图书管理系统

## 项目简介

这是一个用于测试练习的个人图书管理系统项目。该项目故意注入了一些典型的 Bug，用于测试人员练习 Bug 发现和验证。当前版本（Sprint 1）实现了图书管理的基本功能，包括图书信息的增删改查、封面图片上传、购买时间记录等，以及阅读计划的管理功能。

## 当前版本功能

- **图书管理**：支持添加、编辑、删除和查询图书信息，包括书名、作者、出版日期、购买时间、封面图片等。
- **阅读计划**：支持创建和管理阅读计划，包括计划名称、描述、开始日期、结束日期、进度等。
- **数据存储**：使用 SQLite 数据库存储图书和计划信息，数据库文件位于 `data/bookshelf.db`。
- **示例数据**：提供示例数据初始化工具，方便测试和演示。

## 技术栈

- **后端**：FastAPI (Python 3.10+)
- **数据库**：SQLite
- **前端**：Bootstrap 5 + Vanilla JS
- **模板引擎**：Jinja2

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

## 部署说明

### 环境要求

- Python 3.8 或更高版本
- 依赖包：见 `requirements.txt`

### 安装步骤

1. 克隆项目到本地：
   ```bash
   git clone <项目仓库地址>
   cd <项目目录>
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 初始化数据库（可选，仅用于测试）：
   ```bash
   python scripts/init_sample_data.py
   ```

4. 启动应用：
   ```bash
   python run.py
   ```

5. 访问应用：
   打开浏览器，访问 `http://localhost:8000`。

## 注意事项

- **测试版本**：当前版本主要用于测试目的，包含一些已知的 bug，这些 bug 是故意注入的，用于测试系统的容错性和健壮性。
- **数据安全**：请勿在生产环境中使用此版本，建议仅用于开发和测试。

## 联系方式

如有问题或建议，请联系项目维护者 