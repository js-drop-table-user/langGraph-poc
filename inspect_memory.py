import os
import pickle
import sqlite3
from typing import Any

from config import OllamaConfig

DB_PATH = os.path.join(OllamaConfig.WORKSPACE_DIR, "agent_memory.sqlite")


def _process_data_blob(data_blob: Any):
    """데이터 블록을 처리하고 내용을 출력합니다."""
    try:
        if isinstance(data_blob, bytes):
            try:
                data = pickle.loads(data_blob)
                print(f"Unpickled Data: {data}")
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, tuple) and len(item) > 1:
                            val = item[1]
                            if hasattr(val, "content"):
                                print(f"Content: {val.content}")
            except Exception:
                # Fallback: search for strings in raw bytes
                content = data_blob.decode("utf-8", errors="ignore")
                print(f"Raw Bytes Search (Preview): {content[:500]}")
        else:
            print(f"Data: {data_blob}")
    except Exception as e:
        print(f"Error processing data: {e}")


def inspect_messages():
    """DB에 저장된 메시지 내역을 조회합니다."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT thread_id, task, data FROM writes ORDER BY thread_id DESC LIMIT 50;"
        )
        writes = cursor.fetchall()
        print(f"\n--- Found {len(writes)} writes ---")

        for tid, task, data_blob in writes:
            print(f"\n[Thread: {tid}, Task: {task}]")
            _process_data_blob(data_blob)

    except Exception as e:
        print(f"Error querying table: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    inspect_messages()
