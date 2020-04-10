from fastapi import FastAPI

from app import routes
from app.mysql import mysql
from app.logger import get_custom_logger
from app.rmq import rabbit_mq


logger = get_custom_logger(__name__)

app = FastAPI()
app.include_router(routes.router)


@app.on_event("startup")
async def startup():
    await mysql.create_pool()
    await rabbit_mq.startup()


@app.on_event("shutdown")
async def shutdown():
    await rabbit_mq.shutdown()
    await mysql.close_pool()
