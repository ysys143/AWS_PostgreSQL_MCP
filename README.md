# AWS PostgreSQL MCP Server

AWS RDS PostgreSQL 데이터베이스에 SSH 터널링을 통해 연결하는 MCP (Model Context Protocol) 서버입니다.

## 프로젝트 개요

이 프로젝트는 Cursor Agent가 PostgreSQL 데이터베이스에 직접 쿼리를 실행할 수 있도록 하는 MCP 서버를 제공합니다. AWS RDS 인스턴스에 SSH bastion 호스트를 통해 안전하게 연결됩니다. 공식 Postgres MCP와 같이 Node.js를 이용하는 경우, bastion 호스트를 거치는 과정에서 잘못된 주소로 요청을 보내는 오류가 발생할 수 있습니다. Python Psycopg를 이용하면 오류가 발생하지 않습니다.

## 사전 요구사항

- Python 3.8 이상
- uv (Python 패키지 관리자)
- git
- SSH 클라이언트
- AWS EC2 키 페어 (`your-ec2-key.pem`)

## 설치 및 설정

### 1. 저장소 클론

**Unix/Linux/macOS:**
```bash
git clone https://github.com/ysys143/AWS_PostgreSQL_MCP.git
cd AWS_PostgreSQL_MCP
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/ysys143/AWS_PostgreSQL_MCP.git
cd AWS_PostgreSQL_MCP
```

### 2. 가상환경 생성 및 활성화

**Unix/Linux/macOS:**
```bash
# uv를 사용한 가상환경 생성
uv venv

# 가상환경 활성화
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
# uv를 사용한 가상환경 생성
uv venv

# 가상환경 활성화
.venv\Scripts\Activate.ps1
```

### 3. 의존성 설치

```bash
uv pip install -r requirements.txt
```

### 4. 환경 변수 설정

**Unix/Linux/macOS:**
```bash
cp .env_example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env_example .env
```

**⚠️ 중요:** `.env` 파일을 편집하여 실제 데이터베이스 연결 정보로 수정해야 합니다:

```bash
# .env 파일 내용 예시 - 실제 값으로 변경 필요!
# Connection
PGPASSWORD='your_actual_database_password'  # ⚠️ 실제 비밀번호로 변경 필수!
PGHOST='localhost'
PGPORT='10000'
PGUSER='postgres'
PGDATABASE='postgres'

# SSH Tunnel Configuration
SSH_KEY_FILE='your-ec2-key.pem'  # ⚠️ 실제 키 파일명으로 변경
SSH_LOCAL_PORT='10000'
SSH_RDS_ENDPOINT='your-rds-endpoint.region.rds.amazonaws.com'  # ⚠️ 실제 RDS 엔드포인트로 변경
SSH_RDS_PORT='5432'
SSH_BASTION_HOST='ec2-user@your-bastion-ip'  # ⚠️ 실제 bastion 호스트로 변경

# Logging
LOG_LEVEL='INFO'
LOG_FILE='pg_mcp.log'
```

### 5. 자동 설정 실행

```bash
uv run setup.py
```

이 명령어는 다음을 자동으로 수행합니다:
- git clone된 위치를 자동 감지
- 사용자 홈 디렉토리 자동 감지  
- `.cursor/mcp.json` 설정 파일 생성
- 운영체제별 SSH 터널링 스크립트 생성:
  - **Unix/Linux/macOS**: `bastion.sh` (Bash 스크립트)
  - **Windows**: `bastion.ps1` (PowerShell 스크립트)
- 모든 경로를 현재 환경에 맞게 자동 설정

### 6. SSH 키 설정

**옵션 1: 홈 디렉토리 .ssh 폴더 사용 (권장)**

AWS EC2 키 파일을 홈 디렉토리의 `.ssh` 폴더에 배치합니다:

**Unix/Linux/macOS:**
```bash
# SSH 디렉토리 생성 (없는 경우)
mkdir -p ~/.ssh

# 키 파일 복사 및 권한 설정
cp your-ec2-key.pem ~/.ssh/
chmod 600 ~/.ssh/your-ec2-key.pem
```

**Windows (PowerShell):**
```powershell
# SSH 디렉토리 생성 (없는 경우)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh"

# 키 파일 복사
Copy-Item your-ec2-key.pem "$env:USERPROFILE\.ssh\"

# 파일 권한 설정 (소유자만 읽기 권한)
icacls "$env:USERPROFILE\.ssh\your-ec2-key.pem" /inheritance:r /grant:r "$env:USERNAME:R"
```

이 경우 `.env` 파일에서 파일명만 지정하면 됩니다:
```bash
SSH_KEY_FILE='your-ec2-key.pem'
```

