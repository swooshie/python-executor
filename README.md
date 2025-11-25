# Python Script Execution API (Sandboxed with nsjail)

This service executes user-submitted Python code inside a sandbox using nsjail and exposes a single POST `/execute` endpoint.  
It is containerized with Docker and deployable to Google Cloud Run.

---

## Features

- Executes arbitrary Python safely using nsjail  
- Captures only `main()` return value + stdout  
- 5-second timeout  
- No subprocesses, no network, restricted filesystem  
- Supports numpy & pandas  
- Cloud Run compatible (all disallowed namespaces disabled)

---

## API Endpoint

### POST /execute

Request body  
> {"script":"def main(): return {\"hello\": \"world\"}"}

Success  
> {"result":{"hello":"world"}, "stdout":""}

Error  
> {"error":"Function 'main()' not found in script."}

---

## Run Locally

### 1. Build image  
    docker build -t python-executor .

### 2. Run container  
    docker run -p 8080:8080 python-executor

### 3. Test local execution  
    curl -X POST "http://localhost:8080/execute" \
      -H "Content-Type: application/json" \
      -d '{"script":"def main(): return {\"hello\": \"local\"}"}'

Expected output  
> {"result":{"hello":"local"},"stdout":""}

---

## Deployment (Google Cloud Run)

### 1. Build and push AMD64 image  
    docker buildx build \
      --platform linux/amd64 \
      -t us-east1-docker.pkg.dev/<PROJECT_ID>/stacksync-repo/python-executor:latest \
      --push .

### 2. Deploy  
    gcloud run deploy python-executor \
      --image us-east1-docker.pkg.dev/<PROJECT_ID>/stacksync-repo/python-executor:latest \
      --region us-east1 \
      --platform managed \
      --port 8080 \
      --allow-unauthenticated

### 3. Test deployed service  
    curl -X POST "<SERVICE_URL>/execute" \
      -H "Content-Type: application/json" \
      -d '{"script":"def main(): return {\"cloud\": \"ok\"}"}'

Expected  
> {"result":{"cloud":"ok"},"stdout":""}

---

## How the Sandbox Works

Cloud Run restricts namespace creation, so nsjail is configured with all namespace-related flags disabled.

Effective nsjail command:

    /usr/bin/nsjail \
        -Mo \
        --quiet \
        --time_limit 5 \
        --chroot / \
        --disable_proc \
        --disable_clone_newns \
        --disable_clone_newuser \
        --disable_clone_newcgroup \
        --disable_clone_newipc \
        --disable_clone_newuts \
        --disable_clone_newnet \
        --disable_clone_newpid \
        --user 65534 \
        --group 65534 \
        -- \
        /usr/bin/python3 /app/runner.py

Security guarantees:

- Runs as UID/GID 65534 (nobody)  
- No network access  
- No subprocesses  
- Restricted filesystem  
- 5-second CPU time limit  
- Python isolated in a controlled chroot  

---

## Project Structure

    python-executor/
    │
    ├── app.py
    ├── runner.py
    ├── Dockerfile
    ├── requirements.txt
    └── README.md

---

## Working Test Cases

### Simple return  
    curl -X POST "https://python-executor-271438750588.us-east1.run.app/execute" \
      -H "Content-Type: application/json" \
      -d '{"script":"def main(): return {\"status\": \"ok\"}"}'

> {"result":{"status":"ok"},"stdout":""}

### Stdout + return  
    curl -X POST "https://python-executor-271438750588.us-east1.run.app/execute" \
      -H "Content-Type: application/json" \
      -d '{"script":"def main(): print(\"hi\"); return {\"msg\":\"done\"}"}'

> {"result":{"msg":"done"},"stdout":"hi\n"}

### Pandas  
    curl -X POST "https://python-executor-271438750588.us-east1.run.app/execute" \
      -H "Content-Type: application/json" \
      -d '{"script":"import pandas as pd\ndef main(): return {\"sum\": int(pd.DataFrame({\"a\":[1,2,3]}).a.sum())}"}'

> {"result":{"sum":6},"stdout":""}

### Infinite loop (jail kills it)  
    curl -X POST "https://python-executor-271438750588.us-east1.run.app/execute" \
      -H "Content-Type: application/json" \
      -d '{"script":"def main():\n while True: pass"}'

> {"error":"Execution failed"}

### File listing  
    curl -X POST "https://python-executor-271438750588.us-east1.run.app/execute" \
      -H "Content-Type: application/json" \
      -d '{"script":"import os\ndef main(): return {\"files\": os.listdir(\"/\")}"}'

> {"result":{"files":[...]}, "stdout":""}

---

## Notes

- User code **must** define `main()`  
- Result must be JSON-serializable  
- stdout is captured  
- Network access blocked  
- Execution timeout kills long-running code 

---

## Author

Aditya Jhaveri  
Secure Python Executor – Cloud Run Sandbox