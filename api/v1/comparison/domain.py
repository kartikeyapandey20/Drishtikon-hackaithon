from .repository import ProcessedDataRepository
from .schema import ProcessedDataResponse

class ProcessedDataDomain:
    def __init__(self):
        self.processed_data_repository = ProcessedDataRepository()
    
    async def process_and_store_data(self, input_text: str, image_1, image_2, db) -> ProcessedDataResponse:
        return await self.processed_data_repository.process_and_store_data(input_text, image_1, image_2, db)