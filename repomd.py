import os
import shutil
import subprocess
import argparse
import time

def parse_args():
    parser = argparse.ArgumentParser(
        description="Clone and clean a GitHub repo for LLM ingestion (Windows-safe)."
    )
    parser.add_argument('repo_url', help='GitHub repo URL (e.g. https://github.com/username/repo.git)')
    parser.add_argument('--clean_dir', default='clean_code', help='Directory for cleaned code')
    parser.add_argument('--clone_dir', default='repo_temp', help='Temp clone directory')
    parser.add_argument('--max_mb', type=int, default=10, help='Max file size (MB) for non-code files')
    parser.add_argument('--extensions', default='.py,.cpp,.h,.hpp,.c,.js,.java,.ts,.go,.rs',
                        help='Comma-separated list of code file extensions')
    return parser.parse_args()

def is_code_file(filename, code_extensions):
    return any(filename.endswith(ext) for ext in code_extensions)

def is_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read()
        return True
    except:
        return False

def on_rm_error(func, path, exc_info):
    """
    Error handler for `shutil.rmtree`.
    If the error is due to access permission, it tries to change the file to be writable and remove again.
    """
    import stat
    try:
        os.chmod(path, stat.S_IWUSR)
        func(path)
        print(f"  Forced remove: {path}")
    except Exception as e:
        print(f"  Could not remove {path}: {e}")

def try_delete_folder(folder, retries=5, delay=1):
    for attempt in range(retries):
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder, onerror=on_rm_error)
                print(f"  Deleted: {folder}")
                return True
            except Exception as e:
                print(f"  Attempt {attempt+1}: Could not remove {folder}: {e}")
                time.sleep(delay)
        else:
            print(f"  Folder not found (already deleted): {folder}")
            return True
    print(f"  ERROR: Could not remove {folder} after several attempts.")
    return False


def combine_to_markdown(clean_dir, output_md="combined_code.md", code_extensions=None):
    if code_extensions is None:
        code_extensions = [".py", ".cpp", ".h", ".hpp", ".c", ".js", ".java", ".ts", ".go", ".rs"]
    print(f"\nCombining all code files into {output_md} ...")
    with open(output_md, "w", encoding="utf-8") as out_md:
        for root, dirs, files in os.walk(clean_dir):
            for file in files:
                ext = os.path.splitext(file)[-1]
                # Only include files with the desired code extensions
                if ext.lower() not in code_extensions:
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, clean_dir)
                lang = ext.lstrip(".")
                out_md.write(f"\n\n---\n\n### `{rel_path}`\n\n")
                out_md.write(f"```{lang}\n")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        out_md.write(f.read())
                except Exception as e:
                    out_md.write(f"<Could not read file: {e}>")
                out_md.write("\n```\n")
    print(f"Combined Markdown saved to {output_md}")


def main():
    args = parse_args()
    REPO_URL = args.repo_url
    CLONE_DIR = args.clone_dir
    CLEAN_DIR = args.clean_dir
    MAX_FILESIZE_MB = args.max_mb
    CODE_EXTENSIONS = [ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions.split(',')]

    FOLDERS_TO_REMOVE = [
        '.git', 'build', 'dist', 'bin', 'obj', 'node_modules', 'venv',
        '__pycache__', '.mypy_cache', '.env'
    ]

    # -------- 1. Clone Repo --------
    if os.path.exists(CLONE_DIR):
        print(f"Removing old clone directory: {CLONE_DIR}")
        shutil.rmtree(CLONE_DIR, onerror=on_rm_error)
    print(f"Cloning {REPO_URL} ...")
    subprocess.run(["git", "clone", REPO_URL, CLONE_DIR], check=True)

    # -------- 2. Remove unwanted folders (including .git robustly) --------
    print("Removing unwanted folders...")
    for folder in FOLDERS_TO_REMOVE:
        dir_path = os.path.join(CLONE_DIR, folder)
        if os.path.isdir(dir_path):
            try_delete_folder(dir_path)

    # -------- 3. Remove non-text (binary) files & big files, skipping .git --------
    print("Removing binaries and large non-code files...")
    for root, dirs, files in os.walk(CLONE_DIR):
        # Defensive: skip any .git still left
        if '.git' in root.split(os.sep):
            continue
        for file in files:
            file_path = os.path.join(root, file)
            # Remove big files unless code
            if not is_code_file(file, CODE_EXTENSIONS) and os.path.getsize(file_path) > MAX_FILESIZE_MB * 1024 * 1024:
                print(f"  Removing large file: {file_path}")
                try:
                    os.remove(file_path)
                except PermissionError:
                    print(f"  Skipped (permission error): {file_path}")
                except Exception as e:
                    print(f"  Skipped ({e}): {file_path}")
                continue
            # Remove binaries (non-text, non-code)
            if not is_code_file(file, CODE_EXTENSIONS) and not is_text_file(file_path):
                print(f"  Removing binary file: {file_path}")
                try:
                    os.remove(file_path)
                except PermissionError:
                    print(f"  Skipped (permission error): {file_path}")
                except Exception as e:
                    print(f"  Skipped ({e}): {file_path}")

    # -------- 4. Copy only code files to clean dir --------
    if os.path.exists(CLEAN_DIR):
        print(f"Removing old clean directory: {CLEAN_DIR}")
        shutil.rmtree(CLEAN_DIR, onerror=on_rm_error)
    print("Copying code files to clean directory...")
    for root, dirs, files in os.walk(CLONE_DIR):
        # Defensive: skip any .git still left
        if '.git' in root.split(os.sep):
            continue
        for file in files:
            if is_code_file(file, CODE_EXTENSIONS):
                src = os.path.join(root, file)
                dst = os.path.join(CLEAN_DIR, os.path.relpath(src, CLONE_DIR))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

    print(f"\nAll cleaned code is in '{CLEAN_DIR}'.")
    combine_to_markdown(CLEAN_DIR, "combined_code.md")

if __name__ == '__main__':
    main()
