import os
import sys
import psycopg2

def execute_query(query):
    """
    PostgreSQL에 쿼리를 실행하고 결과를 반환하는 함수
    
    Args:
        query (str): 실행할 SQL 쿼리
        
    Returns:
        list: SELECT 쿼리의 경우 결과 행들의 리스트
        int: INSERT, UPDATE, DELETE 쿼리의 경우 영향받은 행 수
        str: 에러가 발생한 경우 에러 메시지
    """
    try:

        try:
            import dotenv
            dotenv.load_dotenv()
            print("--------------------------------")
            print(".env 파일 내용:")
            print("PGHOST: ", os.getenv('PGHOST'))
            print("PGPORT: ", os.getenv('PGPORT'))
            print("PGUSER: ", os.getenv('PGUSER'))
            print("PGDATABASE: ", os.getenv('PGDATABASE'))
            print("PGPASSWORD: ", os.getenv('PGPASSWORD'))
            print("--------------------------------")
        except:
            pass
        
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '10000'),
            user=os.getenv('PGUSER', 'postgres'),
            password=os.getenv('PGPASSWORD', 'your_password'),
            database=os.getenv('PGDATABASE', 'postgres')
        )
        
        cur = conn.cursor()
        
        # 쿼리 실행
        cur.execute(query)
        
        # 쿼리 타입에 따른 구분 처리
        query_upper = query.strip().upper()
        
        # SELECT 관련 쿼리들 (결과를 fetch해야 하는 쿼리들)
        select_keywords = ['SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'EXPLAIN']
        is_select_query = any(query_upper.startswith(keyword) for keyword in select_keywords)
        
        if is_select_query:
            # SELECT 계열 쿼리의 경우 결과를 가져옴
            try:
                results = cur.fetchall()
                # 컬럼 이름도 함께 반환 (description이 있는 경우에만)
                column_names = []
                if cur.description:
                    column_names = [desc[0] for desc in cur.description]
                
                conn.close()
                return {
                    'type': 'select',
                    'columns': column_names,
                    'rows': results,
                    'row_count': len(results)
                }
            except psycopg2.ProgrammingError:
                # 결과가 없는 쿼리의 경우 (예: EXPLAIN ANALYZE)
                conn.close()
                return {
                    'type': 'select_no_result',
                    'message': '쿼리가 성공적으로 실행되었습니다. (결과 없음)'
                }
        else:
            # INSERT, UPDATE, DELETE, CREATE, DROP 등의 경우
            affected_rows = cur.rowcount
            conn.commit()
            conn.close()
            
            # 쿼리 타입별 메시지 구분
            if query_upper.startswith('INSERT'):
                operation = '삽입'
            elif query_upper.startswith('UPDATE'):
                operation = '수정'
            elif query_upper.startswith('DELETE'):
                operation = '삭제'
            elif query_upper.startswith('CREATE'):
                operation = '생성'
            elif query_upper.startswith('DROP'):
                operation = '삭제'
            elif query_upper.startswith('ALTER'):
                operation = '변경'
            else:
                operation = '실행'
            
            return {
                'type': 'modify',
                'affected_rows': affected_rows,
                'operation': operation,
                'message': f'{operation} 쿼리가 성공적으로 실행되었습니다. {affected_rows}개 행이 영향받았습니다.'
            }
            
    except psycopg2.Error as e:
        return {
            'error': f'데이터베이스 오류: {str(e)}'
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 명령줄 인수로 쿼리가 제공된 경우
        query = " ".join(sys.argv[1:])
        print(f"실행할 쿼리: {query}")
        print("-" * 50)
        
        result = execute_query(query)
        
        if 'error' in result:
            print(f"에러: {result['error']}")
        elif result.get('type') == 'select':
            # SELECT 계열 쿼리 결과 출력
            print(f"\n결과 ({result['row_count']}개 행):")
            if result['columns']:
                print("컬럼:", ", ".join(result['columns']))
                print("-" * 50)
                for row in result['rows']:
                    print(row)
            else:
                print("컬럼 정보가 없습니다.")
                for row in result['rows']:
                    print(row)
        elif result.get('type') == 'select_no_result':
            # 결과가 없는 SELECT 계열 쿼리
            print(result['message'])
        elif result.get('type') == 'modify':
            # INSERT, UPDATE, DELETE 등의 결과 출력
            print(f"[{result['operation']}] {result['message']}")
        else:
            # 기타 경우
            print(result.get('message', '쿼리가 실행되었습니다.'))
    else:
        # 대화형 모드
        print("PostgreSQL 쿼리 실행기")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
        
        while True:
            query = input("\nSQL 쿼리를 입력하세요: ").strip()
            
            if query.lower() in ['quit', 'exit']:
                print("프로그램을 종료합니다.")
                break
                
            if not query:
                print("쿼리를 입력해주세요.")
                continue
                
            result = execute_query(query)
            
            if 'error' in result:
                print(f"에러: {result['error']}")
            elif result.get('type') == 'select':
                # SELECT 계열 쿼리 결과 출력
                print(f"\n결과 ({result['row_count']}개 행):")
                if result['columns']:
                    print("컬럼:", ", ".join(result['columns']))
                    print("-" * 50)
                    for row in result['rows']:
                        print(row)
                else:
                    print("컬럼 정보가 없습니다.")
                    for row in result['rows']:
                        print(row)
            elif result.get('type') == 'select_no_result':
                # 결과가 없는 SELECT 계열 쿼리
                print(result['message'])
            elif result.get('type') == 'modify':
                # INSERT, UPDATE, DELETE 등의 결과 출력
                print(f"[{result['operation']}] {result['message']}")
            else:
                # 기타 경우
                print(result.get('message', '쿼리가 실행되었습니다.'))