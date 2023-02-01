from datetime import datetime

from fastapi import FastAPI, Response

from . import WebhookHandlerPool
from .models import WebHook
from .route_classes import QSEncodedRoute

app = FastAPI()
pool = WebhookHandlerPool()

app.router.route_class = QSEncodedRoute

@app.post("/")
@pool.add_origin
async def webhook(hook: WebHook):
    # await pool.resolve(hook)
    return Response(status_code=200)



def run(app_path="webhook_puppeteer.main:app"):
    import uvicorn
    uvicorn.run(app_path, port=5000, log_level="info", reload=True)


if __name__ == "__main__":
    run("main:app")
