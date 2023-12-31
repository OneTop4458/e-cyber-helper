import sys
import time

from common.config_manager import ConfigManager
from common.log_manager import LogManager
from common.sqlite_manager import SQLiteManager
from common.thread_manager import ThreadManager

from cryptography.fernet import Fernet


def test_function(arg1, arg2, stop_signal):
    """
    A target function for threads managed by ThreadManager.

    Args:
        arg1: First argument for demonstration purposes.
        arg2: Second argument for demonstration purposes.
        stop_signal (threading.Event): A signal for stopping the thread.

    Returns:
        None
    """
    try:
        while not stop_signal.is_set():
            logger.info(f"Thread with arguments {arg1} and {arg2} is running.")
            time.sleep(1)
            if stop_signal.is_set():
                logger.info(f"Thread with arguments {arg1} and {arg2} received stop signal.")
                break
    except Exception as e:
        sys.stderr.write(f"Error in thread with arguments {arg1} and {arg2}: {e}\n")


def sample_usage():
    # 스레드 매니저 생성
    thread_manager = ThreadManager()

    # 여러 스레드 생성 및 시작
    thread_ids = []
    for i in range(5):  # 5개의 스레드 생성
        thread_name = f"Worker-{i}"  # 스레드에 이름 지정
        tid = thread_manager.create_thread(test_function, args=(f"Hello-{i}", f"World-{i}"), name=thread_name)
        thread_ids.append(tid)
        thread_manager.start_thread(tid)

    # 일정 시간 작업을 수행하고...
    time.sleep(5)

    # 각각의 스레드 중지
    for tid in thread_ids:
        thread_manager.stop_thread(tid)

    # 혹은 모든 스레드 중지
    thread_manager.stop_all_threads()


if __name__ == '__main__':
    # 암호화 키 생성 (이 키는 안전하게 저장되어야 함) | 최초 1회만 이 후에는 자동으로 저장된 키를 계속 사용 함
    encryption_key = Fernet.generate_key().decode()

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

    sample_usage()