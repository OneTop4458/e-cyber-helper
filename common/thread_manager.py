"""
ThreadManager Module
====================

This module provides a ThreadManager class to manage threads.
It allows for creating, starting, and safely stopping threads.

Dependencies:
- threading: A module that constructs higher-level threading interfaces on top of the lower level _thread module.

Classes:
    ThreadManager: A class to manage threads.

Usage:
    from thread_manager import ThreadManager

    # Create a ThreadManager instance
    thread_manager = ThreadManager()

    # Create and start a thread
    thread_id = thread_manager.create_thread(target_function, args=(arg1, arg2), name=thread_name)

    # Stop a specific thread
    thread_manager.stop_thread(thread_id)
"""
import threading
import uuid
import sys

class ThreadManager:
    """
    ThreadManager Class
    ===================

    This class manages threads, allowing for thread creation, execution, and safe termination.

    Attributes:
        threads (dict): A dictionary storing threads with their unique IDs.
        stop_signals (dict): A dictionary storing threading.Event instances to signal thread termination.

    Methods:
        create_thread(self, target, args=(), name=None): Creates a new thread with a unique ID and optional name.
        start_thread(self, thread_id): Starts a thread given its unique ID.
        stop_thread(self, thread_id): Stops a thread and removes it from the manager.
        stop_all_threads(self): Stops all threads managed by the instance.
    """

    def __init__(self):
        self.threads = {}
        self.stop_signals = {}

    def create_thread(self, target, args=(), name=None):
        """
        Creates a new thread with a unique ID and an optional name.

        Args:
            target (callable): The function that the thread will execute.
            args (tuple): The arguments to pass to the target function.
            name (str, optional): The name of the thread for identification.

        Returns:
            str: A unique ID for the created thread.
        """
        thread_id = str(uuid.uuid4())
        stop_signal = threading.Event()  # Thread stop signal
        thread = threading.Thread(target=target, args=args + (stop_signal,), name=name)
        self.threads[thread_id] = thread
        self.stop_signals[thread_id] = stop_signal
        return thread_id

    def start_thread(self, thread_id):
        """
        Starts a thread given its unique ID.

        Args:
            thread_id (str): The unique ID of the thread to start.

        Returns:
            None
        """
        thread = self.threads.get(thread_id)
        if thread:
            try:
                thread.start()
            except Exception as e:
                sys.stderr.write(f"Error starting thread {thread_id}: {e}\n")

    def stop_thread(self, thread_id):
        """
        Stops a thread given its unique ID and removes it from the manager.

        Args:
            thread_id (str): The unique ID of the thread to stop.

        Returns:
            None
        """
        stop_signal = self.stop_signals.pop(thread_id, None)
        thread = self.threads.pop(thread_id, None)
        if stop_signal and thread:
            stop_signal.set()  # Signal the thread to stop
            thread.join()  # Wait for the thread to finish

    def stop_all_threads(self):
        """
        Stops all threads managed by the instance.

        Returns:
            None
        """
        for thread_id in list(self.threads.keys()):
            self.stop_thread(thread_id)