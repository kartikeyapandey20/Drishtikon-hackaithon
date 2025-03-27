# Visually Impaired Assistant API

A FastAPI backend for assisting visually impaired people by processing images through Vision Language Models (VLMs) and Language Models (LLMs) to provide detailed, accessible descriptions.

## Features

- **Image Processing**: Upload images and get detailed descriptions using state-of-the-art vision and language models
- **Multiple Processing Modes**: 
  - General Description: Get a general description of any image
  - OCR: Extract and format text from images
  - Scene Analysis: Get detailed analysis of scenes with spatial relationships
  - Document Reading: Extract and structure content from documents
  - Accessibility: Get descriptions optimized for accessibility
  - Custom: Use custom prompts for specialized needs
- **Specialized Features for Visually Impaired Users**:
  - Currency Recognition: Identify and describe currency denomination and authenticity features
  - Color Analysis: Detailed information about colors, contrasts, and patterns in images
  - Object Recognition & Spatial Relations: Identify objects and their relationships for better navigation
  - Face Recognition: Identify known people and describe facial expressions
  - Product Identification: Identify products including barcode scanning and packaging description
  - Hazard Detection: Safety-focused description highlighting potential dangers
  - Public Transport Information: Extract bus/train numbers, schedules, and relevant transit info
  - Medicine Identification: Help identify medications based on visual characteristics
  - Emotion Analysis: Detect and describe emotional states of people in images
  - Image Comparison: Compare two images and describe the differences between them
  - Document Summarization: Extract, summarize, and determine reading order for documents
  - Enhanced Audio Descriptions: Descriptions specifically formatted for text-to-speech systems
- **User Management**: Register, authenticate, and manage user profiles
- **Image Management**: Upload, list, update, and delete images
- **Processing History**: Track and review past image processing results
- **Feedback System**: Provide feedback on processing results to improve the system
- **Multiple Model Support**: Use OpenAI, Google, or Hugging Face models
- **Multiple Storage Options**: Store images locally, in Google Cloud Storage, or Amazon S3
- **Security**: JWT authentication, role-based access control
- **Rate Limiting**: Prevent abuse with configurable rate limits

## Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: JWT with OAuth2
- **Vision Models**: OpenAI GPT-4 Vision, Google Gemini, Hugging Face models
- **Language Models**: OpenAI GPT-4, Google Gemini, Hugging Face models
- **Storage**: Local filesystem, Google Cloud Storage, Amazon S3
- **Logging**: Loguru
- **Testing**: Pytest

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- API keys for vision and language models (OpenAI, Google, or Hugging Face)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/visually-impaired-assistant.git
   cd visually-impaired-assistant
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

7. Access the API documentation at http://localhost:8000/api/v1/docs

## API Endpoints

### Authentication

- `POST /api/v1/auth/register`: Register a new user
- `POST /api/v1/auth/login`: Login and get access token

### Users

- `GET /api/v1/users/me`: Get current user info
- `PUT /api/v1/users/me`: Update current user info
- `POST /api/v1/users/me/change-password`: Change password

### Images

- `POST /api/v1/images/upload`: Upload an image
- `GET /api/v1/images/`: List user's images
- `GET /api/v1/images/{image_id}`: Get image details
- `PUT /api/v1/images/{image_id}`: Update image metadata
- `DELETE /api/v1/images/{image_id}`: Delete an image

### Processing

- `POST /api/v1/processing/upload-and-process`: Upload and process an image
- `POST /api/v1/processing/process/{image_id}`: Process an existing image
- `GET /api/v1/processing/results`: List processing results
- `GET /api/v1/processing/results/{result_id}`: Get processing result details
- `POST /api/v1/processing/feedback`: Provide feedback on a processing result

### Specialized Features

- `POST /api/v1/specialized/currency`: Identify currency denomination and features
- `POST /api/v1/specialized/colors`: Analyze and describe colors in an image
- `POST /api/v1/specialized/objects`: Recognize objects and their spatial relationships
- `POST /api/v1/specialized/faces`: Recognize and identify faces in images
- `POST /api/v1/specialized/products`: Identify products and read barcodes/QR codes
- `POST /api/v1/specialized/hazards`: Detect potential hazards in an environment
- `POST /api/v1/specialized/transport`: Extract public transport information
- `POST /api/v1/specialized/medicine`: Identify medicine from an image
- `POST /api/v1/specialized/emotions`: Analyze emotions of people in images
- `POST /api/v1/specialized/compare`: Compare two images and describe differences
- `POST /api/v1/specialized/summarize-document`: Extract and summarize text from documents
- `POST /api/v1/specialized/audio-description`: Generate specialized audio descriptions

## Configuration

The application is configured through environment variables, which can be set in the `.env` file:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for JWT token generation
- `VISION_MODEL_PROVIDER`: Provider for vision model (openai, google, huggingface)
- `VISION_MODEL_NAME`: Name of the vision model
- `LLM_PROVIDER`: Provider for language model
- `LLM_MODEL_NAME`: Name of the language model
- `STORAGE_PROVIDER`: Provider for file storage (local, gcs, s3)
- `RATE_LIMIT_PER_MINUTE`: Rate limit for API requests

See `.env.example` for all available configuration options.

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for GPT-4 Vision and GPT-4 models
- FastAPI for the excellent web framework
- SQLAlchemy for the ORM
- All other open-source libraries used in this project 