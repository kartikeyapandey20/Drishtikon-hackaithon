from fastapi import APIRouter
from api.v1.summarization.router import SummarizationRouter 
from api.v1.recognition.router import RecognitionRouter
api_router = APIRouter()

api_router.include_router(SummarizationRouter().router)
api_router.include_router(RecognitionRouter().router)

@api_router.get("/")
def index():
	return {"status": "ok"}
