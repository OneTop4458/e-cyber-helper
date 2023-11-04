"""
SQLiteManager Sample Usage
==========================

This is a sample usage of the SQLiteManager module.

"""
from common.sqlite_manager import SQLiteManager

# SQLiteManager 인스턴스 생성
# 여기서 'example.db'는 SQLite 데이터베이스 파일의 경로입니다.
# 필요하다면 encryption_key에 적절한 암호화 키를 제공하세요.
encryption_key = "your-encryption-key-here"  # Replace with your actual encryption key
db_manager = SQLiteManager('my_encrypted_database.db', encryption_key=encryption_key)


# 테이블 생성을 위한 컬럼 정의
columns = {
    'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
    'name': 'TEXT NOT NULL',
    'email': 'TEXT',
    'age': 'INTEGER'
}

# 'users' 테이블 생성
db_manager.create_table('users', columns)

# 'users' 테이블에 데이터 삽입
user_data = {
    'name': 'John Doe',
    'email': 'john.doe@example.com',
    'age': 30
}
db_manager.insert_data('users', user_data)

# 'users' 테이블에서 모든 데이터 조회
all_users = db_manager.get_data('users')
print('All Users:', all_users)

# 특정 조건에 맞는 데이터 조회
specific_user = db_manager.get_data('users', conditions={'name': 'John Doe'})
print('Specific User:', specific_user)

# 데이터 업데이트
db_manager.update_data('users', data={'email': 'new.email@example.com'}, conditions={'name': 'John Doe'})

# 업데이트된 데이터 확인
updated_user = db_manager.get_data('users', conditions={'name': 'John Doe'})
print('Updated User:', updated_user)

# 데이터 삭제
db_manager.delete_data('users', conditions={'name': 'John Doe'})

# 삭제 후 데이터 확인
users_after_deletion = db_manager.get_data('users')
print('Users after deletion:', users_after_deletion)