**옵션 2: 다른 위치의 키 파일 사용**

SSH 키를 다른 위치에 보관하고 있다면 절대 경로를 사용할 수 있습니다:

**Unix/Linux/macOS:**
```bash
# 키 파일 권한 설정 (위치에 관계없이 필요)
chmod 600 /path/to/your/key/your-ec2-key.pem
```

**Windows (PowerShell):**
```powershell
# 키 파일 권한 설정 (위치에 관계없이 필요)
icacls "C:\path\to\your\key\your-ec2-key.pem" /inheritance:r /grant:r "$env:USERNAME:R"
```

이 경우 `.env` 파일에서 전체 경로를 지정합니다:
```bash
# 절대 경로 사용 (Unix/Linux/macOS)
SSH_KEY_FILE='/Users/username/Documents/keys/your-ec2-key.pem'

# 절대 경로 사용 (Windows)
SSH_KEY_FILE='C:\Users\username\Documents\keys\your-ec2-key.pem'

# 홈 디렉토리 기준 상대 경로
SSH_KEY_FILE='~/Documents/keys/your-ec2-key.pem'

# 프로젝트 기준 상대 경로
SSH_KEY_FILE='../keys/your-ec2-key.pem'
```

## 사용법

### 1. SSH 터널링 연결

**이미 bastion 호스트가 설정되어 있고 터널링이 정상 작동하는 경우:**
- 별도로 `bastion.sh` 스크립트를 실행할 필요가 없습니다
- 기존 터널링 연결을 그대로 사용하면 됩니다
- MCP 서버가 `localhost:10000` (또는 설정한 포트)으로 연결할 수 있으면 충분합니다

**새로 터널링을 설정해야 하는 경우:**

**Unix/Linux/macOS:**
```bash
# bastion 호스트를 통한 터널링 시작
bash bastion.sh
```

**Windows (PowerShell):**
```powershell
# 방법 1: PowerShell 스크립트 실행 (권장)
powershell -ExecutionPolicy Bypass -File bastion.ps1

# 방법 2: 파이프를 통한 실행
Get-Content bastion.ps1 | powershell

# 방법 3: 직접 SSH 명령어 실행
ssh -i "$env:USERPROFILE\.ssh\your-ec2-key.pem" -L 10000:your-rds-endpoint.region.rds.amazonaws.com:5432 ec2-user@your-bastion-ip
```

**Windows에서 "코드에 접근할 수 없습니다" 오류 발생 시:**
- `bastion.ps1` 파일을 메모장으로 열어서 노란색으로 표시된 SSH 명령어를 복사
- PowerShell에 직접 붙여넣기하여 실행

이 명령어는 백그라운드에서 실행되며, 로컬 포트 10000을 통해 RDS 인스턴스에 연결합니다.

### 2. 연결 테스트 (선택사항)

**방법 1: 전용 테스트 스크립트 사용 (권장)**

MCP 연결 문제가 발생하거나 데이터베이스 연결을 확인하려면 `test_connection.py`를 사용하세요:

```bash
# 간단한 연결 테스트
python test_connection.py "SELECT 1"

# PostgreSQL 버전 확인
python test_connection.py "SELECT version()"

# 현재 시간 확인
python test_connection.py "SELECT now()"

# 테이블 목록 조회
python test_connection.py "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"

# 대화형 모드로 여러 쿼리 실행
python test_connection.py
```

`test_connection.py`는 `.env` 파일의 설정을 자동으로 읽어서 연결하며, 연결 정보와 쿼리 결과를 상세히 표시해줍니다.

**중요:** `test_connection.py` 사용 전 반드시 확인하세요:
- `.env` 파일이 존재하고 올바른 값들이 설정되어 있는지 확인
- `PGPASSWORD` 환경 변수에 실제 데이터베이스 비밀번호가 설정되어 있는지 확인
- SSH 터널링이 활성화되어 있는지 확인 (포트 10000 사용 중인지)

**방법 2: 기본 도구 사용**

```bash
# PostgreSQL 연결 테스트 (psql이 설치된 경우)
psql -h localhost -p 10000 -U postgres -d postgres

# 또는 Python으로 간단 테스트
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=10000, user='postgres', password='your_password', database='postgres'); print('연결 성공!')"
```

### 3. MCP 서버 연결

Cursor IDE에서:
1. MCP 서버 설정 새로고침
2. `AWS-PostgreSQL` 서버 연결 확인
3. 연결 상태가 정상인지 확인

### 4. 데이터베이스 쿼리 실행

MCP 서버가 연결되면 AI 모델에게 다음과 같이 요청할 수 있습니다:

```
PostgreSQL 데이터베이스에서 모든 테이블 목록을 조회해주세요.
```

