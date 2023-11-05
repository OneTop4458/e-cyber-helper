"""
ThreadManager Module
====================

This module provides the ThreadManager class to manage and handle the life cycle of threads in a Python application.
The class offers functionality to create, start, and safely stop threads using unique thread IDs.

Features:
- Create threads with a unique identifier and an optional name.
- Start and stop threads safely with proper cleanup.
- Ability to stop all threads managed by the ThreadManager instance.

Dependencies:
- threading: Utilizes the high-level threading API for creating and managing threads.
- uuid: Generates unique identifiers for each thread.
- sys: Used to handle exceptions and output errors.

Classes:
    ThreadManager: A class to encapsulate thread management logic.

Usage:
    # Import the ThreadManager class
    from thread_manager import ThreadManager

    # Instantiate the ThreadManager
    thread_manager = ThreadManager()

    # Define a target function for the thread
    def target_function(arg1, arg2, stop_signal):
        ...

    # Create a new thread and retrieve its unique ID
    thread_id = thread_manager.create_thread(target_function, args=(arg1, arg2), name="MyThread")

    # Start the thread using its unique ID
    thread_manager.start_thread(thread_id)

    # Perform other operations...
    ...

    # Stop the thread using its unique ID when it's no longer needed
    thread_manager.stop_thread(thread_id)

    # Alternatively, stop all threads managed by the ThreadManager
    thread_manager.stop_all_threads()
"""

import threading
import uuid
import sys


class ThreadManager:
    """Manages threads for creating, executing, and safe termination.

    This class provides methods to manage threads including creating, starting,
    and safely stopping threads. It uses a threading.Event to signal threads to
    stop and a threading.Lock to ensure thread-safe manipulation of the internal
    data structures.

    Attributes:
        threads (dict): A dictionary storing threads with their unique IDs.
        stop_signals (dict): A dictionary storing threading.Event instances to signal thread termination.
        lock (threading.Lock): A lock to prevent concurrent access to threads and stop_signals.
    """

    def __init__(self):
        """Initializes the thread manager with empty threads and stop_signals dictionaries."""
        self.threads = {}
        self.stop_signals = {}
        self.lock = threading.Lock()

    def create_thread(self, target, args=(), kwargs=None, name=None):
        """Creates a new thread with a unique ID.

        Args:
            target (callable): The function that the thread will execute.
            args (tuple): The arguments to pass to the target function.
            kwargs (dict): The keyword arguments to pass to the target function.
            name (str): An optional name for the thread.

        Returns:
            str: A unique ID for the created thread.
        """
        if kwargs is None:
            kwargs = {}
        thread_id = str(uuid.uuid4())
        stop_signal = threading.Event()
        kwargs['stop_signal'] = stop_signal
        thread = threading.Thread(target=target, args=args, kwargs=kwargs, name=name)
        with self.lock:
            self.threads[thread_id] = thread
            self.stop_signals[thread_id] = stop_signal
        return thread_id

    def start_thread(self, thread_id):
        """Starts a thread given its unique ID.

        Args:
            thread_id (str): The unique ID of the thread to start.
        """
        with self.lock:
            thread = self.threads.get(thread_id)
            if thread:
                try:
                    thread.start()
                except Exception as e:
                    sys.stderr.write(f"Error starting thread {thread_id}: {e}\n")

    def stop_thread(self, thread_id, timeout=None):
        """Stops a thread given its unique ID.

        Args:
            thread_id (str): The unique ID of the thread to stop.
            timeout (float): The maximum time to wait for the thread to stop.
        """
        with self.lock:
            stop_signal = self.stop_signals.pop(thread_id, None)
            thread = self.threads.pop(thread_id, None)

        if stop_signal and thread:
            stop_signal.set()
            thread.join(timeout)

            if thread.is_alive():
                sys.stderr.write(f"Warning: thread {thread_id} did not terminate in the expected time.\n")

    def stop_all_threads(self, timeout_per_thread=None):
        """Stops all threads managed by the instance.

        Args:
            timeout_per_thread (float): The maximum time to wait for each thread to stop.
        """
        with self.lock:
            thread_ids = list(self.threads.keys())

        for thread_id in thread_ids:
            self.stop_thread(thread_id, timeout=timeout_per_thread)
