import threading
import zipfile
import os
from contextlib import closing
import urllib.request
import sqlite3, zlib, random, time
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
import hashlib
import requests
import time
# import logging
# logging.basicConfig(filename="download.log", level=logging.INFO)


def download_file(urls, local_file, expected_checksum=None, max_retries=3):
    if not urls:
        raise ValueError("No URLs provided.")

    for url in urls:
        retries = 0
        success = False

        while not success and retries < max_retries:
            try:
                download_file_simple(url, local_file, expected_checksum)
                success = True
            except (requests.exceptions.RequestException, ValueError) as e:
                print(f"Error downloading from {url}: {e}")
                retries += 1
                if retries < max_retries:
                    print(f"Retrying... ({retries}/{max_retries})")
                    time.sleep(2**retries)  # exponential backoff
                else:
                    print(f"Failed to download from {url} after {max_retries} attempts.")
        
        if success:
            return True
    
    return False

def download_extract(urls, extract_dir, checksum):
    local_dl_file = os.path.join(extract_dir, os.path.basename(urls[0]))

    success = download_file(urls, local_file=local_dl_file, expected_checksum=checksum, max_retries=3)
    if success:
        with zipfile.ZipFile(local_dl_file, "r") as f:
            f.extractall(extract_dir)
        # remove the zip file after extraction
        os.remove(local_dl_file)

    return success

def sha256_checksum(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def download_file_simple(url, target_path, expected_sha256=None):
    progress_lock = threading.Lock()

    def show_progress(count, total_size):
        with progress_lock:
            percentage = int(count * 100 / total_size)
            print(f'\rDownloading {url}: {percentage}%', end='')

    if os.path.isdir(target_path):
        file_name = os.path.basename(urlparse(url).path)
        target_path = os.path.join(target_path, file_name)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('Content-Length', -1))

    with open(target_path, 'wb') as local_file:
        block_size = 8192
        downloaded_size = 0
        for block in response.iter_content(block_size):
            local_file.write(block)
            downloaded_size += len(block)
            show_progress(downloaded_size, total_size)
        print()

    if expected_sha256:
        actual_sha256 = sha256_checksum(target_path)
        if actual_sha256.lower() != expected_sha256.lower():
            os.remove(target_path)
            raise ValueError(f"Downloaded file has incorrect SHA256 hash. Expected {expected_sha256}, but got {actual_sha256}.")
        else:
            print("SHA256 hash verified.")


def download_thread(url, extract_dir, checksum):
    dl_thread = threading.Thread(target=download_file_simple, args=(url, extract_dir, checksum))
    dl_thread.start()
    dl_thread.join()