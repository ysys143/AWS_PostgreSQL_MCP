#!/usr/bin/env python3
"""
MCP Server Setup Script
git clone한 위치를 자동으로 감지하여 설정 파일들을 업데이트합니다.
"""

import os
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def get_project_root():
    """git 저장소의 루트 디렉토리를 찾습니다."""
    try:
        # git rev-parse --show-toplevel로 git 루트 찾기
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        # git이 없거나 git 저장소가 아닌 경우 현재 스크립트 위치 기준
        return Path(__file__).parent.absolute()

def get_user_home():
    """사용자 홈 디렉토리를 가져옵니다."""
    return Path.home()

def load_env_config():
    """dotenv를 사용하여 .env 파일을 로드합니다."""
    project_root = get_project_root()
    env_path = project_root / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        return True
    return False

def setup_mcp_config():
    """mcp.json 설정 파일을 동적으로 생성합니다."""
    project_root = get_project_root()
    
    # 운영체제에 따른 가상환경 Python 경로 설정
    if os.name == 'nt':  # Windows
        venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        venv_python = project_root / ".venv" / "bin" / "python"
    
    mcp_server = project_root / "mcp_server.py"
    
    # .env 파일 로드
    load_env_config()
    
    # 환경변수에서 값 읽기 (기본값 포함)
    default_env = {
        "PGHOST": os.getenv("PGHOST", "localhost"),
        "PGPORT": os.getenv("PGPORT", "10000"), 
        "PGUSER": os.getenv("PGUSER", "postgres"),
        "PGPASSWORD": os.getenv("PGPASSWORD", "your_password_here"),
        "PGDATABASE": os.getenv("PGDATABASE", "postgres"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "LOG_FILE": str(project_root / os.getenv("LOG_FILE", "pg_mcp.log"))
    }
    
    # Windows에서 JSON 경로는 forward slash 또는 이스케이프된 백슬래시 사용
    # Python의 json 모듈은 자동으로 백슬래시를 이스케이프 처리함
    mcp_config = {
        "mcpServers": {
            "AWS-PostgreSQL": {
                "command": str(venv_python),
                "args": [str(mcp_server)],
                "env": default_env
            }
        }
    }
    
    # .cursor 디렉토리 생성
    cursor_dir = project_root / ".cursor"
    cursor_dir.mkdir(exist_ok=True)
    
    # mcp.json 파일 생성
    mcp_json_path = cursor_dir / "mcp.json"
    with open(mcp_json_path, 'w', encoding='utf-8') as f:
        json.dump(mcp_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ MCP 설정 파일 생성됨: {mcp_json_path}")
    print(f"   프로젝트 루트: {project_root}")
    print(f"   Python 경로: {venv_python}")
    print(f"   서버 스크립트: {mcp_server}")

def setup_bastion_script():
    """운영체제에 맞는 SSH 터널링 스크립트를 생성합니다."""
    project_root = get_project_root()
    user_home = get_user_home()
    
    # .env 파일 로드
    load_env_config()
    
    # SSH 터널링 환경변수 읽기
    ssh_key_file = os.getenv('SSH_KEY_FILE')
    ssh_local_port = os.getenv('SSH_LOCAL_PORT') 
    ssh_rds_endpoint = os.getenv('SSH_RDS_ENDPOINT')
    ssh_rds_port = os.getenv('SSH_RDS_PORT')
    ssh_bastion_host = os.getenv('SSH_BASTION_HOST')
    
    # Windows와 Unix 계열 운영체제에 따른 스크립트 생성
    if os.name == 'nt':  # Windows
        # Windows용 PowerShell 스크립트 생성
        if all([ssh_key_file, ssh_local_port, ssh_rds_endpoint, ssh_rds_port, ssh_bastion_host]):
            # SSH 키 파일 경로 처리 (절대 경로가 아닌 경우 .ssh 폴더 기준)
            if not os.path.isabs(ssh_key_file):
                ssh_key_path = f"$env:USERPROFILE\\.ssh\\{ssh_key_file}"
            else:
                ssh_key_path = ssh_key_file.replace('\\', '\\\\')  # PowerShell용 이스케이프
            
            bastion_content = f"""# Windows PowerShell 스크립트 (.env 기반)
# 프로젝트 루트: {project_root}
# 사용자 홈: {user_home}

Write-Host "SSH 터널링을 시작합니다..."
Write-Host "로컬 포트 {ssh_local_port} -> RDS {ssh_rds_endpoint}:{ssh_rds_port}"
Write-Host ""
Write-Host "아래 SSH 명령어를 복사해서 PowerShell에 직접 붙여넣으세요:"
Write-Host "ssh -i `"{ssh_key_path}`" -L {ssh_local_port}:{ssh_rds_endpoint}:{ssh_rds_port} {ssh_bastion_host}" -ForegroundColor Yellow
Write-Host ""

# SSH 터널링 연결
ssh -i "{ssh_key_path}" -L {ssh_local_port}:{ssh_rds_endpoint}:{ssh_rds_port} {ssh_bastion_host}
"""
        else:
            bastion_content = f"""# Windows PowerShell 스크립트
# 프로젝트 루트: {project_root}
# 사용자 홈: {user_home}

Write-Host ".env에서 SSH 설정을 찾을 수 없어 기본 템플릿을 사용합니다"
Write-Host ".env에 다음 환경변수들을 설정하세요:"
Write-Host "SSH_KEY_FILE='your-ec2-key.pem'"
Write-Host "SSH_LOCAL_PORT='10000'"
Write-Host "SSH_RDS_ENDPOINT='your-rds-endpoint.region.rds.amazonaws.com'"
Write-Host "SSH_RDS_PORT='5432'"
Write-Host "SSH_BASTION_HOST='ec2-user@your-bastion-ip'"
Write-Host ""
Write-Host "아래 SSH 명령어를 복사해서 PowerShell에 직접 붙여넣으세요:"
Write-Host "ssh -i `"$env:USERPROFILE\\.ssh\\your-ec2-key.pem`" -L 10000:your-rds-endpoint.region.rds.amazonaws.com:5432 ec2-user@your-bastion-ip" -ForegroundColor Yellow
Write-Host ""

# SSH 터널링 연결 (기본값)
ssh -i "$env:USERPROFILE\\.ssh\\your-ec2-key.pem" -L 10000:your-rds-endpoint.region.rds.amazonaws.com:5432 ec2-user@your-bastion-ip
"""
        
        bastion_path = project_root / "bastion.ps1"
        with open(bastion_path, 'w', encoding='utf-8') as f:
            f.write(bastion_content)
        
        print(f"✅ Windows PowerShell 스크립트 생성됨: {bastion_path}")
        print(f"   실행 방법 1: powershell -ExecutionPolicy Bypass -File bastion.ps1")
        print(f"   실행 방법 2: Get-Content bastion.ps1 | powershell")
        print(f"   실행 방법 3: bastion.ps1 파일을 열어서 노란색 SSH 명령어를 복사해서 PowerShell에 붙여넣기")
        
    else:  # Unix/Linux/macOS
        # Unix용 bash 스크립트 생성
        if all([ssh_key_file, ssh_local_port, ssh_rds_endpoint, ssh_rds_port, ssh_bastion_host]):
            # SSH 키 파일 경로 처리 (절대 경로가 아닌 경우 .ssh 폴더 기준)
            if not os.path.isabs(ssh_key_file):
                ssh_key_path = f"~/.ssh/{ssh_key_file}"
            else:
                ssh_key_path = ssh_key_file
            
            bastion_content = f"""#!/bin/bash
# 동적으로 생성된 bastion 스크립트 (.env 기반)
# 프로젝트 루트: {project_root}
# 사용자 홈: {user_home}

cd "{user_home}/.ssh/"

echo "SSH 터널링을 시작합니다..."
echo "로컬 포트 {ssh_local_port} -> RDS {ssh_rds_endpoint}:{ssh_rds_port}"

# SSH 터널링 연결
ssh -i {ssh_key_path} -L {ssh_local_port}:{ssh_rds_endpoint}:{ssh_rds_port} {ssh_bastion_host}
"""
        else:
            bastion_content = f"""#!/bin/bash
# 동적으로 생성된 bastion 스크립트
# 프로젝트 루트: {project_root}
# 사용자 홈: {user_home}

cd "{user_home}/.ssh/"

echo ".env에서 SSH 설정을 찾을 수 없어 기본 템플릿을 사용합니다"
echo ".env에 다음 환경변수들을 설정하세요:"
echo "SSH_KEY_FILE='your-ec2-key.pem'"
echo "SSH_LOCAL_PORT='10000'"
echo "SSH_RDS_ENDPOINT='your-rds-endpoint.region.rds.amazonaws.com'"
echo "SSH_RDS_PORT='5432'"
echo "SSH_BASTION_HOST='ec2-user@your-bastion-ip'"

# SSH 터널링 연결 (기본값)
ssh -i your-ec2-key.pem -L 10000:your-rds-endpoint.region.rds.amazonaws.com:5432 ec2-user@your-bastion-ip
"""
        
        bastion_path = project_root / "bastion.sh"
        with open(bastion_path, 'w', encoding='utf-8') as f:
            f.write(bastion_content)
        
        # 실행 권한 부여 (Unix 계열만)
        os.chmod(bastion_path, 0o755)
        
        print(f"✅ Bash 스크립트 생성됨: {bastion_path}")
        print(f"   실행 방법: bash bastion.sh")
    
    # 공통 정보 출력
    if all([ssh_key_file, ssh_local_port, ssh_rds_endpoint, ssh_rds_port, ssh_bastion_host]):
        print(f"✅ SSH 터널링 정보를 .env에서 읽어옴:")
        print(f"   키 파일: {ssh_key_file}")
        print(f"   로컬 포트: {ssh_local_port}")
        print(f"   RDS 엔드포인트: {ssh_rds_endpoint}:{ssh_rds_port}")
        print(f"   베스천 호스트: {ssh_bastion_host}")
    else:
        print("⚠️  .env에서 SSH 터널링 정보를 찾을 수 없음. 기본 템플릿 사용.")
        print("   SSH_KEY_FILE, SSH_LOCAL_PORT, SSH_RDS_ENDPOINT, SSH_RDS_PORT, SSH_BASTION_HOST")
        print("   환경변수들을 .env에 설정하세요.")
    
    print(f"   SSH 키 경로: {user_home}/.ssh/")

def main():
    """메인 설정 함수"""
    print("🔧 MCP PostgreSQL 서버 설정을 시작합니다...")
    print()
    
    try:
        setup_mcp_config()
        setup_bastion_script()
        
        print()
        print("🎉 설정이 완료되었습니다!")
        print()
        print("다음 단계:")
        print("1. 가상환경이 활성화되어 있는지 확인")
        print("2. .env 파일의 실제 값들을 업데이트")
        print("3. Cursor에서 MCP 서버 재연결")
        if os.name == 'nt':  # Windows
            print("4. bastion.ps1 실행으로 터널링 연결 확인")
            print("   실행: powershell -ExecutionPolicy Bypass -File bastion.ps1")
            print("   또는: Get-Content bastion.ps1 | powershell")
        else:  # Unix/Linux/macOS
            print("4. bastion.sh 실행으로 터널링 연결 확인")
            print("   실행: bash bastion.sh")
        
    except Exception as e:
        print(f"❌ 설정 중 오류가 발생했습니다: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 