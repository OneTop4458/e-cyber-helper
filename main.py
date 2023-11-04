import sys

from common.config_manager import ConfigManager
from common.log_manager import LogManager
from common.sqlite_manager import SQLiteManager
from cryptography.fernet import Fernet

if __name__ == '__main__':
    # 암호화 키 생성 (이 키는 안전하게 저장되어야 함) | 최초 1회만 이 후에는 자동으로 저장된 키를 계속 사용 함
    encryption_key = Fernet.generate_key().decode()
    print(encryption_key)

    # ConfigManager 인스턴스 생성
    config_manager = ConfigManager('config.yaml', encryption_key, False)

    # LogManager 인스턴스 생성
    log_manager = LogManager(config_manager)

    # DBManager 인스턴스 생성
    db_manager = SQLiteManager('e_cyber_helper.db', encryption_key=encryption_key)

    # 전체 설정 로드
    config_data = config_manager.load_config()
    print(config_data)

    # 로거 가져오기
    logger = log_manager.get_logger('main_thread_logger')

    logger.info('start up program')

