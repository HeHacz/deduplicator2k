import sqlite3
import os
from datetime import datetime

class DBManager:
    def __init__(self, db_path="file_hashes.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        db_exists = os.path.exists(db_path) 
        # Connect to database
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row

        self.cursor = self.conn.cursor()
        if not db_exists:
            self.initialize_db()
        
    def initialize_db(self):
        """Create the necessary tables if they don't exist."""

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                file_name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                size INTEGER NOT NULL,
                last_modified INTEGER NOT NULL,
                last_scan INTEGER NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                deactivated_at INTEGER DEFAULT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS hashes (
                hash_value TEXT NOT NULL,
                file_id INTEGER NOT NULL,
                PRIMARY KEY (hash_value, file_id),
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hash_value ON hashes (hash_value)
        ''')
        
        self.conn.commit()

    def get_table_info(self):
        """Retrieve information about the database tables."""
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = self.cursor.fetchall()
            table_info = {}
            for table in tables:
                table_name = table[0]
                self.cursor.execute(f"PRAGMA table_info({table_name})")
                columns = self.cursor.fetchall()
                table_info[table_name] = [dict(column) for column in columns]
            print(f"Tables in database: {table_info.keys()}")
            # Return table information
            print(f"Table info: {table_info}")  

            return table_info
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return {}
    
    def insert_file(self, file_path, file_name, file_size, last_modified, scan_date, file_hash):
        """Insert or update a file's information in the database."""
        # Store file info with its hash
        try:
            # Check if the file already exists in the database     
            self.cursor.execute("SELECT id, file_name, active FROM files WHERE path = ?", (file_path,))
            existing_file = self.cursor.fetchone()
            if existing_file:
                active = existing_file['active']
                deactivated_at = existing_file['deactivated_at']
                data = [file_name, file_path, file_size, last_modified, scan_date, active, deactivated_at, existing_file['id']]
                self.cursor.execute("UPDATE files SET file_name = ?, size = ?, last_modified = ?, last_scan = ?,  deactivated_at = ?, active = ? WHERE id = ?", data)
                file_id = existing_file['id']
            else:
                data = [file_name, file_path, file_size, last_modified, scan_date]
                self.cursor.execute("INSERT INTO files (file_name, path, size, last_modified, last_scan, active) VALUES (?, ?, ?, ?, ?, TRUE)", data)
                file_id = self.cursor.lastrowid
                
            hashes_values = [file_hash, file_id]
            self.cursor.execute("INSERT OR REPLACE INTO hashes (hash_value, file_id) VALUES (?,?)", hashes_values)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
        
    def get_duplicates(self):
        """Retrieve all duplicate files grouped by hash."""
        try:
            self.cursor.execute("SELECT h.hash_value, COUNT(*) as count FROM hashes h GROUP BY h.hash_value HAVING COUNT(*) > 1")
            duplicate_hashes = self.cursor.fetchall()
            result = {}
            for hash_record  in duplicate_hashes:
                hash_value = hash_record[0]

                self.cursor.execute("SELECT f.id, f.file_name, f.path, f.size, f.last_modified, f.last_scan, f.active FROM files f JOIN hashes h on f.id = h.file_id WHERE f.active = 1 and h.hash_value = ? ORDER BY f.last_modified, f.file_name", (hash_value,))
                duplicate_files = [dict(row) for row in self.cursor.fetchall()]
                result[hash_value] = duplicate_files
            return result
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return {}
        
    def lookup_file(self, file_name=None, file_path=None, file_hash=None):
        """Look up a file by path or hash."""
        try:

            query = "SELECT f.id, f.file_name, f.path, f.size, f.last_modified, f.last_scan, f.active, h.hash_value FROM files f JOIN hashes h ON f.id = h.file_id WHERE {}"
            
            if file_name:
                query = query.format("f.file_name = ?")
                param = file_name
            elif file_path:
                query = query.format("f.path = ?")
                param = file_path
            elif file_hash:
                query = query.format("h.hash_value = ?")
                param = file_hash
            else:
                return []  
                
            self.cursor.execute(query, (param,))
            files = self.cursor.fetchall()
            return files
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return []
        
    def get_file_by_hash(self, file_hash):
        """Get all files with a specific hash."""
        # Return all file paths matching a hash
        try:
            self.cursor.execute("SELECT f.file_name, f.path FROM files f JOIN hashes h on f.id = h.file_id WHERE h.hash_value = ?", (file_hash,))
            files = self.cursor.fetchall()
            return files
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return []
        
    def get_file_by_path(self, file_path):
        """Get a file by its path."""
        # Return file information matching a path
        try:
            self.cursor.execute("SELECT f.file_name, f.path, f.size, f.last_modified, f.last_scan, f.active FROM files f WHERE f.path = ?", (file_path,))
            file_info = self.cursor.fetchone()
            if file_info:
                return dict(file_info)
            return None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return None
    
    def get_file_active_status(self, file_path):
        """Get the active status of a file."""
        try:
            self.cursor.execute("SELECT active FROM files WHERE path = ?", (file_path,))
            file_status = self.cursor.fetchone()
            if file_status:
                return file_status[0]
            return None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return None
    
    def get_active_file(self, file_path):
        """Get the active file information."""
        try:
                # Get the hash for the given file path
            self.cursor.execute(
                "SELECT h.hash_value FROM hashes h JOIN files f ON h.file_id = f.id WHERE f.path = ?",
                (file_path,)
            )
            hash_row = self.cursor.fetchone()
            if not hash_row:
                return []
            file_hash = hash_row["hash_value"]

            # Get all active files with the same hash
            self.cursor.execute(
                "SELECT f.file_name, f.path FROM files f JOIN hashes h ON f.id = h.file_id WHERE h.hash_value = ? AND f.active = 1",
                (file_hash,)
            )
            files = self.cursor.fetchall()
            return [dict(row) for row in files]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return None
    
    def get_active_files(self):
        """Get all active files."""
        try:
            self.cursor.execute("SELECT f.file_name, f.path, f.size, f.last_modified, f.last_scan, f.active FROM files f WHERE f.active = 1")
            active_files = self.cursor.fetchall()
            return [dict(row) for row in active_files]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return []
    
    def get_inactive_files(self):
        """Get all inactive files."""
        try:
            self.cursor.execute("SELECT f.file_name, f.path, f.size, f.last_modified, f.last_scan, f.active, f.deactivated_at FROM files f WHERE f.active = 0")
            inactive_files = self.cursor.fetchall()
            return [dict(row) for row in inactive_files]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return []

    def set_file_inactive(self, file_path):
        """Set a file as inactive in the database."""
        try:
            self.cursor.execute("SELECT id FROM files WHERE path = ?", (file_path,))
            file_id = self.cursor.fetchone()

            if file_id:
                file_id = file_id[0]
                self.cursor.execute("UPDATE files SET active = FALSE, deactivated_at = ? WHERE path = ?", (datetime.now().timestamp(), file_path))
                self.conn.commit()
                return True
            return False
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
        
    def set_file_active(self, file_path):
        """Set a file as active in the database."""
        try:
            self.cursor.execute("SELECT id FROM files WHERE path = ?", (file_path,))
            file_id = self.cursor.fetchone()

            if file_id:
                file_id = file_id[0]
                self.cursor.execute("UPDATE files SET active = TRUE, deactivated_at = NULL WHERE path = ?", (file_path,))
                self.conn.commit()
                return True
            return False
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
    
        
    def remove_file(self, file_path):
        """Remove a file from the database."""
        try:
            self.cursor.execute("SELECT id FROM files WHERE path = ?", (file_path,))
            file_id = self.cursor.fetchone()

            if file_id:
                file_id = file_id[0]
                self.cursor.execute("DELETE FROM hashes WHERE file_id=?", (file_id,))
                self.cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                self.conn.commit()
                return True
            return False
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False

    
    def clean_missing_files(self):
        """Remove entries for files that no longer exist."""
        # Verify files still exist and remove if not
        try:
            self.cursor.execute("SELECT id, path FROM files")
            files = self.cursor.fetchall()
            
            removed_count = 0
            for file_id, file_path in files:
                if not os.path.exists(file_path):
                    self.cursor.execute("DELETE FROM hashes WHERE file_id = ?", (file_id,))
                    self.cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                    removed_count += 1
                self.cursor.commit()
            return  removed_count
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()