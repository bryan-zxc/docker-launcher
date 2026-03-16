import time
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel

from docker_launcher.prerequisites import (
    get_prerequisites,
    install_gh,
    gh_login,
)
from docker_launcher.update_service import (
    check_for_update,
    download_update,
    get_update_state,
    start_background_checker,
)
from docker_launcher.docker_service import (
    DockerNotAvailableError,
    list_images,
    get_image,
    build_image,
    list_containers,
    create_container,
    start_container,
    stop_container,
    delete_container,
    open_in_vscode,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import webbrowser

    start_background_checker()
    webbrowser.open("http://localhost:3000")
    yield


app = FastAPI(title="Docker Launcher", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DockerNotAvailableError)
async def docker_not_available_handler(request: Request, exc: DockerNotAvailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc), "docker_not_running": True},
    )


# --- Version ---


@app.get("/api/version")
async def api_version():
    try:
        v = version("docker-launcher")
    except Exception:
        v = "dev"
    return {"version": v}


# --- Images ---


@app.get("/api/images")
async def api_list_images():
    return list_images()


@app.get("/api/images/{name}")
async def api_get_image(name: str):
    image = get_image(name)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@app.post("/api/images/{name}/build")
async def api_build_image(name: str, force: bool = False):
    image = get_image(name)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    def stream():
        try:
            for line in build_image(name, force=force):
                yield f"data: {line}\n\n"
        except Exception as e:
            yield f"data: ERROR: {e}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# --- Containers ---


class CreateContainerRequest(BaseModel):
    image: str
    repo_url: str | None = None
    name: str | None = None


@app.get("/api/containers")
async def api_list_containers():
    return list_containers()


@app.post("/api/containers")
async def api_create_container(req: CreateContainerRequest):
    try:
        return create_container(req.image, req.repo_url, req.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        import logging

        logging.getLogger(__name__).exception("Container creation failed")
        raise HTTPException(status_code=500, detail="Container creation failed")


@app.post("/api/containers/{container_id}/start")
async def api_start_container(container_id: str):
    try:
        return start_container(container_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/containers/{container_id}/stop")
async def api_stop_container(container_id: str):
    try:
        return stop_container(container_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/containers/{container_id}/vscode")
async def api_open_vscode(container_id: str):
    try:
        return open_in_vscode(container_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/containers/{container_id}")
async def api_delete_container(container_id: str):
    try:
        return delete_container(container_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Prerequisites ---


@app.get("/api/prerequisites")
async def api_prerequisites():
    return get_prerequisites()


@app.post("/api/prerequisites/install-gh")
async def api_install_gh():
    def stream():
        try:
            for line in install_gh():
                yield f"data: {line}\n\n"
        except Exception as e:
            yield f"data: ERROR: {e}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream; charset=utf-8")


@app.post("/api/prerequisites/gh-login")
async def api_gh_login():
    def stream():
        try:
            for line in gh_login():
                yield f"data: {line}\n\n"
        except Exception as e:
            yield f"data: ERROR: {e}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream; charset=utf-8")


# --- Updates ---


@app.get("/api/update-check")
async def api_update_check():
    return get_update_state()


@app.post("/api/update-check")
async def api_update_check_now():
    return check_for_update()


@app.post("/api/update-download")
async def api_update_download():
    def stream():
        try:
            for line in download_update():
                yield f"data: {line}\n\n"
        except Exception as e:
            yield f"data: ERROR: {e}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream; charset=utf-8")


@app.post("/api/shutdown")
async def api_shutdown():
    import os
    import signal
    import threading

    def _delayed_shutdown():
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=_delayed_shutdown, daemon=True).start()
    return {"status": "shutting_down"}


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True))


def main():
    import logging
    from logging.handlers import RotatingFileHandler

    import uvicorn

    log_file = Path.home() / ".docker-launcher" / "launcher.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    uvicorn.run(app, host="127.0.0.1", port=3000)
