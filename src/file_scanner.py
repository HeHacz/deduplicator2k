from tqdm import tqdm
import os


def scan_for_files(path: str):
    files = []
    for root, dirnames, filenames in tqdm(os.walk(path)):
        for file in filenames:
            path = os.path.join(root, file)
            files.append({
                'path': path,
                'file_name': file,
                'size': os.path.getsize(path),
                'last_modified': os.path.getmtime(path)
            })
    return files


