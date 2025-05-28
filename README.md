# Repo to Markdown
A simple Python script to convert a GitHub repository to a single markdown file. The original purpose is to aid LLM ingestion for analyzing existing code

<!-- # Examples -->


## Usage
```sh
usage: repomd.py [-h] [--clean_dir CLEAN_DIR] [--clone_dir CLONE_DIR] [--max_mb MAX_MB] [--extensions EXTENSIONS] repo_url
repomd.py: error: argument -h/--help: ignored explicit argument 'elp'
```

## Help
```
Clone and clean a GitHub repo for LLM ingestion (Windows-safe).

positional arguments:
  repo_url              GitHub repo URL (e.g. https://github.com/username/repo.git)

options:
  -h, --help            show this help message and exit
  --clean_dir CLEAN_DIR
                        Directory for cleaned code
  --clone_dir CLONE_DIR
                        Temp clone directory
  --max_mb MAX_MB       Max file size (MB) for non-code files
  --extensions EXTENSIONS
                        Comma-separated list of code file extensions
```
* Generated with GPT-4.1
