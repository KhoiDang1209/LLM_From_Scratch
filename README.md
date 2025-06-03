# RAG Chatbot with Fine-tuned Viet-Mistral

This project implements a Retrieval-Augmented Generation (RAG) chatbot using a fine-tuned Viet-Mistral model. The chatbot combines document retrieval capabilities with the language model to provide accurate and context-aware responses.

## Features

- Fine-tuned Viet-Mistral model for Vietnamese language understanding
- MongoDB-based document retrieval system
- OpenAI embeddings for semantic search
- Context-aware response generation
- Document source tracking and citation

## Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account
- OpenAI API key
- Fine-tuned Viet-Mistral model checkpoint

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# For Google Colab
from google.colab import userdata
userdata.set('mongodb', 'your_mongodb_uri')
userdata.set('OpenAI', 'your_openai_api_key')

# For local development
export MONGODB_URI='your_mongodb_uri'
export OPENAI_API_KEY='your_openai_api_key'
```

## Usage

1. Start the chatbot:
```bash
python rag_chatbot.py
```

2. Interact with the chatbot by typing your questions. The chatbot will:
   - Search for relevant documents in the database
   - Use the retrieved context to generate a response
   - Show the sources used for the response

3. Type 'quit' to exit the chatbot.

## Project Structure

- `rag_chatbot.py`: Main chatbot implementation
- `RAG_Pipeline.py`: Document retrieval and search functionality
- `requirements.txt`: Project dependencies
- `vistral-lora-checkpoint/`: Fine-tuned model checkpoint directory

## Customization

### Adding Documents

To add new documents to the database:

```python
from RAG_Pipeline import RAGSearch

rag = RAGSearch(mongodb_uri='your_mongodb_uri', openai_api_key='your_openai_api_key')

# Add a document
rag.add_document(
    content="Your document content here",
    metadata={
        "title": "Document Title",
        "document_type": "article",
        # Add other metadata as needed
    }
)
```

### Model Configuration

You can modify the model parameters in `rag_chatbot.py`:

```python
# Generation parameters
max_new_tokens=512
temperature=0.7
top_p=0.9
top_k=50
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
