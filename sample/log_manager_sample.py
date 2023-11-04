"""
LogManager Sample Usage
==========================

This is a sample usage of the LogManager module.

"""
import sys

from cryptography.fernet import Fernet
from common.config_manager import ConfigManager
from common.log_manager import LogManager

# 암호화 키 생성 (이 키는 안전하게 저장되어야 함) | 최초 1회만 이 후에는 자동으로 저장된 키를 계속 사용 함
encryption_key = Fernet.generate_key().decode()
print(encryption_key)

# ConfigManager 인스턴스 생성
config_manager = ConfigManager('config.yaml', encryption_key, False)

# 설정 업데이트
config_manager.update_config('username', 'user123')
config_manager.update_config('password', 'pass456')

# 전체 설정 로드
config_data = config_manager.load_config()
print(config_data)

# 특정 설정 값 가져오기
config_value = config_manager.get_config('username')
print(config_value)

# LogManager 인스턴스 생성
log_manager = LogManager(config_manager)

# 로거 가져오기
logger = log_manager.get_logger('sample_logger')

# 로깅 예시
logger.info('This is an informational message.')
logger.debug('This is an debug message.')
logger.critical('This is an critical message.')
logger.warning('This is an warning message.')
logger.error('This is an error message.')

try:
    raise ValueError('This is a test error.')
except Exception as e:
    exc_info = sys.exc_info()
    log_manager.log_exception(exc_info)  # dump_file_name 매개변수 전달

