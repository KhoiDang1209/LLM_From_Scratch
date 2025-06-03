import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from RAG_Pipeline import RAGSearch
from google.colab import userdata

class RAGChatbot:
    def __init__(self, mongodb_uri, openai_api_key, base_model_name="Viet-Mistral/Vistral-7B-Chat", adapter_path="./vistral-lora-checkpoint"):
        # Initialize RAG search
        self.rag_search = RAGSearch(mongodb_uri=mongodb_uri, openai_api_key=openai_api_key)
        
        # Load model and tokenizer
        print("Loading model and tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        self.model = PeftModel.from_pretrained(self.model, adapter_path)
        print("Model and tokenizer loaded successfully!")

    def format_rag_results(self, rag_results):
        """Format RAG results into a context string"""
        formatted_string = "Relevant Documents:\n"
        for i, doc in enumerate(rag_results):
            formatted_string += f"--- Document {i+1} ---\n"
            formatted_string += f"Title: {doc.metadata.get('title', 'N/A')}\n"
            formatted_string += f"Document Type: {doc.metadata.get('document_type', 'N/A')}\n"
            formatted_string += f"Content:\n{doc.page_content}\n\n"
        return formatted_string

    def generate_response(self, prompt, context="", max_new_tokens=512):
        """Generate response using the model with context"""
        # Combine context and prompt
        if context:
            full_prompt = f"Bạn là một trợ lý hỗ trợ thông tin về trường Đại học Quốc tế HCMIU. Dựa trên thông tin sau đây, hãy trả lời câu hỏi của người dùng. \n\nThông tin truy vấn: {context}\n\nCâu hỏi: {prompt}"
        else:
            full_prompt = prompt

        # Format the prompt using the chat template
        messages = [{"role": "user", "content": full_prompt}]
        formatted_prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize the input
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
        
        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                top_k=50,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode and return the response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.split("Assistant: ")[-1].strip()
        return response

    def chat(self, query):
        """Process a query with RAG and generate response"""
        # Get relevant documents
        rag_results = self.rag_search.search(query)
        
        # Format context from RAG results
        context = self.format_rag_results(rag_results)
        
        # Generate response
        response = self.generate_response(query, context)
        
        
        
        return response
