import sys
import json
import threading
import requests

def download_file(url, path, index):
    try:
        resp = requests.get(url, stream=True)
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 1024*1024  # 1MB
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = int(downloaded * 100 / total) if total else 0
                    # gửi progress về stdout
                    print(json.dumps({"index": index, "progress": percent}))
                    sys.stdout.flush()
        # hoàn tất
        print(json.dumps({"index": index, "progress": 100, "status": "completed"}))
        sys.stdout.flush()
    except Exception as e:
        print(json.dumps({"index": index, "progress": 0, "status": "error", "error": str(e)}))
        sys.stdout.flush()

def main():
    threads = []
    task_index = 0
    for line in sys.stdin:
        data = json.loads(line)
        url = data.get("url")
        path = data.get("path")
        if url and path:
            t = threading.Thread(target=download_file, args=(url, path, task_index))
            t.start()
            threads.append(t)
            task_index += 1

    # join threads nếu muốn chờ tất cả hoàn tất
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
