"""
ThreadManager Sample Usage
==========================

This is a sample usage of the ThreadManager module.

"""
import sys
import time
from common.thread_manager import ThreadManager


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
            print(f"Thread with arguments {arg1} and {arg2} is running. \n")
            time.sleep(1)
            if stop_signal.is_set():
                print(f"Thread with arguments {arg1} and {arg2} received stop signal. \n")
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
    time.sleep(10)

    # 각각의 스레드 중지
    for tid in thread_ids:
        thread_manager.stop_thread(tid)

    # 혹은 모든 스레드 중지
    thread_manager.stop_all_threads()


if __name__ == "__main__":
    sample_usage()
