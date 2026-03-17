#!/usr/bin/env python3
"""
金蝶业务Skill发布器 - 标准打包脚本

按照 Skill Creator 最佳实践打包 skill:
- 打包为 .skill 文件 (zip格式)
- 验证 skill 结构
- 只包含必要文件
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Tuple, List


def validate_skill(skill_dir: str) -> Tuple[bool, List]:
    """
    验证 skill 结构是否符合规范
    
    Returns:
        (是否有效, 警告列表)
    """
    warnings = []
    
    # 检查 SKILL.md 是否存在
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md):
        print("❌ 错误: 缺少必需的 SKILL.md 文件")
        return False, ["缺少必需的 SKILL.md 文件"]
    else:
        # 检查 frontmatter
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.startswith('---'):
                print("❌ 错误: SKILL.md 缺少 YAML frontmatter")
                return False, ["SKILL.md 缺少 YAML frontmatter"]
            elif 'name:' not in content or 'description:' not in content:
                print("❌ 错误: SKILL.md frontmatter 缺少 name 或 description 字段")
                return False, ["SKILL.md frontmatter 缺少 name 或 description 字段"]
    
    # 检查 scripts 目录（如果有）
    scripts_dir = os.path.join(skill_dir, "scripts")
    if os.path.exists(scripts_dir):
        init_file = os.path.join(scripts_dir, "__init__.py")
        if not os.path.exists(init_file):
            warnings.append("scripts 目录缺少 __init__.py 文件")
    
    # 检查是否有不必要的文件（仅警告，不阻止打包）
    unnecessary = ["README.md", "INSTALL.md", "CHANGELOG.md", "QUICK_REFERENCE.md"]
    for filename in unnecessary:
        if os.path.exists(os.path.join(skill_dir, filename)):
            warnings.append(f"发现辅助文档: {filename} (将在打包时自动排除)")
    
    return True, warnings


def package_skill_both_formats(source_dir: str, output_dir: str) -> tuple:
    """
    打包 skill 为 .skill 和 .zip 两种格式
    
    Args:
        source_dir: skill 源目录
        output_dir: 输出目录
        
    Returns:
        (skill_file_path, zip_file_path)
    """
    skill_name = "kingdee-skill-publisher"
    version = "1.2.0"
    
    # 构建输出文件名
    skill_file = os.path.join(output_dir, f"{skill_name}.skill")
    zip_file = os.path.join(output_dir, f"{skill_name}.zip")
    
    print(f"\n📦 打包 Skill: {skill_name}")
    print(f"📋 版本: {version}")
    print(f"📂 源目录: {source_dir}")
    
    # 需要包含的文件和目录
    includes = [
        "SKILL.md",
        "LICENSE.txt",
        "scripts",
        "references",
        "tests"
    ]
    
    def create_archive(output_path: str, format_name: str):
        """创建压缩文件"""
        print(f"\n📝 创建 {format_name} 文件...")
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in includes:
                source_path_full = os.path.join(source_dir, item)
                
                if not os.path.exists(source_path_full):
                    print(f"  ⚠️ 跳过不存在: {item}")
                    continue
                
                if os.path.isdir(source_path_full):
                    # 添加目录中的所有文件
                    for root, dirs, files in os.walk(source_path_full):
                        # 排除 __pycache__ 等
                        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.DS_Store']]
                        
                        for file in files:
                            if file.endswith(('.pyc', '.pyo', '.DS_Store')):
                                continue
                            
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_dir)
                            zf.write(file_path, arcname)
                            print(f"  + {arcname}")
                else:
                    # 添加单个文件
                    arcname = item
                    zf.write(source_path_full, arcname)
                    print(f"  + {arcname}")
    
    # 创建 .skill 文件
    create_archive(skill_file, ".skill")
    
    # 创建 .zip 文件（内容完全相同）
    print(f"\n📦 复制为 ZIP 格式...")
    shutil.copy2(skill_file, zip_file)
    
    return skill_file, zip_file


def install_skill_locally(skill_file: str, skills_dir: str):
    """
    在本地安装 skill
    
    Args:
        skill_file: .skill 文件路径
        skills_dir: 本地 skills 目录
    """
    skill_name = "kingdee-skill-publisher"
    install_dir = os.path.join(skills_dir, skill_name)
    
    print(f"\n📥 本地安装 Skill")
    print(f"📂 安装目录: {install_dir}")
    
    # 备份现有版本
    if os.path.exists(install_dir):
        backup_name = f"{skill_name}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        backup_dir = os.path.join(skills_dir, backup_name)
        print(f"📦 备份现有版本到: {backup_dir}")
        shutil.move(install_dir, backup_dir)
    
    # 解压 .skill 文件
    print(f"📂 解压 skill 文件...")
    os.makedirs(install_dir, exist_ok=True)
    
    with zipfile.ZipFile(skill_file, 'r') as zf:
        zf.extractall(install_dir)
    
    print(f"✅ 安装完成")
    
    # 验证安装
    print(f"\n🔍 验证安装...")
    skill_md = os.path.join(install_dir, "SKILL.md")
    scripts_dir = os.path.join(install_dir, "scripts")
    
    checks = [
        ("SKILL.md", os.path.exists(skill_md)),
        ("scripts/", os.path.exists(scripts_dir)),
        ("scripts/__init__.py", os.path.exists(os.path.join(scripts_dir, "__init__.py"))),
        ("scripts/api_client.py", os.path.exists(os.path.join(scripts_dir, "api_client.py"))),
    ]
    
    for name, exists in checks:
        status = "✓" if exists else "✗"
        print(f"  {status} {name}")
    
    return install_dir


def get_skills_dir():
    """获取本地 skills 目录"""
    home = Path.home()
    
    # 按优先级检查
    possible_dirs = [
        home / ".config" / "agents" / "skills",
        home / ".kimi" / "skills",
        home / ".claude" / "skills",
    ]
    
    # 使用第一个存在的，或创建默认的
    for d in possible_dirs:
        if d.exists():
            return str(d)
    
    # 创建默认目录
    default = possible_dirs[0]
    default.mkdir(parents=True, exist_ok=True)
    return str(default)


def main():
    """主函数"""
    print("=" * 60)
    print("金蝶业务Skill发布器 - 标准打包与安装")
    print("=" * 60)
    
    source_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 询问打包位置
    print("\n选择打包位置:")
    print("  1. 当前目录 (./kingdee-skill-publisher.skill)")
    print("  2. dist/ 目录 (./dist/kingdee-skill-publisher.skill)")
    
    location_choice = input("\n请输入选项 (1/2，默认1): ").strip() or "1"
    
    if location_choice == "1":
        output_dir = source_dir
    else:
        output_dir = os.path.join(source_dir, "dist")
        os.makedirs(output_dir, exist_ok=True)
    
    # 步骤1: 验证 skill
    print("\n" + "-" * 60)
    print("步骤 1/3: 验证 Skill 结构")
    print("-" * 60)
    
    is_valid, errors = validate_skill(source_dir)
    
    if not is_valid:
        print("\n❌ 验证失败:")
        for error in errors:
            print(f"  ✗ {error}")
        print("\n请修复上述问题后重新打包")
        return 1
    
    print("\n✅ 验证通过")
    
    # 步骤2: 打包
    print("\n" + "-" * 60)
    print("步骤 2/3: 打包 Skill")
    print("-" * 60)
    
    skill_file, zip_file = package_skill_both_formats(source_dir, output_dir)
    
    # 显示打包信息
    skill_size = os.path.getsize(skill_file) / 1024
    zip_size = os.path.getsize(zip_file) / 1024
    
    print(f"\n📊 打包完成:")
    print(f"  📄 {skill_file}")
    print(f"     大小: {skill_size:.2f} KB")
    print(f"  📄 {zip_file}")
    print(f"     大小: {zip_size:.2f} KB")
    print(f"\n💡 提示: .skill 和 .zip 内容相同，只是扩展名不同")
    
    # 步骤3: 本地安装
    print("\n" + "-" * 60)
    print("步骤 3/3: 本地安装")
    print("-" * 60)
    
    skills_dir = get_skills_dir()
    print(f"\n📂 Skills 目录: {skills_dir}")
    
    confirm = input("\n是否安装到本地 skills 目录? (y/n，默认y): ").strip().lower()
    if confirm != "n":
        # 使用 zip 文件进行安装（两种格式内容相同）
        install_dir = install_skill_locally(zip_file, skills_dir)
        
        print("\n" + "=" * 60)
        print("安装完成！")
        print("=" * 60)
        print(f"\n📂 安装路径: {install_dir}")
        print(f"\n使用方法:")
        print(f"  1. Skill 已自动加载到 Claude")
        print(f"  2. 或在 Python 中使用:")
        print(f"     from scripts import KingdeeSkillPublisher")
        print(f"     publisher = KingdeeSkillPublisher()")
    else:
        print("\n跳过本地安装")
        print(f"\n📦 打包文件已保存:")
        print(f"  - {skill_file}")
        print(f"  - {zip_file}")
        print(f"\n手动安装命令:")
        print(f"  unzip kingdee-skill-publisher.zip -d ~/.config/agents/skills/kingdee-skill-publisher")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
