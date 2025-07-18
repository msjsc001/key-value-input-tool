[![GitHub release (latest by date)](https://img.shields.io/github/v/release/msjsc001/key-value-input-tool)](https://github.com/msjsc001/key-value-input-tool/releases/latest) [![GitHub last commit](https://img.shields.io/github/last-commit/msjsc001/key-value-input-tool)](https://github.com/msjsc001/key-value-input-tool/commits/master) [![GitHub All Releases Downloads](https://img.shields.io/github/downloads/msjsc001/key-value-input-tool/total?label=Downloads&color=brightgreen)](https://github.com/msjsc001/key-value-input-tool/releases)
# QuickKV - 你的智能键值对快速输入与管理大师

![QuickKV Logo](https://img.icons8.com/fluency/96/keyboard.png)

**QuickKV** 是一款专为追求极致效率的用户设计的桌面应用程序。它允许您预先定义和管理大量的“键-值”数据对，并通过一个高度智能化的界面，实现闪电般的快速输入、组合和复制。无论您是程序员、文案工作者、客服人员还是数据分析师，QuickKV 都能成为您工作流中不可或缺的效率倍增器。

---

## ✨ 核心特性

*   **智能联想输入**: 为您的“键”和“值”提供实时、高效的输入联想。
*   **多值组合**: 支持一个“键”关联多个“值”，并自定义分隔符，一键生成复杂文本。
*   **强大的列表管理**: 在“数据管理”中心，通过直观的拖拽操作，对您的数据进行**手动排序**，或随时切换为**字母排序**。
*   **组合快照 (Layouts)**: 保存和加载不同的界面布局，为您在不同工作场景（如“写代码”、“回邮件”）之间提供一键切换的便利。
*   **状态记忆**: 自动保存您的窗口大小、位置、历史输入和界面布局，让每次打开都像从未离开。
*   **健壮的数据持久化**: 所有核心数据存储在单一、可移植的 `quick_kv.db` (SQLite) 文件中，并通过版本控制确保未来升级的安全性。
*   **导入/导出**: 支持通过简单的 Markdown 文件进行批量数据导入和备份，打通与外部编辑器的数据链路。

---

## 🚀 面向用户：快速上手指南

### 1. 安装与运行

**环境要求**:
*   Python 3.8 或更高版本
*   PySide6 库

**安装步骤**:
1.  确保您的电脑已安装Python。
2.  打开终端（或CMD/PowerShell），安装必要的库：
    ```bash
    pip install PySide6
    ```
3.  将项目文件夹下载或克隆到您的电脑。
4.  在终端中，进入项目文件夹，运行主程序：
    ```bash
    python main.py
    ```
    首次运行会自动在项目文件夹下创建 `quick_kv.db` 数据库文件。

### 2. 主界面使用

*   **添加键值行**: 点击底部的 `添加新键组 (+)` 按钮，会增加一个“主行”。
*   **输入键/值**: 在左侧输入“键”，右侧输入“值”。输入时会自动弹出联想列表。
*   **添加多值**: 点击任意一行右侧的 `+` 按钮，会在其下方添加一个“次行”，用于输入同一个键的更多值。
*   **自定义分隔符**: 在“次行”最左侧的小框中，可以定义该值与前一个值之间的分隔符（默认为 `,`）。
*   **删除行**: 点击任意一行最右侧的 `X` 按钮。删除“主行”会一并删除其下的所有“次行”。
*   **复制到剪贴板**: 完成输入后，点击左上角的 `确定 (复制)` 按钮，所有内容将按格式拼接并复制。

### 3. 组合管理

*   **切换组合**: 使用左上角的下拉框，可以在不同的界面布局（组合）之间切换。每个组合都会记住自己独立的行和内容。
*   **管理组合**: 点击“管理组合”按钮，可以添加、重命名或删除组合。

### 4. 数据管理

*   点击 `管理数据` 按钮，打开数据管理中心。
*   **独立管理**: 左侧为“键”管理器，右侧为“值”管理器，两者完全独立。
*   **排序模式**:
    *   点击右上角的 `排序` 按钮，会弹出一个菜单。
    *   **手动排序 (默认)**: 您可以**直接用鼠标拖拽**列表中的项来改变它们的顺序。这个顺序会被永久保存。
    *   **字母排序**: 选择“按字母升序”或“按字母降序”可临时查看，此模式下无法拖拽。
*   **操作**: 双击可编辑，右键可删除或添加新项。
*   **导入/导出**: 点击窗口底部的 `导出为md` 或 `导入为md` 按钮，可以方便地备份和批量处理您的数据。

---

## 🛠️ 面向开发者：技术架构与维护指南

本项目采用 Python 和 PySide6 构建，遵循了清晰、模块化的设计原则，便于未来维护和功能扩展。

### 1. 项目结构

QuickKV/
├── main.py # 主程序入口，包含所有UI逻辑 (MainWindow, ManagementDialog等)
├── database.py # 数据库接口层，封装所有SQL操作
├── quick_kv.db # SQLite数据库文件，存储所有核心数据
└── README.md # 本文档


### 2. 核心技术栈

*   **GUI框架**: `PySide6` (Qt for Python)
*   **核心控件**: `QListWidget` (用于数据管理，稳定可靠)
*   **数据库**: `SQLite 3` (通过Python内置的 `sqlite3` 模块访问)
*   **配置存储**: `QSettings` (用于保存窗口状态、组合布局、历史记录等)

### 3. 数据库设计 (`database.py`)

数据库 (`quick_kv.db`) 包含两张核心表：`keys` 和 `value_items`。经过迭代，最终版本采用了简洁而稳健的扁平结构。

**表结构 (v2)**:
*   `id` (INTEGER PRIMARY KEY): 唯一标识符。
*   `key_text` / `value_text` (TEXT UNIQUE NOT NULL): 存储键或值的文本。
*   `sort_order` (INTEGER DEFAULT 0): **实现手动排序的核心**。用于记录用户拖拽后的顺序。

**版本控制**:
*   `ensure_db_tables()` 函数使用 `PRAGMA user_version` 来管理数据库版本。
*   **重要**: 当需要修改表结构时，应：
    1.  在 `database.py` 中提升 `APP_DB_VERSION` 的版本号。
    2.  在 `ensure_db_tables()` 中添加一个新的 `if db_version < NEW_VERSION:` 代码块。
    3.  在该代码块中，编写安全的 `ALTER TABLE` 或数据迁移脚本。

### 4. 主要UI类逻辑 (`main.py`)

*   **`MainWindow`**:
    *   程序主窗口，负责管理整体布局和“组合”的切换。
    *   通过 `QSettings` 在 `closeEvent` 中**强制同步 (`sync()`)** 保存所有状态，确保数据不丢失。
    *   持有 `key_model` 和 `value_model` (`QStringListModel`)，为所有 `InputRow` 提供全局的联想数据源。
*   **`InputRow`**:
    *   代表主界面上的一行输入。通过 `row_type` ("PRIMARY" 或 "SECONDARY") 区分形态。
    *   联想数据直接来自 `MainWindow` 传递的全局模型。
*   **`HistoryLineEdit`**:
    *   一个简单的 `QLineEdit` 子类，只负责通过 `deque` 和 `QSettings` 维护自己的输入历史。
*   **`ManagementDialog` & `DataManagerWidget`**:
    *   `ManagementDialog` 是一个容器，容纳了两个 `DataManagerWidget` 实例。
    *   `DataManagerWidget` 是核心，它**基于稳定可靠的 `QListWidget`**，实现了排序、搜索、增删改、导入/导出等所有管理逻辑。
    *   通过 `data_changed` 信号通知 `MainWindow` 数据库已发生变化，以便 `MainWindow` 刷新其全局联想模型。

### 5. 未来扩展方向

*   **云同步**: 可以通过集成如 Dropbox, Google Drive API 或自建服务，实现 `quick_kv.db` 文件的云端同步。
*   **插件系统**: 可以设计一个插件API，允许用户编写自己的“值生成器”（例如，一个能生成当前时间戳的插件）。
*   **更丰富的输出格式**: 允许用户通过模板语言（如 Jinja2）自定义“确定复制”后的输出格式。
*   **(可选)高级视图**: 如果未来对树状视图的需求非常强烈，可以考虑引入专业的、经过充分测试的第三方树控件库，而不是从头手写。

---

*文档最后更新于 2025-07-17*
