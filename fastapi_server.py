from fastapi import FastAPI, BackgroundTasks, Query, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
import os
import glob
import subprocess
from typing import Optional
import tempfile
import threading

app = FastAPI()

LOGS_DIR = 'logs'
CLI_PATH = 'cli.py'
PYTHON_EXEC = 'python'

def get_latest_log(command_prefix: str) -> Optional[str]:
    files = sorted(glob.glob(f'{LOGS_DIR}/{command_prefix}_*.log'), reverse=True)
    return files[0] if files else None

def run_cli_command(args, log_file):
    with open(log_file, 'w', encoding='utf-8') as f:
        process = subprocess.Popen([PYTHON_EXEC, CLI_PATH] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
        for line in process.stdout:
            print(line, end='')  # Print to server console
            f.write(line)
        process.wait()

def split_refs_file(refs_file, num_chunks=5):
    with open(refs_file, encoding='utf-8') as f:
        refs = [line for line in f if line.strip()]
    chunk_size = (len(refs) + num_chunks - 1) // num_chunks
    temp_files = []
    for i in range(num_chunks):
        chunk = refs[i*chunk_size:(i+1)*chunk_size]
        if not chunk:
            continue
        tf = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.txt')
        tf.writelines(chunk)
        tf.close()
        temp_files.append(tf.name)
    return temp_files

def run_and_cleanup(args, log_file, temp_file):
    run_cli_command(args, log_file)
    try:
        os.remove(temp_file)
    except Exception:
        pass

@app.post('/run/explicit')
def run_explicit(refs_file: str = Query('sefaria_trefs.txt'), background_tasks: BackgroundTasks = None):
    os.makedirs(LOGS_DIR, exist_ok=True)
    temp_files = split_refs_file(refs_file, num_chunks=5)
    log_files = []
    for i, temp_file in enumerate(temp_files):
        log_file = f"{LOGS_DIR}/explicit_{os.getpid()}_{i}.log"
        args = ['explicit', '--refs-file', temp_file]
        background_tasks.add_task(run_and_cleanup, args, log_file, temp_file)
        log_files.append(log_file)
    return {"log_files": log_files}

@app.post('/run/semantic')
def run_semantic(
    threshold: Optional[float] = Query(None),
    minlen: Optional[int] = Query(None),
    background_tasks: BackgroundTasks = None
):
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = f"{LOGS_DIR}/semantic_{os.getpid()}.log"
    args = ['semantic']
    if threshold is not None:
        args += ['--threshold', str(threshold)]
    if minlen is not None:
        args += ['--minlen', str(minlen)]
    background_tasks.add_task(run_cli_command, args, log_file)
    return {"log_file": log_file}

@app.get('/logs')
def list_logs():
    files = sorted(glob.glob(f'{LOGS_DIR}/*.log'), reverse=True)
    return JSONResponse([os.path.basename(f) for f in files])

@app.get('/logs/{log_file}')
def get_log(log_file: str):
    file_path = os.path.join(LOGS_DIR, log_file)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Log file not found")
    return PlainTextResponse(open(file_path, encoding='utf-8').read()) 