## 프로젝트 구조

```
AWS_PostgreSQL_MCP/
├── setup.py              # 자동 설정 스크립트
├── mcp_server.py          # MCP 서버 메인 코드
├── test_connection.py     # 데이터베이스 연결 테스트 스크립트
├── bastion.sh             # SSH 터널링 스크립트 (Unix/Linux/macOS, 자동 생성됨)
├── bastion.ps1            # SSH 터널링 스크립트 (Windows, 자동 생성됨)
├── requirements.txt       # Python 의존성
├── .env_example          # 환경 변수 템플릿
├── .env                  # 환경 변수 설정 (복사해서 생성)
├── .gitignore            # Git 무시 파일 목록
├── .cursor/
│   └── mcp.json          # MCP 서버 설정 (자동 생성됨)
├── pg_mcp.log            # 로그 파일 (실행 시 생성됨)
└── README.md             # 이 파일
```

## 설정 파일

### 환경 변수

MCP 서버는 `.env` 파일에서 다음 환경 변수를 사용합니다:

**데이터베이스 연결:**
- `PGHOST`: PostgreSQL 호스트 (기본값: localhost)
- `PGPORT`: PostgreSQL 포트 (기본값: 10000)
- `PGUSER`: 데이터베이스 사용자 (기본값: postgres)
- `PGPASSWORD`: 데이터베이스 비밀번호
- `PGDATABASE`: 데이터베이스 이름 (기본값: postgres)

**SSH 터널링 설정:**
- `SSH_KEY_FILE`: EC2 키 파일 경로 (파일명만 입력시 ~/.ssh/ 폴더에서 찾음, 절대/상대 경로 지원)
- `SSH_LOCAL_PORT`: 로컬 포트 (기본값: 10000)
- `SSH_RDS_ENDPOINT`: RDS 엔드포인트 주소
- `SSH_RDS_PORT`: RDS 포트 (기본값: 5432)
- `SSH_BASTION_HOST`: Bastion 호스트 정보

**로깅:**
- `LOG_LEVEL`: 로그 레벨 (기본값: INFO)
- `LOG_FILE`: 로그 파일 경로 (기본값: pg_mcp.log)

### 재설정

환경이 변경되거나 경로를 업데이트해야 할 때는 언제든지 다음 명령어를 다시 실행할 수 있습니다:

```bash
uv run setup.py
```

## 수동 설정 (setup.py 실패 시)

자동 설정이 실패하는 경우 다음과 같이 수동으로 설정할 수 있습니다:

### 1. MCP 설정 파일 생성

`.cursor/mcp.json` 파일을 생성하고 다음 내용을 입력합니다:

**Unix/Linux/macOS:**
```json
{
  "mcpServers": {
    "AWS-PostgreSQL": {
      "command": "/절대경로/AWS_PostgreSQL_MCP/.venv/bin/python",
      "args": ["/절대경로/AWS_PostgreSQL_MCP/mcp_server.py"],
      "env": {
        "PGHOST": "localhost",
        "PGPORT": "10000",
        "PGUSER": "postgres", 
        "PGPASSWORD": "your_password_here",
        "PGDATABASE": "postgres",
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "/절대경로/AWS_PostgreSQL_MCP/pg_mcp.log"
      }
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "AWS-PostgreSQL": {
      "command": "C:\\절대경로\\AWS_PostgreSQL_MCP\\.venv\\Scripts\\python.exe",
      "args": ["C:\\절대경로\\AWS_PostgreSQL_MCP\\mcp_server.py"],
      "env": {
        "PGHOST": "localhost",
        "PGPORT": "10000",
        "PGUSER": "postgres", 
        "PGPASSWORD": "your_password_here",
        "PGDATABASE": "postgres",
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "C:\\절대경로\\AWS_PostgreSQL_MCP\\pg_mcp.log"
      }
    }
  }
}
```

**경로 찾기 방법:**

**Unix/Linux/macOS:**
```bash
# 현재 프로젝트의 절대 경로 확인
pwd
# 결과: /Users/username/Documents/GitHub/AWS_PostgreSQL_MCP

# 가상환경 Python 경로 확인
which python
# 가상환경 활성화 후 실행
```

**Windows (PowerShell):**
```powershell
# 현재 프로젝트의 절대 경로 확인
Get-Location
# 결과: C:\Users\username\Documents\GitHub\AWS_PostgreSQL_MCP

# 가상환경 Python 경로 확인
Get-Command python | Select-Object Source
# 가상환경 활성화 후 실행
```

