#!/usr/bin/env python3
"""
完整项目备份工具
备份所有文件、配置、环境信息，确保可以在其他电脑上完全还原
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


class ProjectBackuper:
    """项目备份器"""

    def __init__(self):
        self.script_dir = Path(__file__).parent.resolve()
        self.backup_dir = self.script_dir / "backup_full"
        self.backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_name = f"NagaAgent_Backup_{self.backup_time}"
        self.backup_path = self.backup_dir / self.backup_name

    def print_banner(self):
        """打印横幅"""
        banner = """
===========================================================

              NagaAgent Full Backup Tool

         Complete Migration - All Configs & Files

===========================================================
        """
        print(banner)

    def create_backup_dir(self):
        """创建备份目录"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
        if not self.backup_path.exists():
            self.backup_path.mkdir(parents=True)
        print(f"[OK] Backup directory created: {self.backup_path}")

    def backup_source_files(self):
        """备份所有源代码文件"""
        print("\n[1/6] Backing up source files...")

        exclude_dirs = {
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            "backup_full",
            "release",
            ".pytest_cache",
            ".mypy_cache",
        }

        for item in self.script_dir.iterdir():
            if item.name in exclude_dirs:
                print(f"  - Skipped {item.name}")
                continue

            dest = self.backup_path / item.name

            if item.is_dir():
                print(f"  - Copying directory: {item.name}")
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", ".git", "*.log", "*.cache"
                ), dirs_exist_ok=True)
            else:
                print(f"  - Copying file: {item.name}")
                shutil.copy2(item, dest)

        print("[OK] Source files backed up")

    def backup_config(self):
        """备份配置文件"""
        print("\n[2/6] Backing up configuration...")

        config_files = [
            "config.json",
            "config.json.example",
        ]

        for cfg_file in config_files:
            src = self.script_dir / cfg_file
            if src.exists():
                print(f"  - {cfg_file}")
                shutil.copy2(src, self.backup_path / cfg_file)

        # 复制所有配置相关的目录
        config_dirs = [
            "baodou_AI",
            "VCPToolBox",
        ]

        for dir_name in config_dirs:
            src = self.script_dir / dir_name
            if src.is_dir():
                dest = self.backup_path / dir_name
                print(f"  - Directory: {dir_name}")
                shutil.copytree(src, dest, dirs_exist_ok=True)

        print("[OK] Configuration backed up")

    def backup_environment_info(self):
        """备份环境信息"""
        print("\n[3/6] Collecting environment information...")

        env_info = {
            "backup_time": datetime.now().isoformat(),
            "backup_version": "1.0",
        }

        # Python 信息
        try:
            import platform
            env_info["python"] = {
                "version": platform.python_version(),
                "executable": sys.executable,
                "platform": platform.platform(),
                "system": platform.system(),
                "machine": platform.machine(),
            }
            print(f"  - Python {env_info['python']['version']}")
        except Exception as e:
            print(f"  [Warning] Failed to get Python info: {e}")

        # pip 信息
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True
            )
            env_info["pip"] = result.stdout.strip()
            print(f"  - pip version retrieved")
        except Exception as e:
            print(f"  [Warning] Failed to get pip info: {e}")

        # 当前工作目录
        env_info["project_path"] = str(self.script_dir)
        print(f"  - Project path: {self.script_dir}")

        # 保存环境信息
        env_file = self.backup_path / "_environment_info.json"
        with open(env_file, 'w', encoding='utf-8') as f:
            json.dump(env_info, f, indent=2, ensure_ascii=False)

        print("[OK] Environment info saved")

    def backup_installed_packages(self):
        """备份已安装的包列表"""
        print("\n[4/6] Backing up installed packages...")

        # 备份当前环境的包列表
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                packages_file = self.backup_path / "_installed_packages.json"
                with open(packages_file, 'w', encoding='utf-8') as f:
                    json.dump(packages, f, indent=2)
                print(f"  - {len(packages)} packages saved")
        except Exception as e:
            print(f"  [Warning] Failed to get packages list: {e}")

        # 备份 requirements.txt
        if (self.script_dir / "requirements.txt").exists():
            shutil.copy2(
                self.script_dir / "requirements.txt",
                self.backup_path / "requirements.txt"
            )
            # 同时备份 requirements_install.txt（无中文注释版本）
            if (self.script_dir / "requirements_install.txt").exists():
                shutil.copy2(
                    self.script_dir / "requirements_install.txt",
                    self.backup_path / "requirements_install.txt"
                )
            print(f"  - requirements.txt copied")

        # 生成完整依赖树
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                freeze_file = self.backup_path / "_pip_freeze.txt"
                with open(freeze_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                print(f"  - pip freeze saved")
        except Exception as e:
            print(f"  [Warning] Failed to run pip freeze: {e}")

        print("[OK] Packages information backed up")

    def backup_logs(self):
        """备份日志文件"""
        print("\n[5/6] Backing up logs...")

        logs_dir = self.script_dir / "logs"
        if logs_dir.exists():
            backup_logs_dir = self.backup_path / "logs"
            shutil.copytree(logs_dir, backup_logs_dir, dirs_exist_ok=True)
            print(f"  - Logs directory copied")
        else:
            print(f"  [TIP] No logs directory found")

        # 查找其他日志文件
        for log_file in self.script_dir.glob("*.log"):
            if log_file.parent == self.script_dir:
                shutil.copy2(log_file, self.backup_path / log_file.name)
                print(f"  - {log_file.name}")

        print("[OK] Logs backed up")

    def create_restore_script(self):
        """创建还原脚本"""
        print("\n[6/6] Creating restore script...")

        # Windows 批处理还原脚本
        restore_bat = f"""@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ============================================================
echo.
echo         NagaAgent Restore Tool
echo.
echo     Restoring backup: {self.backup_name}
echo.
echo ============================================================
echo.

echo [1/4] Checking Python environment...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo [OK] Python found
echo.

echo [2/4] Creating virtual environment...
if exist ".venv" (
    echo [TIP] Existing .venv detected, delete and recreate?
    choice /C YN /M "Delete and recreate"
    if errorlevel 2 (
        echo Keeping existing .venv
    ) else (
        rmdir /s /q .venv
        python -m venv .venv
    )
) else (
    python -m venv .venv
)
echo [OK] Virtual environment created
echo.

echo [3/4] Installing dependencies...
call .venv\\Scripts\\activate.bat
if exist "requirements_install.txt" (
    echo Using requirements_install.txt (no Chinese comments)
    pip install -r requirements_install.txt -i https://pypi.org/simple --default-timeout=300
    echo [OK] Dependencies installed
) else (
    echo [Warning] requirements_install.txt not found
    echo Skipping dependency installation
)
echo.

echo [4/4] Restore complete!
echo.
echo Next steps:
echo   1. Check config.json and update paths if needed
echo   2. Run install_wizard.py if needed
echo   3. Start with start.bat
echo.
pause
"""

        restore_bat_path = self.backup_path / "restore.bat"
        with open(restore_bat_path, 'w', encoding='utf-8') as f:
            f.write(restore_bat)

        # Linux/Mac 还原脚本
        restore_sh = f"""#!/bin/bash

echo "============================================================"
echo ""
echo "         NagaAgent Restore Tool"
echo ""
echo "     Restoring backup: {self.backup_name}"
echo ""
echo "============================================================"
echo ""

echo "[1/4] Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found"
    exit 1
fi
echo "[OK] Python found"
echo ""

echo "[2/4] Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "[TIP] Existing .venv detected"
    read -p "Delete and recreate? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
    fi
else
    python3 -m venv .venv
fi
echo "[OK] Virtual environment created"
echo ""

        echo "[3/4] Installing dependencies..."
        source .venv/bin/activate
        if [ -f "requirements_install.txt" ]; then
            echo "Using requirements_install.txt (no Chinese comments)"
            pip install -r requirements_install.txt -i https://pypi.org/simple
            echo "[OK] Dependencies installed"
        else
            echo "[Warning] requirements_install.txt not found"
            echo "Skipping dependency installation"
        fi
        echo ""

echo "[4/4] Restore complete!"
echo ""
echo "Next steps:"
echo "  1. Check config.json and update paths if needed"
echo "  2. Run install_wizard.py if needed"
echo "  3. Start with ./start.sh"
echo ""
"""

        restore_sh_path = self.backup_path / "restore.sh"
        with open(restore_sh_path, 'w', encoding='utf-8') as f:
            f.write(restore_sh)

        # 创建还原说明
        restore_guide = f"""
===========================================================
             NagaAgent Backup - Restore Guide
===========================================================

Backup Information:
  Name: {self.backup_name}
  Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
  Path: {self.backup_path}

Restore Instructions:

Windows:
  1. Extract this backup to a new location
  2. Double-click: restore.bat
  3. Follow the prompts

Linux/Mac:
  1. Extract this backup to a new location
  2. Run: chmod +x restore.sh && ./restore.sh
  3. Follow the prompts

Manual Restore:
  1. Create virtual environment:
     python -m venv .venv

  2. Activate virtual environment:
     Windows: .venv\\Scripts\\activate
     Linux/Mac: source .venv/bin/activate

  3. Install dependencies:
     pip install -r requirements.txt

  4. Check config.json and update any paths if needed

  5. Start the program:
     Windows: start.bat
     Linux/Mac: ./start.sh

Important Notes:
  - This backup includes your current configuration
  - API keys are preserved (keep them secure!)
  - Local paths in config.json may need updating
  - Neo4j and other external services need to be set up separately
  - Logs are included for reference

Files Included:
  - All source code
  - Configuration files (config.json, etc.)
  - Installed packages list
  - Environment information
  - Logs
  - Documentation

===========================================================
"""

        guide_path = self.backup_path / "RESTORE_GUIDE.txt"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(restore_guide)

        print("[OK] Restore script created")

    def create_readme(self):
        """创建备份说明"""
        readme = f"""
# NagaAgent Complete Backup

This is a complete backup of your NagaAgent project.

## What's Included

- All source code
- Current configuration (config.json)
- Environment information
- Installed packages list
- Logs (if any)
- All documentation

## How to Use

### On Another Computer

1. **Extract the backup** to your desired location

2. **Run the restore script**:
   - Windows: Double-click `restore.bat`
   - Linux/Mac: `./restore.sh`

3. **Update paths** in `config.json` if needed (check for absolute paths)

4. **Set up external services**:
   - Neo4j (if using knowledge graph)
   - GPT-SoVITS (if using voice)
   - Other services as configured

5. **Start the program**:
   - Windows: `start.bat`
   - Linux/Mac: `./start.sh`

## Important Security Notes

⚠️ **This backup contains sensitive information:**
- API keys (DeepSeek, etc.)
- Configuration settings
- Potentially personal data in logs

**Keep this backup secure!** Do not share it publicly.

## Backup Details

- **Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Version**: {self.backup_name}
- **Original Path**: {self.script_dir}

## Troubleshooting

If something doesn't work after restore:

1. Check that Python 3.11+ is installed
2. Verify the virtual environment was created
3. Check config.json for any hardcoded paths
4. Ensure all external services (Neo4j, etc.) are running
5. Check the logs in the `logs/` directory

For more help, see the original project documentation.
"""

        readme_path = self.backup_path / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme)

        print(f"[OK] README created")

    def compress_backup(self):
        """压缩备份"""
        print("\nCompressing backup...")

        import zipfile

        zip_path = self.backup_dir / f"{self.backup_name}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.backup_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.backup_path)
                    zipf.write(file_path, arcname)

        size_mb = zip_path.stat().st_size / (1024 * 1024)

        print(f"[OK] Backup compressed: {zip_path.name}")
        print(f"     Size: {size_mb:.2f} MB")

        # 询问是否删除未压缩的备份
        print("\nDo you want to keep the uncompressed backup?")
        print("(Recommended: No, keep only the .zip file)")
        keep = input("[Y/n]: ").strip().lower()
        if keep == 'n':
            try:
                shutil.rmtree(self.backup_path)
                print("[OK] Uncompressed backup removed")
            except Exception as e:
                print(f"[Warning] Failed to remove uncompressed backup: {e}")

        return zip_path

    def run(self):
        """运行备份"""
        try:
            self.print_banner()

            print(f"Backup will be created in: {self.backup_path}")
            input("\nPress Enter to continue, or Ctrl+C to cancel...")

            self.create_backup_dir()
            self.backup_source_files()
            self.backup_config()
            self.backup_environment_info()
            self.backup_installed_packages()
            self.backup_logs()
            self.create_restore_script()
            self.create_readme()

            print("\n" + "=" * 60)
            print("Backup completed successfully!")
            print("=" * 60)

            compress = input("\nCompress backup to .zip? [Y/n]: ").strip().lower()
            if compress != 'n':
                zip_path = self.compress_backup()

                print("\n" + "=" * 60)
                print("Next steps:")
                print("=" * 60)
                print(f"\n1. Backup file created:")
                print(f"   {zip_path}")
                print(f"\n2. To transfer to another computer:")
                print(f"   - Copy the .zip file")
                print(f"   - Extract to desired location")
                print(f"   - Run restore.bat (Windows) or ./restore.sh (Linux/Mac)")
                print(f"\n3. After restore, update any paths in config.json if needed")
                print(f"\n⚠️  Keep this backup secure - it contains API keys!")

        except KeyboardInterrupt:
            print("\n\nBackup cancelled by user")
        except Exception as e:
            print(f"\n[ERROR] Backup failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    backuper = ProjectBackuper()
    backuper.run()


if __name__ == "__main__":
    main()
