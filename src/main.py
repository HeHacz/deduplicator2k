from hash_utils import get_file_hash
from file_scanner import scan_for_files
from db_manager import DBManager
from datetime import datetime
from tqdm import tqdm
import os, argparse, shutil

def remove_file(file_path, db):
    """Remove a file from the filesystem."""
    try:
        os.remove(file_path)
        print(f"Removed file from the filesystem: {file_path}")
        db.set_file_inactive(file_path)
        print(f"File marked as inactive in database: {file_path}")
    except Exception as e:
        print(f"Error removing file {file_path}: {e}")

def restore_file(orginal_file_path, file_path, db):
    """Restore a file in the filesystem."""
    try:
        # Assuming the file is moved to a backup location, restore it from there
        if not os.path.exists(orginal_file_path):
            print(f"The file cannot be restored because the original path couldn't be found.")
            return
        else:
            shutil.copy2(orginal_file_path, file_path)
            print(f"Restored file to the filesystem: {file_path}")
            db.set_file_active(file_path)
            print(f"File marked as active in database: {file_path}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        db.remove_file(file_path)
        removed_count += 1
    except PermissionError:
        print(f"Permission denied: {file_path}")
        db.remove_file(file_path)
        removed_count += 1
    except IsADirectoryError:
        print(f"Is a directory: {file_path}")
        db.remove_file(file_path)
        removed_count += 1
    except OSError as e:
        print(f"OS error: {e}")
        db.remove_file(file_path)
        removed_count += 1

def print_removed_files(path, db):
    """Print all removed files from specified path and give option to restore them."""
    try:
        db.cursor.execute("SELECT path FROM files WHERE active = FALSE and path LIKE ?", (f"{path}%",))
        removed_files = db.cursor.fetchall()
        if not removed_files:
            print("No removed files found.")
            return
        print("Removed files:")
        for file in removed_files:
            print(file[0])
            restore = input(f"Do you want to restore {file[0]}? (y/n): ")
            if restore.lower() == 'y':
                original_file = db.get_active_file(file[0])
                restore_file(original_file[0]["path"], file[0], db)
                print(f"Restored file: {file[0]}")
    except Exception as e:
        print(f"Error retrieving removed files: {e}")

def print_message(message, silent_mode):
    """Print a message if not in silent mode."""
    if not silent_mode:
        print(message)



def main():
    parser = argparse.ArgumentParser(description="This is deduplicator2k. It will help you sweep all duplicate files in your filesystem!!!")
    parser.add_argument("-d", "--directory", help="Directory to scan for files")
    parser.add_argument("-y", "--assumeyes", help="Assume yes to all prompts", action="store_true")
    parser.add_argument("-n", "--dryrun", help="Perform a dry run without deleting files", action="store_true")
    parser.add_argument("-v", "--verbose", help="Enable verbose output", action="store_true")
    parser.add_argument("-r", "--restore", help="Print all removed files and give option to restore them", action="store_true")
    parser.add_argument("-p", "--progress", help="Show progress bar", action="store_true")
    parser.add_argument("-s", "--silent", help="Run in silent mode", action="store_true")

    args = parser.parse_args()

    db = DBManager()
    silent_mode = False
    if args.silent:
        print_message("Silent mode enabled. No output will be printed.", silent_mode)
        silent_mode = True
    if args.verbose and args.silent:
        print_message("Verbose mode and silent mode cannot be used together. Exiting.", silent_mode)
        return
    if args.progress:
        print_message("Progress bar enabled.", silent_mode)
    if args.verbose:
        print_message("Verbose mode enabled.", silent_mode)
    if args.directory and not os.path.isdir(args.directory):
        print_message(f"Directory does not exist: {args.directory}", silent_mode)
        return
    elif args.directory and not os.path.exists(args.directory):
        print_message(f"Directory does not exist: {args.directory}", silent_mode)
        return
    elif args.directory and os.path.isdir(args.directory):
        print_message(f"Directory exists: {args.directory}", silent_mode)
    elif args.directory and os.path.isfile(args.directory):
        print_message(f"File exists: {args.directory}", silent_mode)
        print_message("Please provide a directory to scan for files.", silent_mode)
        return
    if args.directory:
        print_message(f"Scanning directory: {args.directory}", silent_mode)
    else:
        print_message("No directory specified. Using current working directory.", silent_mode)
        args.directory = os.getcwd()
    if args.dryrun:
        print_message("Dry run mode enabled. No files will be deleted.", silent_mode)
    if args.assumeyes:
        print_message("Assuming yes to all prompts.", silent_mode)
    if args.restore:
        print_message("Restore mode enabled. Removed files will be listed for restoration.", silent_mode)
        print_removed_files(args.directory, db)
        return
    files = scan_for_files(args.directory)
    print_message(f"Found {len(files)} files in the directory.", silent_mode)
    if args.verbose:
        for file in files:
            print_message(f"File: {file['file_name']}, Path: {file['path']}, Size: {file['size']}, Last Modified: {file['last_modified']}", silent_mode)
    if not files:
        print_message("No files found in the specified directory.", silent_mode)
        return
    for file in tqdm(files):
        if db.lookup_file(file["file_name"], file["path"]):
            # File already exists in the database
            if args.verbose:
                print_message(f"File already exists in the database: {file['file_name']}", silent_mode)
            # Check if the file is active
            db.cursor.execute("SELECT active FROM files WHERE path = ?", (file["path"],))
            file_status = db.get_file_active_status(file["path"])
            if not file_status:
                db.set_file_active(file["path"])
            else:
                if args.verbose:
                    print_message(f"File already exists in the database: {file['file_name']}", silent_mode)
            continue
        else:
            file_hash = get_file_hash(file["path"])
            db.insert_file(file["file_name"], file["path"], file["size"], file["last_modified"], datetime.today().strftime('%Y-%m-%d %H:%M:%S'), file_hash)
    dups =  db.get_duplicates()
    for entry in tqdm(dups):
        for duplicate in dups[entry][1:]:
            print_message(f"Duplicate found: {dups[entry][0]} and {duplicate}", silent_mode)
            if args.dryrun:
                print_message(f"Dry run mode: Not deleting {duplicate['path']}", silent_mode)
                continue
            if args.assumeyes:
                # Remove the file from the filesystem
                remove_file(duplicate["path"], db)
            else:
                # Ask for confirmation before removing the file
                confirm = input(f"Do you want to remove {duplicate['path']}? (y/n): ")
                if confirm.lower() == 'y':
                    remove_file(duplicate["path"], db)
                else:
                    print_message(f"Skipping removal of {duplicate['path']}", silent_mode)
    db.close()

main()
