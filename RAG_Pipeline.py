from openai import OpenAI
from pymongo import MongoClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import torch
import logging
from typing import List, Dict, Any

class RAGSearch:
    def __init__(self, mongodb_uri: str, openai_api_key: str):
        """
        Initialize the RAG Search system
        
        Args:
            mongodb_uri (str): MongoDB connection URI
            openai_api_key (str): OpenAI API key for document routing
        """
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Initialize MongoDB connection
        self.client = MongoClient(mongodb_uri)
        self.collection = self.client["HCMIU_Data"]["Data"]
        
        # Initialize embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="keepitreal/vietnamese-sbert",
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize OpenAI client for document routing
        self.openai_client = OpenAI(api_key=openai_api_key)
        
    def get_available_document_types(self) -> List[str]:
        """Get list of unique document types in the database"""
        return self.collection.distinct("document_type")
    
    def normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to range [0,1] using min-max normalization"""
        if not scores:
            return []
        min_score = min(scores)
        max_score = max(scores)
        if max_score == min_score:
            return [1.0] * len(scores)
        return [(score - min_score) / (max_score - min_score) for score in scores]
    
    def get_document_type(self, query: str) -> str:
        """
        Use OpenAI to determine the document type for a query
        
        Args:
            query (str): The user's query
            
        Returns:
            str: The determined document type
        """
        functions = [
            {
                "name": "document_routing",
                "description": "Bạn đang đóng vai là một nhân viên phân loại tài liệu của một trường học, bạn sẽ phân loại tài liệu dựa trên nội dung đầu vào của người dùng: 1-'article' nếu yêu cầu thông tin cơ bản, 2-'policy' nếu yêu cầu đề xuất chính sách, đề án, 3-'course_structure' nếu yêu cầu chương trình học, 4-'diem_ren_luyen' nếu yêu cầu thông tin về điểm rèn luyện của sinh viên, 5-'vi_pham' nếu yêu cầu thông tin về vi phạm của sinh viên. 6-'quy_dinh' nếu yêu cầu thông tin về quy định của trường",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_type": {
                            "type": "string",
                            "description": "Phân loại tài liệu dựa trên nội dung đầu vào của người dùng: 1-'article' nếu yêu cầu thông tin cơ bản, 2-'course_structure' nếu yêu cầu chương trình học, 3-'diem_ren_luyen' nếu yêu cầu thông tin về điểm rèn luyện của sinh viên, 4-'vi_pham' nếu yêu cầu thông tin về vi phạm của sinh viên. 5-'quy_dinh' nếu yêu cầu thông tin về quy định của trường"
                        }
                    },
                    "required": ["document_type"]
                }
            }
        ]

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a document classification assistant for a university."},
                    {"role": "user", "content": query}
                ],
                functions=functions,
                function_call={"name": "document_routing"}
            )

            function_call = response.choices[0].message.function_call
            if function_call:
                import json
                args = json.loads(function_call.arguments)
                return args.get('document_type')
            
            return None

        except Exception as e:
            self.logger.error(f"Error in document type determination: {e}")
            return None
    
    def hybrid_search(self, query: str, document_type: str, alpha: float = 0.5) -> List[Document]:
        """
        Perform hybrid search with document type filtering
        
        Args:
            query (str): The search query
            document_type (str): The document type to search within
            alpha (float): Weight for vector search (0-1)
            
        Returns:
            List[Document]: Ranked search results
        """
        try:
            # Check if document type exists
            doc_count = self.collection.count_documents({"document_type": document_type})
            if doc_count == 0:
                self.logger.warning(f"⚠️ No documents found for type: {document_type}")
                return []
            
            # Special handling for course_structure documents
            if document_type == "course_structure":
                return self._course_structure_search(query, document_type)
            else:
                return self._hybrid_search(query, document_type, alpha)
                
        except Exception as e:
            self.logger.error(f"❌ Search failed: {e}")
            return []
    
    def _course_structure_search(self, query: str, document_type: str) -> List[Document]:
        """Specialized search for course structure documents"""
        bm25_pipeline = [
            {
                "$search": {
                    "index": "text",
                    "compound": {
                        "must": [
                            {
                                "text": {
                                    "query": query,
                                    "path": "title",
                                    "score": {"boost": {"value": 2}}
                                }
                            }
                        ],
                        "should": [
                            {
                                "text": {
                                    "query": query,
                                    "path": "content"
                                }
                            }
                        ]
                    }
                }
            },
            {
                "$match": {
                    "document_type": document_type
                }
            },
            {
                "$project": {
                    "title": 1,
                    "content": 1,
                    "document_type": 1,
                    "textScore": { "$meta": "searchScore" }
                }
            },
            {
                "$limit": 20
            }
        ]
        
        results = list(self.collection.aggregate(bm25_pipeline))
        
        docs = []
        for doc in results:
            docs.append(Document(
                page_content=doc.get("content", ""),
                metadata={
                    "title": doc.get("title"),
                    "document_type": doc.get("document_type"),
                    "score": doc.get("textScore", 0),
                    "text_score": doc.get("textScore", 0),
                    "vector_score": 0.0
                }
            ))
        
        docs.sort(key=lambda x: x.metadata.get("score", 0), reverse=True)
        return docs[:10]
    
    def _hybrid_search(self, query: str, document_type: str, alpha: float) -> List[Document]:
        """Regular hybrid search for non-course structure documents"""
        # Get query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # BM25 Search
        bm25_pipeline = [
            {
                "$search": {
                    "index": "text",
                    "text": {
                        "query": query,
                        "path": ["title", "content"]
                    }
                }
            },
            {
                "$match": {
                    "document_type": document_type
                }
            },
            {
                "$project": {
                    "title": 1,
                    "content": 1,
                    "document_type": 1,
                    "textScore": { "$meta": "searchScore" }
                }
            },
            {
                "$limit": 20
            }
        ]
        
        bm25_results = list(self.collection.aggregate(bm25_pipeline))
        
        # Vector Search
        vector_pipeline = [
            {
                "$vectorSearch": {
                    "queryVector": query_embedding,
                    "path": "embedding",
                    "numCandidates": 100,
                    "limit": 50,
                    "index": "default"
                }
            },
            {
                "$match": {
                    "document_type": document_type
                }
            },
            {
                "$project": {
                    "title": 1,
                    "content": 1,
                    "document_type": 1,
                    "vectorScore": { "$meta": "vectorSearchScore" }
                }
            },
            {
                "$limit": 20
            }
        ]
        
        vector_results = list(self.collection.aggregate(vector_pipeline))
        
        # Combine and normalize scores
        combined_results = {}
        
        # Process BM25 results
        if bm25_results:
            bm25_scores = [doc.get("textScore", 0) for doc in bm25_results]
            normalized_bm25_scores = self.normalize_scores(bm25_scores)
            
            for doc, norm_score in zip(bm25_results, normalized_bm25_scores):
                doc_id = doc.get("_id")
                combined_results[doc_id] = {
                    "title": doc.get("title"),
                    "content": doc.get("content"),
                    "document_type": doc.get("document_type"),
                    "textScore": norm_score,
                    "vectorScore": 0.0
                }
        
        # Process Vector results
        if vector_results:
            vector_scores = [doc.get("vectorScore", 0) for doc in vector_results]
            normalized_vector_scores = self.normalize_scores(vector_scores)
            
            for doc, norm_score in zip(vector_results, normalized_vector_scores):
                doc_id = doc.get("_id")
                if doc_id in combined_results:
                    combined_results[doc_id]["vectorScore"] = norm_score
                else:
                    combined_results[doc_id] = {
                        "title": doc.get("title"),
                        "content": doc.get("content"),
                        "document_type": doc.get("document_type"),
                        "textScore": 0.0,
                        "vectorScore": norm_score
                    }
        
        # Calculate final scores
        docs = []
        for doc_id, result in combined_results.items():
            vector_score = result["vectorScore"]
            text_score = result["textScore"]
            
            combined_score = (alpha * vector_score) + ((1 - alpha) * text_score)
            
            docs.append(Document(
                page_content=result["content"],
                metadata={
                    "title": result["title"],
                    "document_type": result["document_type"],
                    "score": combined_score,
                    "vector_score": vector_score,
                    "text_score": text_score
                }
            ))
        
        docs.sort(key=lambda x: x.metadata.get("score", 0), reverse=True)
        return docs[:10]
    
    def search(self, query: str, alpha: float = 0.5) -> List[Document]:
        """
        Main search function that determines document type and performs search
        
        Args:
            query (str): The search query
            alpha (float): Weight for vector search (0-1)
            
        Returns:
            List[Document]: Ranked search results
        """
        try:
            # Get document type
            document_type = self.get_document_type(query)
            
            if not document_type:
                self.logger.warning("⚠️ Could not determine document type from query")
                self.logger.info("Available document types:")
                for doc_type in self.get_available_document_types():
                    self.logger.info(f"  - {doc_type}")
                return []
            
            # Perform search
            results = self.hybrid_search(query, document_type, alpha)
            
            # Display results
            print(f"\nSearching for '{query}' in document type: {document_type}")
            print(f"Found {len(results)} relevant documents")
            print("=" * 60)
            
            for i, doc in enumerate(results[:5], 1):
                print(f"\n📄 Result {i}")
                print("Title:", doc.metadata.get("title"))
                print("Document Type:", doc.metadata.get("document_type"))
                print("Combined Score:", f"{doc.metadata.get('score'):.4f}")
                print("Vector Score:", f"{doc.metadata.get('vector_score'):.4f}")
                print("Text Score:", f"{doc.metadata.get('text_score'):.4f}")
                print("Content Preview:", doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)
                print("-" * 50)
            
            return results[:2]
            
        except Exception as e:
            self.logger.error(f"❌ Search process failed: {e}")
            return []