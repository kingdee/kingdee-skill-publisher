# 金蝶业务Skill发布器 - 快速开始

## 📦 打包的 Skill 文件

```
dist/kingdee-skill-publisher.skill
```

这是一个标准的 `.skill` 文件（zip格式），包含：
- `SKILL.md` - Skill定义和使用指南
- `LICENSE.txt` - MIT许可证
- `scripts/` - Python核心模块
- `references/` - 参考文档
- `tests/` - 测试文件

## 🚀 安装方法

### 方法1: 使用打包脚本（推荐）

```bash
python3 package_skill_proper.py
```

### 方法2: 手动安装

```bash
# 解压到 skills 目录
unzip dist/kingdee-skill-publisher.skill -d ~/.config/agents/skills/kingdee-skill-publisher
```

### 方法3: 直接复制（开发时）

```bash
# 复制必要文件到 skills 目录
cp -r scripts references tests ~/.config/agents/skills/kingdee-skill-publisher/
cp SKILL.md LICENSE.txt ~/.config/agents/skills/kingdee-skill-publisher/
```

## ✅ 验证安装

```bash
# 检查文件
ls ~/.config/agents/skills/kingdee-skill-publisher/

# 测试导入
python3 -c "from scripts import KingdeeSkillPublisher; print('✓ 安装成功')"
```

## 📖 使用 Skill

### 在 Claude 中使用

安装后，Claude 会自动加载 skill。根据 `SKILL.md` 中的描述触发：

> 当用户想要快速发布金蝶业务Skill、配置金蝶API接口、查询金蝶API清单时，使用此Skill。

### 在 Python 中使用

```python
from scripts import KingdeeSkillPublisher

# 创建发布器实例
publisher = KingdeeSkillPublisher()

# 配置凭证
result = publisher.setup_credentials(
    server_url="https://xxx.kingdee.com/ierp",
    app_id="your_app_id",
    app_secret="your_app_secret",
    account_id="your_account_id"
)

# 搜索API
apis = publisher.search_apis(
    appid_number="basedata",
    keyword="凭证"
)

# 获取API详情
detail = publisher.get_api_detail(api_id="123456")

# 创建Skill
result = publisher.create_skill_from_api_id(
    api_id="123456",
    skill_name="my-api-skill"
)
```

## 📁 项目结构

```
kingdee-skill-publisher/          # 项目根目录（开发）
├── SKILL.md                      # Skill定义（必需）
├── LICENSE.txt                   # 许可证
├── scripts/                      # Python模块
│   ├── __init__.py
│   ├── api_client.py
│   └── skill_generator.py
├── references/                   # 参考文档
├── tests/                        # 测试文件
├── dist/                         # 打包输出
│   └── kingdee-skill-publisher.skill
└── package_skill_proper.py       # 打包脚本

~/.config/agents/skills/          # 本地 skills 目录（安装后）
└── kingdee-skill-publisher/      # 安装的 skill
    ├── SKILL.md
    ├── LICENSE.txt
    ├── scripts/
    ├── references/
    └── tests/
```

## 🔧 开发工作流

1. **修改代码** → 编辑 `scripts/` 下的文件
2. **本地测试** → 直接运行测试脚本
3. **重新打包** → 运行 `package_skill_proper.py`
4. **验证安装** → 检查 `~/.config/agents/skills/`

## 📚 相关文档

- `SKILL.md` - 完整功能说明
- `PROJECT_SUMMARY.md` - 项目架构总结
- `ITERATION_SUMMARY_v2.md` - 迭代记录

---

**版本**: 1.2.0  
**打包日期**: 2026-03-16
