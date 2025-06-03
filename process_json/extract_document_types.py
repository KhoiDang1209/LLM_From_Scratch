import json
from typing import Set

def extract_unique_document_types(file_path: str) -> Set[str]:
    """
    Extract unique document types from combined_chunks.json
    
    Args:
        file_path (str): Path to the combined_chunks.json file
        
    Returns:
        Set[str]: Set of unique document types
    """
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract unique document types from chunks
        unique_types = set()
        for chunk in data.get('chunks', []):
            doc_type = chunk.get('document_type')
            if doc_type:
                unique_types.add(doc_type)
        
        return unique_types
        
    except Exception as e:
        print(f"Error reading file: {e}")
        return set()

def main():
    # File path
    file_path = "combined_chunks.json"
    
    # Get unique document types
    unique_types = extract_unique_document_types(file_path)
    
    # Print results
    print("\nUnique Document Types:")
    print("-" * 20)
    for doc_type in sorted(unique_types):
        print(f"- {doc_type}")
    print("-" * 20)
    print(f"Total unique types: {len(unique_types)}")

if __name__ == "__main__":
    main()