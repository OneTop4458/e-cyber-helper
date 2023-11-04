"""
ConfigManager Module
====================

This module provides a ConfigManager class to manage configuration data.
It uses Fernet symmetric encryption to encrypt and decrypt the configuration data,
stored in a YAML file.

Dependencies:
- PyYAML: A library to parse and generate YAML files.
- cryptography: A package designed to expose cryptographic primitives and recipes to Python developers.
- keyring: Provides a way to securely store passwords and other secrets.

Classes:
    ConfigManager: A class to manage configuration data with encryption.

Usage:
    from config_manager import ConfigManager

    # Create a ConfigManager instance
    config_manager = ConfigManager('config.yaml')

    # Update configuration
    config_manager.update_config('username', 'user123')
    config_manager.update_config('password', 'pass456')

    # Load configuration
    config_data = config_manager.load_config()

    # Get a specific configuration value
    config_value = config_manager.get_config('username')

"""

import yaml
import os
import uuid
import sys
import base64
import keyring
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet


class ConfigManager:
    """
    A class to manage configuration data with encryption.

    Attributes:
        config_path (str): The path to the configuration file.
        salt (bytes): The salt value used for key generation, derived from the system's UUID.
        key (bytes): The encryption key.
        fernet (Fernet): The Fernet encryption object.

    Methods:
        __init__(self, config_path, password=None, reset_key=False): Constructor for the class.
        _get_or_create_key(self, password, reset_key): Gets an existing or creates a new encryption key.
        _generate_key(self, password, salt): Generates an encryption key using a password and salt.
        _encrypt(self, data): Encrypts data before saving to the configuration file.
        _decrypt(self, data): Decrypts data loaded from the configuration file.
        load_config(self): Loads and decrypts configuration data from the file.
        save_config(self, config_data): Encrypts and saves the configuration data to the file.
        update_config(self, key, value): Updates a configuration key with a new value in the file.
        get_config(self, key): Retrieves a configuration value by key from the file.
    """

    def __init__(self, config_path, password=None, reset_key=False):
        """
        Initializes a new ConfigManager instance.

        Args:
            config_path (str): Path to the YAML configuration file.
            password (str, optional): Password to generate the encryption key.
                                      If not provided, a default password may be used.
            reset_key (bool, optional): Whether to reset (regenerate) the encryption key.

        Returns:
            None
        """
        self.config_path = config_path
        self.salt = uuid.UUID(int=uuid.getnode()).bytes  # PC의 UUID를 사용하여 Salt 생성
        self.key = self._get_or_create_key(password, reset_key)  # reset_key 인자를 _get_or_create_key 메서드에 전달
        self.fernet = Fernet(self.key)

    def _get_or_create_key(self, password, reset_key):
        """
        Retrieves an existing encryption key from the keyring or creates a new one.

        Args:
            password (str): The password to generate the encryption key.
            reset_key (bool): If true, forces the creation of a new key.

        Returns:
            bytes: The generated or retrieved Fernet encryption key.
        """
        existing_key = keyring.get_password("your_system", "encryption_key")
        if existing_key and not reset_key:  # reset_key가 False이고 키가 존재하는 경우 기존 키 사용
            print("Using existing key.")
            return existing_key.encode()
        # 새 키를 생성하고 저장 (reset_key가 True이거나 키가 존재하지 않는 경우)
        print("Creating and storing a new key.")
        new_key = self._generate_key(password, self.salt)
        keyring.set_password("your_system", "encryption_key", new_key.decode())
        return new_key

    def _generate_key(self, password, salt):
        """
        Generates a Fernet encryption key using a password and a salt.

        Args:
            password (str): The password to use in the key derivation function.
            salt (bytes): A sequence of bytes used as salt in the key derivation function.

        Returns:
            bytes: The derived Fernet encryption key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))  # 비밀번호와 Salt를 사용하여 키 생성
        return key

    def _encrypt(self, data):
        """
        Encrypts the provided data using Fernet encryption.

        Args:
            data (str, dict, list): The data to be encrypted. Can be a string,
                                    dictionary, or list to be converted to a YAML string.

        Returns:
            str: The encrypted string or the original data if encryption fails.
        """
        try:
            if isinstance(data, (dict, list)):
                data = yaml.dump(data)  # Convert dict or list to YAML string
            elif isinstance(data, (str, int)):
                data = str(data)  # Ensure data is a string
            else:
                raise ValueError(f'Unsupported data type: {type(data)}')

            if self.fernet:
                return self.fernet.encrypt(data.encode()).decode()
        except Exception as e:
            sys.stderr.write(f'Encryption failed: {e}\n')
        return data

    def _decrypt(self, data):
        """
        Decrypts the provided data using Fernet encryption.

        Args:
            data (str): The encrypted data string to be decrypted.

        Returns:
            str, dict, list: The decrypted data, which can be a string,
                             dictionary, or list depending on the original data type.
        """
        try:
            if self.fernet:
                decrypted_data = self.fernet.decrypt(data.encode()).decode()
                try:
                    return yaml.safe_load(decrypted_data)  # Attempt to convert YAML string to dict or list
                except yaml.YAMLError:
                    return decrypted_data  # If not a YAML string, return the decrypted string as-is
        except Exception as e:
            sys.stderr.write(f'Decryption failed: {e}\n')
        return data

    def load_config(self):
        """
        Loads and decrypts the configuration data from the YAML file.

        Returns:
            dict: The decrypted configuration data as a dictionary.
        """
        if not os.path.exists(self.config_path):
            return {}
        try:
            with open(self.config_path, 'r') as file:
                config_data = yaml.safe_load(file)
                if config_data is None:
                    return {}  # 파일이 비어 있는 경우 빈 딕셔너리 반환
                decrypted_data = {key: self._decrypt(str(value)) for key, value in config_data.items()}
                return {key: yaml.safe_load(value) if isinstance(value, str) else value for key, value in decrypted_data.items()}
        except Exception as e:
            sys.stderr.write(f'Failed to load config: {e}\n')
            return {}

    def save_config(self, config_data):
        """
        Encrypts and saves the provided configuration data to the YAML file.

        Args:
            config_data (dict): The configuration data to encrypt and save.

        Returns:
            None
        """
        try:
            existing_data = self.load_config()
            merged_data = {**existing_data, **config_data}
            str_data = {key: yaml.dump(value) if isinstance(value, (dict, list)) else str(value) for key, value in merged_data.items()}
            encrypted_data = {key: self._encrypt(value) for key, value in str_data.items()}
            with open(self.config_path, 'w') as file:
                yaml.safe_dump(encrypted_data, file)
        except Exception as e:
            sys.stderr.write(f'Failed to save config: {e}\n')

    def update_config(self, key, value):
        """
        Updates a configuration key with a new value in the YAML file.

        Args:
            key (str): The key in the configuration data to update.
            value: The new value to set for the key.

        Returns:
            None
        """
        config_data = self.load_config()
        config_data[key] = value
        self.save_config(config_data)

    def get_config(self, key):
        """
        Retrieves a specific configuration value by key from the YAML file.

        Args:
            key (str): The key whose value is to be retrieved.

        Returns:
            The value associated with the key, or None if the key is not found.
        """
        config_data = self.load_config()
        return config_data.get(key, None)  # 키가 없는 경우 None 반환
