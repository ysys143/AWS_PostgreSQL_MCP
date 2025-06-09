# PostgreSQL MCP Server

AWS RDS PostgreSQL 데이터베이스에 SSH 터널링을 통해 연결하는 MCP (Model Context Protocol) 서버입니다.

## 프로젝트 개요

이 프로젝트는 Cursor Agent가 PostgreSQL 데이터베이스에 직접 쿼리를 실행할 수 있도록 하는 MCP 서버를 제공합니다. AWS RDS 인스턴스에 SSH bastion 호스트를 통해 안전하게 연결됩니다. 공식 Postgres MCP와 같이 Node.js를 이용하는 경우, bastion 호스트를 거치는 과정에서 잘못된 주소로 요청을 보내는 오류가 발생할 수 있습니다.Python Psycopg를 이용하면 오류가 발생하지 않습니다.

## 사전 요구사항

- Python 3.8 이상
- uv (Python 패키지 관리자)
- git
- SSH 클라이언트
- AWS EC2 키 페어 (`your-ec2-key.pem`)

## 설치 및 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd pg_mcp
```

### 2. 가상환경 생성 및 활성화

```bash
# uv를 사용한 가상환경 생성
uv venv

# 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate

# 가상환경 활성화 (Windows)
# .venv\Scripts\activate
```

### 3. 의존성 설치

```bash
uv pip install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
cp .env_example .env
```

필요에 따라 `.env` 파일을 편집하여 데이터베이스 연결 정보를 수정할 수 있습니다:

```bash
# .env 파일 내용 예시
PGPASSWORD='your_password_here'
PGHOST='localhost'
PGPORT='10000'
PGUSER='postgres'
PGDATABASE='postgres'
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
- `bastion.sh` 스크립트 업데이트
- 모든 경로를 현재 환경에 맞게 자동 설정

### 6. SSH 키 설정

AWS EC2 키 파일을 홈 디렉토리의 `.ssh` 폴더에 배치합니다:

```bash
# SSH 디렉토리 생성 (없는 경우)
mkdir -p ~/.ssh

# 키 파일 복사 및 권한 설정
cp your-ec2-key.pem ~/.ssh/
chmod 600 ~/.ssh/your-ec2-key.pem
```

## 사용법

### 1. SSH 터널링 연결

```bash
# bastion 호스트를 통한 터널링 시작
bash bastion.sh
```

이 명령어는 백그라운드에서 실행되며, 로컬 포트 10000을 통해 RDS 인스턴스에 연결합니다.

### 2. MCP 서버 연결

Cursor IDE에서:
1. MCP 서버 설정 새로고침
2. `AWS-PostgreSQL` 서버 연결 확인
3. 연결 상태가 정상인지 확인

### 3. 데이터베이스 쿼리 실행

MCP 서버가 연결되면 AI 모델에게 다음과 같이 요청할 수 있습니다:

```
PostgreSQL 데이터베이스에서 모든 테이블 목록을 조회해주세요.
```

## 프로젝트 구조

```
pg_mcp/
├── setup.py              # 자동 설정 스크립트
├── mcp_server.py          # MCP 서버 메인 코드
├── bastion.sh             # SSH 터널링 스크립트 (자동 생성됨)
├── requirements.txt       # Python 의존성
├── .env_example          # 환경 변수 템플릿
├── .env                  # 환경 변수 설정 (복사해서 생성)
├── .cursor/
│   └── mcp.json          # MCP 서버 설정 (자동 생성됨)
├── pg_mcp.log            # 로그 파일
└── README.md             # 이 파일
```

## 설정 파일

### 환경 변수

MCP 서버는 다음 환경 변수를 사용합니다:

- `PGHOST`: PostgreSQL 호스트 (기본값: localhost)
- `PGPORT`: PostgreSQL 포트 (기본값: 10000)
- `PGUSER`: 데이터베이스 사용자 (기본값: postgres)
- `PGPASSWORD`: 데이터베이스 비밀번호
- `PGDATABASE`: 데이터베이스 이름 (기본값: postgres)
- `LOG_LEVEL`: 로그 레벨 (기본값: INFO)
- `LOG_FILE`: 로그 파일 경로 (기본값: ./pg_mcp.log)

### 재설정

환경이 변경되거나 경로를 업데이트해야 할 때는 언제든지 다음 명령어를 다시 실행할 수 있습니다:

```bash
uv run setup.py
```

## 수동 설정 (setup.py 실패 시)

자동 설정이 실패하는 경우 다음과 같이 수동으로 설정할 수 있습니다:

### 1. MCP 설정 파일 생성

`.cursor/mcp.json` 파일을 생성하고 다음 내용을 입력합니다:

```json
{
  "mcpServers": {
    "AWS-PostgreSQL": {
      "command": "/절대경로/pg_mcp/.venv/bin/python",
      "args": ["/절대경로/pg_mcp/mcp_server.py"],
      "env": {
        "PGHOST": "localhost",
        "PGPORT": "10000",
        "PGUSER": "postgres", 
        "PGPASSWORD": "your_password_here",
        "PGDATABASE": "postgres",
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "/절대경로/pg_mcp/pg_mcp.log"
      }
    }
  }
}
```

**경로 찾기 방법:**
```bash
# 현재 프로젝트의 절대 경로 확인
pwd
# 결과: /Users/username/Documents/GitHub/pg_mcp

# 가상환경 Python 경로 확인
which python
# 가상환경 활성화 후 실행
```

### 2. Bastion 스크립트 수정

`bastion.sh` 파일을 다음과 같이 수정합니다:

```bash
#!/bin/bash
cd ~/.ssh/
ssh -i your-ec2-key.pem -L 10000:your-rds-endpoint.region.rds.amazonaws.com:5432 ec2-user@your-bastion-ip
```

실행 권한을 부여합니다:
```bash
chmod +x bastion.sh
```

### 3. 디렉토리 생성

필요한 디렉토리가 없다면 생성합니다:

```bash
# .cursor 디렉토리 생성
mkdir -p .cursor

# .ssh 디렉토리 생성 (홈 디렉토리에)
mkdir -p ~/.ssh
```

## 문제 해결

### 연결 오류

1. **SSH 터널링 확인**:
   ```bash
   # 포트 10000이 열려있는지 확인
   lsof -i :10000
   ```

2. **bastion 호스트 연결 확인**:
   ```bash
   # SSH 연결 테스트
   ssh -i ~/.ssh/your-ec2-key.pem ec2-user@your-bastion-ip
   ```

3. **MCP 서버 로그 확인**:
   ```bash
   tail -f pg_mcp.log
   ```

### 권한 오류

SSH 키 파일의 권한을 확인하세요:

```bash
ls -la ~/.ssh/your-ec2-key.pem
# 결과는 -rw------- 이어야 합니다
```

## 주요 기능

- **자동 경로 감지**: git clone 위치에 관계없이 자동으로 올바른 경로 설정
- **SSH 터널링**: AWS RDS에 안전한 연결
- **MCP 프로토콜**: Claude 등 AI 모델과의 표준 인터페이스
- **로깅**: 상세한 로그로 디버깅 지원
- **오류 처리**: 연결 실패 시 자동 재시도 및 상세 오류 메시지

