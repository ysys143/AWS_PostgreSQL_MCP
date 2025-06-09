#!/usr/bin/env python3
"""PostgreSQL MCP Server"""

import os
import logging
import subprocess
import time
import socket
from typing import Dict, Any
import psycopg2
from fastmcp import FastMCP

# Logging setup
def setup_logger(name: str, log_file: str = "pg_mcp.log"):
    """Setup logger with console and file handlers"""
    logger = logging.getLogger(name)
    log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper())
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
        
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with safe path handling
    # 로그 파일 경로가 절대 경로가 아니라면 현재 작업 디렉토리 기준으로 설정
    if not os.path.isabs(log_file):
        log_file = os.path.join(os.getcwd(), log_file)
    
    # 루트 디렉토리에 직접 쓰기 방지
    if log_file.startswith('/') and log_file.count('/') == 1:
        log_file = os.path.join(os.getcwd(), os.path.basename(log_file))
        logger.warning(f"Prevented writing to root directory, using: {log_file}")
    
    # 로그 파일 디렉토리가 없으면 생성
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # 파일 핸들러 생성 실패 시 콘솔에만 로그 출력
        logger.warning(f"Failed to create log file handler for {log_file}: {e}")
        logger.warning("Continuing with console logging only")
    
    return logger

# 안전한 디폴트 로그 파일 경로 사용
logger = setup_logger("pg_mcp", os.getenv('LOG_FILE', './pg_mcp.log'))

# Bastion management functions
def is_port_open(host: str = "localhost", port: int = 10000) -> bool:
    """Check if bastion port is open"""
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except (socket.error, ConnectionRefusedError):
        return False

def check_bastion_requirements() -> Dict[str, Any]:
    """Check bastion script and SSH key requirements"""
    issues = []
    bastion_script = "bastion.sh"
    
    # Check bastion script exists
    if not os.path.exists(bastion_script):
        issues.append(f"Bastion script '{bastion_script}' not found")
        return {"valid": False, "issues": issues}
    
    # Read and parse bastion script
    try:
        with open(bastion_script, 'r') as f:
            content = f.read()
        
        # Extract SSH key path from script
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        ssh_line = None
        for line in lines:
            if 'ssh -i' in line:
                ssh_line = line
                break
        
        if not ssh_line:
            issues.append("No SSH command found in bastion script")
            return {"valid": False, "issues": issues}
        
        # Extract key file path
        import re
        key_match = re.search(r'-i\s+([^\s]+)', ssh_line)
        if key_match:
            key_path = key_match.group(1)
            
            # Check if key path is relative to .ssh directory
            if not key_path.startswith('/') and not key_path.startswith('.ssh/'):
                key_path = f".ssh/{key_path}"
            
            # Check key file exists
            if not os.path.exists(key_path):
                issues.append(f"SSH key file not found: {key_path}")
            else:
                # Check key file permissions
                import stat
                key_stat = os.stat(key_path)
                if key_stat.st_mode & 0o077:
                    issues.append(f"SSH key file has unsafe permissions: {key_path} (should be 600)")
        else:
            issues.append("SSH key path not found in bastion script")
        
        # Check .ssh directory exists
        ssh_dir = ".ssh"
        if not os.path.exists(ssh_dir):
            issues.append(f"SSH directory not found: {ssh_dir}")
        
    except Exception as e:
        issues.append(f"Error reading bastion script: {e}")
    
    return {"valid": len(issues) == 0, "issues": issues}

