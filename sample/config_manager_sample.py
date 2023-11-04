"""
ConfigManager Sample Usage
==========================

This is a sample usage of the ConfigManager module.

"""

from cryptography.fernet import Fernet
from common.config_manager import ConfigManager

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