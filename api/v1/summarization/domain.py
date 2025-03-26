from .repository import SummarizationRepository

class SummarizationDomain:
    def __init__(self) -> None:
        self.__repository = SummarizationRepository()

    def create_text_entry(self, db, text_data):
        """
        Create a new text entry, store it, process it with AI, and return the result.

        Args:
            db: The database session.
            text_data: The input text data.

        Returns:
            TextResponse: The stored and AI-processed text.
        """
        return self.__repository.create_text(text_data, db)

    def get_text_entry_by_id(self, text_id, db):
        """
        Retrieve a text entry by its ID.

        Args:
            text_id: The ID of the text entry.
            db: The database session.

        Returns:
            TextResponse: The stored text with AI processing result.
        """
        return self.__repository.get_text_by_id(text_id, db)
