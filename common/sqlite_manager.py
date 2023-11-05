"""
SQLiteManager Module
====================

This module provides a SQLiteManager class to handle operations on an SQLite database.
It supports basic CRUD (Create, Read, Update, Delete) operations and can optionally handle
encryption and decryption of data if an encryption key is provided.

Dependencies:
- sqlite3 (built-in)
- base64 (built-in)
- sys (built-in)

Classes:
    SQLiteManager: A class for managing an SQLite database and performing encrypted data operations.

Usage:
    from sqlite_manager import SQLiteManager

    # Initialize the SQLiteManager with the path to the database and an optional encryption key
    db_manager = SQLiteManager('/path/to/database.db', encryption_key='my-encryption-key')

    # Create a new table
    db_manager.create_table('users', {'id': 'INTEGER PRIMARY KEY', 'username': 'TEXT', 'password': 'TEXT'})

    # Insert data into the table
    db_manager.insert_data('users', {'username': 'johndoe', 'password': 's3cr3t'})

    # Retrieve data from the table
    user_data = db_manager.get_data('users')

    # Update data in the table
    db_manager.update_data('users', {'password': 'newpassword'}, {'username': 'johndoe'})

    # Delete data from the table
    db_manager.delete_data('users', {'username': 'johndoe'})

"""
import sqlite3
import base64
import sys

from common.config_manager import ConfigManager


class SQLiteManager:
    """
    This class is designed to handle interactions with an SQLite database. It provides
    functionality to create tables, and perform insert, update, delete, and select operations.
    If an encryption key is provided, it can also handle the encryption and decryption of data.
    """

    def __init__(self, db_path, encryption_key=None):
        """
        Initializes the SQLiteManager with a path to the SQLite database file and an optional
        encryption key for encrypting and decrypting the data stored in the database.

        Args:
            db_path (str): The file path to the SQLite database.
            encryption_key (str, optional): A key used for data encryption and decryption.
        """
        self.db_path = db_path
        # The ConfigManager here seems to be used for encryption purposes, which is not typical.
        self.config_manager = ConfigManager(db_path, password=encryption_key)

    def execute_query(self, query, params=None, commit=False):
        """
        Executes a SQL query on the SQLite database.

        Args:
            query (str): The SQL query to execute.
            params (tuple, optional): Parameters to substitute into the query.
            commit (bool, optional): Whether to commit the transaction immediately.

        Returns:
            list: The result of the fetchall() if commit is False, otherwise None.

        Raises:
            sqlite3.Error: If an SQLite error occurs.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or [])
                if commit:
                    conn.commit()
                else:
                    return cursor.fetchall()
        except sqlite3.Error as e:
            sys.stderr.write(f"An error occurred: {e.args[0]}")
            raise

    def create_table(self, table_name, columns):
        """
        Creates a new table in the SQLite database with the specified columns if it doesn't exist.

        Args:
            table_name (str): The name of the table to create.
            columns (dict): A dictionary with column names as keys and data types as values.

        Raises:
            Exception: If any error occurs during the creation of the table.
        """
        try:
            column_defs = ', '.join([f"{col_name} {data_type}" for col_name, data_type in columns.items()])
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"
            self.execute_query(query, commit=True)
        except Exception as e:
            sys.stderr.write(f"An error occurred while creating the table: {e}")
            raise

    def insert_data(self, table, data):
        """
        Inserts a new row into the specified table. If an encryption key is provided, the data
        is encrypted before being inserted.

        Args:
            table (str): The name of the table to insert data into.
            data (dict): A dictionary where keys are column names and values are the data to insert.

        Raises:
            Exception: If an error occurs during the data insertion.
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            encrypted_values = tuple(
                base64.b64encode(self.config_manager.encrypt(str(value)).encode()) for value in data.values()
            )
            query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
            self.execute_query(query, encrypted_values, commit=True)
        except Exception as e:
            sys.stderr.write(f"An error occurred during data insertion: {e}")
            raise

    def get_data(self, table, conditions=None):
        """
        Retrieves data from the specified table, with an optional WHERE clause defined by the conditions.

        Args:
            table (str): The name of the table to retrieve data from.
            conditions (dict, optional): A dictionary of conditions to apply to the WHERE clause.

        Returns:
            list: A list of dictionaries representing each row of the result set, with data decrypted if necessary.

        Raises:
            Exception: If any error occurs during the data retrieval process.
        """
        try:
            # Retrieve column names to map the database values to the correct columns
            cursor = self.execute_query(f"PRAGMA table_info({table})")
            column_names = [info[1] for info in cursor]

            conditions_str = ' AND '.join([f"{k}=:{k}" for k in conditions]) if conditions else ''
            query = f"SELECT * FROM {table} {f'WHERE {conditions_str}' if conditions_str else ''}"

            rows = self.execute_query(query, conditions if conditions else None)

            decrypted_rows = self._decrypt_rows(column_names, rows)
            return decrypted_rows
        except Exception as e:
            sys.stderr.write(f"An error occurred during data retrieval: {e}\n")
            raise

    def _decrypt_rows(self, column_names, rows):
        """
        Decrypts the values in the rows retrieved from the database if encryption was used.

        Args:
            column_names (list): A list of column names.
            rows (list): The rows retrieved from the database, which may contain encrypted data.

        Returns:
            list: A list of dictionaries, with each representing a decrypted row.

        Raises:
            ValueError: If decryption fails for any value.
        """
        decrypted_rows = []
        for row in rows:
            decrypted_row = {}
            for key, value in zip(column_names, row):
                if value is not None and isinstance(value, bytes):
                    try:
                        decoded_value = base64.b64decode(value).decode()
                        decrypted_value = self.config_manager.decrypt(decoded_value)
                    except Exception as e:
                        raise ValueError(f"Error decrypting value for {key}: {e}")
                    decrypted_row[key] = decrypted_value
                else:
                    decrypted_row[key] = value
            decrypted_rows.append(decrypted_row)
        return decrypted_rows

    def update_data(self, table, data, conditions):
        """
        Updates rows in the specified table that meet the given conditions with the provided data.

        Args:
            table (str): The name of the table where the update will occur.
            data (dict): A dictionary with column names as keys and the new data as values.
            conditions (dict): A dictionary that specifies the conditions for the update.

        Raises:
            Exception: If an error occurs during the update process.
        """
        try:
            set_clause = ', '.join([f"{k}=?" for k in data])
            encrypted_values = tuple(
                base64.b64encode(self.config_manager.encrypt(str(value)).encode()) for value in data.values()
            )
            where_clause = ' AND '.join([f"{k}=?" for k in conditions])
            query = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
            self.execute_query(query, encrypted_values + tuple(conditions.values()), commit=True)
        except Exception as e:
            sys.stderr.write(f"An error occurred during data update: {e}")
            raise

    def delete_data(self, table, conditions):
        """
        Deletes rows from the specified table that meet the given conditions.

        Args:
            table (str): The name of the table to delete data from.
            conditions (dict): A dictionary that specifies the conditions for deletion.

        Raises:
            Exception: If an error occurs during the deletion process.
        """
        try:
            where_clause = ' AND '.join([f"{k}=?" for k in conditions])
            query = f'DELETE FROM {table} WHERE {where_clause}'
            self.execute_query(query, tuple(conditions.values()), commit=True)
        except Exception as e:
            sys.stderr.write(f"An error occurred during data deletion: {e}")
            raise