**Windows 경로 사용 시 주의사항:**
- **PowerShell 명령어, .env 파일**: 단일 백슬래시 (`\`) 사용
- **JSON 파일 (mcp.json)**: 이중 백슬래시 (`\\`) 사용 (JSON 이스케이프 규칙)

### 2. Bastion 스크립트 생성

`bastion.sh` 파일을 다음과 같이 생성합니다:

**Unix/Linux/macOS:**
```bash
#!/bin/bash
cd ~/.ssh/
ssh -i your-ec2-key.pem -L 10000:your-rds-endpoint.region.rds.amazonaws.com:5432 ec2-user@your-bastion-ip
```

실행 권한을 부여합니다:
```bash
chmod +x bastion.sh
```

**Windows:**
Windows에서는 `bastion.ps1` PowerShell 스크립트를 사용합니다:

```powershell
# PowerShell 스크립트 실행
powershell -ExecutionPolicy Bypass -File bastion.ps1

# 또는 파이프를 통한 실행
Get-Content bastion.ps1 | powershell

# 또는 직접 SSH 터널링 실행
ssh -i "$env:USERPROFILE\.ssh\your-ec2-key.pem" -L 10000:your-rds-endpoint.region.rds.amazonaws.com:5432 ec2-user@your-bastion-ip
```

**"코드에 접근할 수 없습니다" 오류 발생 시:**
`bastion.ps1` 파일을 메모장으로 열어서 노란색으로 표시된 SSH 명령어를 복사해서 PowerShell에 직접 붙여넣기하세요.

### 3. 디렉토리 생성

필요한 디렉토리가 없다면 생성합니다:

**Unix/Linux/macOS:**
```bash
# .cursor 디렉토리 생성
mkdir -p .cursor

# .ssh 디렉토리 생성 (홈 디렉토리에)
mkdir -p ~/.ssh
```

**Windows (PowerShell):**
```powershell
# .cursor 디렉토리 생성
New-Item -ItemType Directory -Force -Path ".cursor"

# .ssh 디렉토리 생성 (홈 디렉토리에)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh"
```

## 문제 해결

### 연결 오류

**먼저 연결 테스트 스크립트로 확인:**

```bash
# 기본 연결 테스트
python test_connection.py "SELECT 1"

# 연결 정보 확인 (환경 변수 출력 포함)
python test_connection.py "SELECT version()"
```

**연결 테스트 실패 시 확인사항:**

1. **`.env` 파일**: 파일이 존재하고 실제 값으로 설정되어 있는지
2. **비밀번호**: `PGPASSWORD`에 올바른 데이터베이스 비밀번호 설정
3. **SSH 터널링**: bastion 스크립트 실행 및 포트 10000 열림 상태
4. **bastion 호스트**: SSH 연결이 정상적으로 작동하는지
5. **MCP 서버 로그**: 오류 메시지 확인

**상세 확인 명령어:**

**Unix/Linux/macOS:**
```bash
# 포트 확인
lsof -i :10000

# SSH 연결 테스트  
ssh -i ~/.ssh/your-ec2-key.pem ec2-user@your-bastion-ip

# 로그 확인
tail -f pg_mcp.log
```

**Windows (PowerShell):**
```powershell
# 포트 확인
netstat -an | Select-String ":10000"

# SSH 연결 테스트
ssh -i "$env:USERPROFILE\.ssh\your-ec2-key.pem" ec2-user@your-bastion-ip

# 로그 확인
Get-Content pg_mcp.log -Wait -Tail 10
```
   


### 권한 오류

SSH 키 파일의 권한을 확인하세요:

**Unix/Linux/macOS:**
```bash
ls -la ~/.ssh/your-ec2-key.pem
# 결과는 -rw------- 이어야 합니다
```

**Windows (PowerShell):**
```powershell
# 파일 권한 확인
icacls "$env:USERPROFILE\.ssh\your-ec2-key.pem"
# 소유자만 읽기 권한이 있어야 합니다
```

### 환경 초기화

프로젝트를 초기 상태로 되돌리려면:

**Unix/Linux/macOS:**
```bash
# Git으로 추적되지 않는 파일들 제거
git clean -fxd

# 가상환경 재생성
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
# Git으로 추적되지 않는 파일들 제거
git clean -fxd

# 가상환경 재생성
uv venv
.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

## 주요 기능

- **자동 경로 감지**: git clone 위치에 관계없이 자동으로 올바른 경로 설정
- **SSH 터널링**: AWS RDS에 안전한 연결
- **MCP 프로토콜**: Claude 등 AI 모델과의 표준 인터페이스
- **로깅**: 상세한 로그로 디버깅 지원
- **오류 처리**: 연결 실패 시 자동 재시도 및 상세 오류 메시지
- **환경 변수 관리**: `.env` 파일을 통한 안전한 설정 관리