def start_bastion() -> bool:
    """Start bastion connection with detailed error checking"""
    # Check requirements first
    check_result = check_bastion_requirements()
    if not check_result["valid"]:
        for issue in check_result["issues"]:
            logger.error(f"Bastion requirement check failed: {issue}")
        return False
    
    try:
        logger.info("Starting bastion connection...")
        
        # Start bastion process in background
        bastion_process = subprocess.Popen(
            ['bash', 'bastion.sh'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            cwd=os.getcwd(),
            start_new_session=True  # Independent process group
        )
        
        # Wait for connection to establish
        for i in range(15):  # Increased timeout to 15 seconds
            time.sleep(1)
            if is_port_open():
                logger.info("Bastion connection established successfully")
                logger.info("Note: Bastion will continue running independently when MCP server stops")
                return True
            
            # Check if process died
            if bastion_process.poll() is not None:
                stdout, stderr = bastion_process.communicate()
                logger.error(f"Bastion process terminated unexpectedly")
                if stderr:
                    logger.error(f"Bastion stderr: {stderr.decode().strip()}")
                if stdout:
                    logger.debug(f"Bastion stdout: {stdout.decode().strip()}")
                return False
                
            logger.debug(f"Waiting for bastion connection... ({i+1}/15)")
                
        logger.error("Bastion connection failed to establish within 15 seconds")
        
        # Check process status
        if bastion_process.poll() is None:
            logger.warning("Bastion process is running but port is not accessible")
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to start bastion: {e}")
        return False

def ensure_bastion_connection() -> bool:
    """Ensure bastion connection is active"""
    if is_port_open():
        logger.info("Bastion connection already active (running independently)")
        return True
        
    logger.info("Bastion connection not detected, attempting to start...")
    return start_bastion()

# PostgreSQL execution functions
def get_connection_params() -> Dict[str, str]:
    """Get PostgreSQL connection parameters"""
    return {
        'host': os.getenv('PGHOST', 'localhost'),
        'port': os.getenv('PGPORT', '10000'),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', ''),
        'database': os.getenv('PGDATABASE', 'postgres')
    }

def get_operation_type(query: str) -> str:
    """Get operation type from query"""
    ops = {'INSERT': 'Insert', 'UPDATE': 'Update', 'DELETE': 'Delete', 'CREATE': 'Create', 'DROP': 'Drop', 'ALTER': 'Alter'}
    return next((op for kw, op in ops.items() if query.startswith(kw)), 'Execute')

def execute_postgresql_query(query: str) -> Dict[str, Any]:
    """Execute PostgreSQL query and return results"""
    SELECT_KEYWORDS = ['SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'EXPLAIN']
    
    if not query.strip():
        return {"success": False, "error": "Empty query"}
    
    # Ensure bastion connection before executing query
    if not ensure_bastion_connection():
        return {"success": False, "error": "Failed to establish bastion connection"}
    
    logger.info(f"Executing query: {query[:100]}...")
    
    try:
        conn_params = get_connection_params()
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                
                if any(query.strip().upper().startswith(kw) for kw in SELECT_KEYWORDS):
                    try:
                        rows = cur.fetchall()
                        columns = [desc[0] for desc in cur.description] if cur.description else []
                        result = {"success": True, "type": "select", "columns": columns, "rows": rows, "row_count": len(rows)}
                    except psycopg2.ProgrammingError:
                        result = {"success": True, "type": "select_no_result", "message": "Query executed successfully (no results)"}
                else:
                    conn.commit()
                    operation = get_operation_type(query.strip().upper())
                    result = {
                        "success": True, 
                        "type": "modify", 
                        "affected_rows": cur.rowcount,
                        "operation": operation,
                        "message": f"{operation} completed: {cur.rowcount} rows affected"
                    }
                
                logger.info(f"Execution successful: {result['type']}")
                return result
                
    except Exception as e:
        error_msg = f"Execution failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

# MCP Server setup
mcp = FastMCP("PostgreSQL Server")

# Tool definition - must be after mcp instance creation
@mcp.tool
def execute_query(query: str) -> str:
    """Execute PostgreSQL query
    
    Args:
        query: SQL query string
        
    Returns:
        Query execution result as formatted string
    """
    result = execute_postgresql_query(query)
    
    if not result["success"]:
        return f"Error: {result['error']}"
    
    if result["type"] == "select":
        if result["row_count"] == 0:
            return "Query executed successfully but returned no rows."
        
        # Format results as a table
        lines = []
        lines.append(f"Query returned {result['row_count']} rows:")
        lines.append("-" * 50)
        lines.append(" | ".join(result["columns"]))
        lines.append("-" * 50)
        
        for row in result["rows"]:
            lines.append(" | ".join(str(val) for val in row))
        
        return "\n".join(lines)
    
    elif result["type"] == "modify":
        return f"{result['operation']} completed successfully. {result['affected_rows']} rows affected."
    
    else:
        return result.get("message", "Query executed successfully.")

def main():
    """Main function to run MCP server"""
    logger.info("MCP server initialized")
    logger.info(f"Server name: {mcp.name}")
    
    # Debug: Check registered tools
    if hasattr(mcp._tool_manager, '_tools'):
        logger.info(f"Registered tools: {list(mcp._tool_manager._tools.keys())}")
        logger.info(f"Total tools: {len(mcp._tool_manager._tools)}")
    
    logger.info("Starting MCP server")
    logger.info("Bastion connections will be managed automatically and run independently")
    
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        raise

if __name__ == "__main__":
    main() 