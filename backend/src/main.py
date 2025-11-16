from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


#import uvicorn
from src.config import config

fastapi_app = FastAPI(docs_url=f'{config.API_PREFIX}/docs',)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8000', 'http://localhost:63342', 'http://localhost:5500'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


from src.routers.report_router import router as report_router
fastapi_app.include_router(report_router)