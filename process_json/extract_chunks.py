import json
from pathlib import Path
import os

def extract_all_chunks(chunked_data_dir, output_file):
    """
    Extract all chunks from JSON files in chunked_data_dir and save to a single JSON file.
    
    Args:
        chunked_data_dir (str): Directory containing chunked JSON files
        output_file (str): Path to output JSON file
    """
    all_chunks = []
    total_chunks = 0
    
    # Get all JSON files in the directory
    json_files = Path(chunked_data_dir).glob('*.json')
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Get document metadata
            doc_id = data.get('document_id', '')
            doc_type = data.get('type', '')
            
            # Process each chunk
            for chunk in data.get('chunks', []):
                chunk_data = {
                    'title': chunk.get('title', ''),
                    'content': chunk.get('content', ''),
                    'document_id': doc_id,
                    'document_type': doc_type,
                    'chunk_id': chunk.get('chunk_id', ''),
                    'semantic_id': chunk.get('semantic_id', ''),
                    'type': chunk.get('type', '')
                }
                all_chunks.append(chunk_data)
            
            num_chunks = len(data.get('chunks', []))
            total_chunks += num_chunks
            print(f"Processed {json_file.name}: {num_chunks} chunks")
            
        except Exception as e:
            print(f"Error processing {json_file.name}: {str(e)}")
    
    # Create output data structure
    output_data = {
        'total_chunks': total_chunks,
        'total_documents': len(list(Path(chunked_data_dir).glob('*.json'))),
        'chunks': all_chunks
    }
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nTotal chunks extracted: {total_chunks}")
    print(f"Output saved to: {output_file}")

def main():
    # Define input and output paths
    chunked_data_dir = '../chunked_data'  # Adjust path as needed
    output_file = '../combined_chunks.json'  # Adjust path as needed
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Extract and save chunks
    extract_all_chunks(chunked_data_dir, output_file)

if __name__ == "__main__":
    main()