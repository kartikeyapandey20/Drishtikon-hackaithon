from fastapi import APIRouter
from api.v1.summarization.router import SummarizationRouter 
api_router = APIRouter()

api_router.include_router(SummarizationRouter().router)

@api_router.get("/")
def index():
	return {"status": "ok"}
