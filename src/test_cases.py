import unittest
import os
import time
from db_manager import DBManager
from hash_utils import get_file_hash

class DBManagerTest(unittest.TestCase):
    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)    
        
    
    def test_insert_file(self):
        # Test basic file insertion
        db = DBManager("test_db_insert.db")
        result = db.insert_file(
            file_path="/test/path.txt",
            file_name="path.txt",
            file_size=100,
            last_modified=time.time(),
            scan_date=time.time(),
            file_hash="dummy_hash" 
        )
        self.assertTrue(result)

        file = db.get_file_by_path("/test/path.txt")
        self.assertIsNotNone(file)
        self.assertEqual(file['file_name'], "path.txt")
        self.assertEqual(file['active'], 1)
        self.assertEqual(file['size'], 100)
        
        if os.path.exists("test_db_insert.db"):
            db.close()
            os.remove("test_db_insert.db")
    

    def test_get_files(self):
        db = DBManager("test_db_get_files.db")
        # Insert a few files
        db.insert_file("/test/file1.txt", "file1.txt", 100, time.time(), time.time(), "hash1")
        db.insert_file("/test/file2.txt", "file2.txt", 200, time.time(), time.time(), "hash2")
        db.insert_file("/test/file3.txt", "file3.txt", 300, time.time(), time.time(), "hash3")
        
        # Deactivate one file
        db.set_file_inactive("/test/file2.txt")
        
        # Get active files
        active_files = db.get_active_files()
        self.assertEqual(len(active_files), 2)
        
        # Verify the correct files are returned
        file_paths = [file['path'] for file in active_files]
        self.assertIn("/test/file1.txt", file_paths)
        self.assertIn("/test/file3.txt", file_paths)
        self.assertNotIn("/test/file2.txt", file_paths)

        if os.path.exists("test_db_get_files.db"):
            db.close()
            os.remove("test_db_get_files.db")
    
    def test_get_file_by_hash(self):
        db = DBManager("test_db_hash.db")
        # Insert a file with a known hash
        unique_hash = "unique_hash_value"
        db.insert_file(
            file_name="hashtest.txt",
            file_path="/test/hashtest.txt",
            file_size=150,
            last_modified=time.time(),
            scan_date=time.time(),
            file_hash=unique_hash
        )
        
        # Retrieve the file by hash
        files = db.get_file_by_hash(unique_hash)

        for file in files:
            self.assertIsNotNone(file)
            self.assertEqual(file['path'], "/test/hashtest.txt")
            self.assertEqual(file['file_name'], "hashtest.txt")
        
        # Test with a hash that doesn't exist
        nonexistent_file = db.get_file_by_hash("nonexistent_hash")
        self.assertFalse(nonexistent_file)
        if os.path.exists("test_db_hash.db"):
            db.close()
            os.remove("test_db_hash.db")

    def test_get_inactive_files(self):
        db = DBManager("test_db_inactive.db")
        # Insert some files
        db.insert_file("/test/active1.txt", "active1.txt", 100, time.time(), time.time(), "hash1")
        db.insert_file("/test/active2.txt", "active2.txt", 100, time.time(), time.time(), "hash2")
        db.insert_file("/test/inactive1.txt", "inactive1.txt", 100, time.time(), time.time(), "hash3")
        db.insert_file("/test/inactive2.txt", "inactive2.txt", 100, time.time(), time.time(), "hash4")


        
        # Deactivate some files
        db.set_file_inactive("/test/inactive1.txt")
        db.set_file_inactive("/test/inactive2.txt")

        # Get inactive files
        inactive_files = db.get_inactive_files()
        self.assertEqual(len(inactive_files), 2)
        
        # Verify correct files are returned
        inactive_paths = [file['path'] for file in inactive_files]
        self.assertIn("/test/inactive1.txt", inactive_paths)
        self.assertIn("/test/inactive2.txt", inactive_paths)
        self.assertNotIn("/test/active1.txt", inactive_paths)
        self.assertNotIn("/test/active2.txt", inactive_paths)

        if os.path.exists("test_db_inactive.db"):
            db.close()
            os.remove("test_db_inactive.db")
      
    def test_active_file(self):
        db = DBManager("test_db_active.db")
        # Insert a file
        db.insert_file(
            file_name="exists.txt",
            file_path="/test/exists.txt",
            file_size=100,
            last_modified=time.time(),
            scan_date=time.time(),
            file_hash="exists_hash"
        )
        
        # Check if file exists
        self.assertTrue(db.get_active_file("/test/exists.txt"))
        self.assertFalse(db.get_active_file("/test/does_not_exist.txt"))

        if os.path.exists("test_db_active.db"):
            db.close()
            os.remove("test_db_active.db")

    def test_if_hash_is_equal(self):
        with open("test_file1.txt", "w") as f:
            f.write("This is a text file and should have unique hash.")
            f.close()
        with open("test_file2.txt", "w") as f:
            f.write("This is a text file and should have same hash as file with the same text.")
            f.close()
        with open("test_file3.txt", "w") as f:
            f.write("This is a text file and should have same hash as file with the same text.")
            f.close()

        unique_hash = get_file_hash("./test_file1.txt")
        hash_file2 = get_file_hash("./test_file2.txt")
        hash_file3 = get_file_hash("./test_file2.txt")



        self.assertNotEqual(unique_hash, hash_file2)
        self.assertNotEqual(unique_hash, hash_file3)
        self.assertEqual(hash_file2, hash_file3)

        if os.path.exists("./test_file1.txt"):
            os.remove("./test_file1.txt")
        
        if os.path.exists("./test_file2.txt"):
            os.remove("./test_file2.txt")

        if os.path.exists("./test_file3.txt"):
            os.remove("./test_file3.txt")    

  
if __name__ == "__main__":
    unittest.main()