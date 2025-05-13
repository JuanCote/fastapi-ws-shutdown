# FastAPI WebSocket Notification Server with Graceful Shutdown

This project is a self-contained WebSocket server built using **FastAPI**. It supports real-time notifications to all connected clients and includes a robust **graceful shutdown mechanism** that ensures the server only stops when either all WebSocket connections are closed or a maximum timeout of **30 minutes** has elapsed.

---

## 🚀 Features

* **WebSocket endpoint** at `/ws` using FastAPI
* **Connection manager** that tracks all active WebSocket clients
* **Broadcast system** to send messages to all connected clients
* **Periodic notifications** sent every 10 seconds
* **Graceful shutdown**

  * Waits for clients to disconnect or 30 minutes
  * Logs progress and connection count
  * Supports multi-worker uvicorn setups
* **Fully Dockerized** setup with Docker Compose
* **Code quality tools**: `black`, `isort`, `flake8`, `mypy`
* **Dependency management** using Poetry

---

## 📁 Project Structure

```
websocket-server/
├── .env
├── .flake8
├── docker-compose.yml
├── Dockerfile
├── lint.sh
├── poetry.lock
├── pyproject.toml
├── README.md
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── graceful_shutdown.py
│   ├── main.py
│   ├── periodic_sender.py
│   ├── redis_listener.py
│   └── ws_manager.py
```

---

## 🛠 Setup Instructions

### 🔧 Prerequisites

* Python 3.11+
* Docker + Docker Compose (v2)

### ⬇️ Clone the Repository

```bash
git clone https://github.com/JuanCote/fastapi-ws-shutdown.git
cd fastapi-ws-shutdown
```

### 📄 Create a `.env` file

Inside the project root, create a file named `.env` and add the following:

```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_CHANNEL=broadcast

PYTHONPATH=.
```

### 🐳 Run with Docker Compose

```bash
docker compose up --build
```

To stop gracefully (without killing Redis):

```bash
docker compose stop app
```

This sends a `SIGINT` to the app container and waits up to 30 minutes for all WebSocket clients to disconnect before forcibly stopping.

---

## 📡 How to Test the WebSocket Endpoint

### Using wscat (CLI)

```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws
```

Open another terminal and connect again:

```bash
wscat -c ws://localhost:8000/ws
```

Sending a message from one will broadcast to the other.

---

## 🧼 Code Quality Tools

Run all linters, formatters, and type checks with:

```bash
./lint.sh
```

Which internally runs:

* `black` – code formatter
* `isort` – import sorter
* `flake8` – linter
* `mypy` – type checker

---

## 🧠 Graceful Shutdown Explained

This application supports running with **multiple Uvicorn workers**, thanks to Redis-based coordination.

Each worker maintains its own connection state and shares shutdown progress via Redis, ensuring that the shutdown logic functions correctly even in a multi-process environment.

1. **Signal Handling**

   * Custom handlers for `SIGINT` and `SIGTERM` are registered.
   * When received, an `asyncio.Event` (`shutdown_event`) is set.

2. **Shutdown Monitoring**

   * A background task checks every 5 seconds how many WebSocket clients remain.
   * If the number drops to **0**, the app exits immediately via `os._exit(0)`.
   * Otherwise, it waits until a **30-minute timeout** expires.

3. **Logging**

   * Every 5 seconds, logs the number of remaining clients and time left.
   * Logs successful shutdown or forced timeout.

4. **Multi-Worker Support**

   * The shutdown event logic is per-process.
   * WebSocket apps should typically use a single worker or external coordination.

---
