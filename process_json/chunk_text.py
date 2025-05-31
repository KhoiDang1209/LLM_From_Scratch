import json
from pathlib import Path
import os
import re
import argparse

def normalize_text_content(content):
    """
    Normalize text content by removing extra whitespace and ensuring consistent formatting.
    
    Args:
        content: Can be string, list of strings, or nested structure with text
        
    Returns:
        str: Normalized text content
    """
    if isinstance(content, str):
        return content.strip()
    elif isinstance(content, list):
        return '\n'.join(item.strip() for item in content if item.strip())
    return ''

def process_table(table):
    """
    Process table content into a readable text format.
    
    Args:
        table: Table structure from JSON
        
    Returns:
        str: Formatted table text
    """
    if not table:
        return ''
        
    table_parts = []
    
    # Add table title if exists
    if table.get('title'):
        table_parts.append(table['title'].strip())
    
    # Process table headers
    if table.get('headers'):
        headers = [h.strip() for h in table['headers'] if h.strip()]
        if headers:
            table_parts.append(' | '.join(headers))
            table_parts.append('-' * len(' | '.join(headers)))
    
    # Process table rows
    if table.get('rows'):
        for row in table['rows']:
            if isinstance(row, list):
                row_text = [str(cell).strip() for cell in row if str(cell).strip()]
                if row_text:
                    table_parts.append(' | '.join(row_text))
    
    return '\n'.join(table_parts)

def process_json_file(file_path, output_dir):
    """
    Process a JSON file, extract text content, and create chunks for each semantic unit.
    
    Args:
        file_path (str): Path to the input JSON file
        output_dir (str): Directory to save chunked output
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the JSON file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    chunks = []
    chunk_id = 1
    
    # Process sections
    if data.get('content', {}).get('sections'):
        for section in data['content']['sections']:
            if not section.get('title') or not section.get('content'):
                continue
            
            # Add the section chunk
            chunks.append({
                'chunk_id': f'chunk_{chunk_id}',
                'title': section['title'],
                'content': section['content']
            })
            chunk_id += 1
    
    # Create output filename
    base_name = Path(file_path).stem
    output_file = os.path.join(output_dir, f"{base_name}_chunks.json")
    
    # Save chunks to JSON file
    output_data = {
        'document_id': data.get('document_id', base_name),
        'type': data.get('type', 'policy'),
        'metadata': data.get('metadata', {}),
        'chunks': chunks
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    return output_file

def process_directory(input_dir, output_dir):
    """
    Process all JSON files in a directory.
    
    Args:
        input_dir (str): Directory containing input JSON files
        output_dir (str): Directory to save chunked output
    """
    input_path = Path(input_dir)
    total_chunks = 0
    
    for json_file in input_path.glob('*.json'):
        try:
            output_file = process_json_file(str(json_file), output_dir)
            # Count chunks in the output file
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                num_chunks = len(data.get('chunks', []))
                total_chunks += num_chunks
            print(f"Processed {json_file.name} -> {Path(output_file).name}")
            print(f"Chunks created: {num_chunks}")
        except Exception as e:
            print(f"Error processing {json_file.name}: {str(e)}")
    
    print(f"\nTotal chunks processed: {total_chunks}")

def process_single_file(input_file, output_dir):
    """
    Process a single JSON file.
    
    Args:
        input_file (str): Path to the input JSON file
        output_dir (str): Directory to save chunked output
    """
    try:
        output_file = process_json_file(input_file, output_dir)
        # Count chunks in the output file
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            num_chunks = len(data.get('chunks', []))
        print(f"Successfully processed {Path(input_file).name}")
        print(f"Chunks created: {num_chunks}")
        print(f"Output saved to: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return None

def process_hcmiu_json(json_data):
    """Process HCMIU JSON structure with sections containing title, content, semantic_id and type."""
    chunks = []
    
    # Get document metadata
    doc_id = json_data.get('document_id', '')
    doc_type = json_data.get('type', '')
    
    # Process each section
    for section in json_data.get('content', {}).get('sections', []):
        title = section.get('title', '')
        content = section.get('content', '')
        semantic_id = section.get('semantic_id', '')
        section_type = section.get('type', '')
        
        # Create chunk with section info
        chunk = {
            'title': title,
            'content': content,
            'semantic_id': semantic_id,
            'type': section_type,
            'document_id': doc_id,
            'document_type': doc_type
        }
        chunks.append(chunk)
        
    return chunks

def process_json(json_data):
    """Process different JSON structures and return chunks."""
    # Check if it's HCMIU structure
    if 'document_id' in json_data and 'content' in json_data and 'sections' in json_data.get('content', {}):
        return process_hcmiu_json(json_data)
        
    # Check if it's article structure
    if 'articles' in json_data:
        return process_article_json(json_data)
        
    # Check if it's points structure  
    if 'points' in json_data:
        return process_points_json(json_data)
        
    # Check if it's chapters structure
    if 'chapters' in json_data:
        return process_chapters_json(json_data)
        
    # Default to processing as single content
    return process_single_content(json_data)

def main():
    # Define input and output paths
    input_files = [
        Path('../rag_data/rag_hcmiu.json')  # Adjusted path to match directory structure
    ]
    output_dir = Path('../chunked_data')  # Adjusted path to match directory structure
    output_dir.mkdir(exist_ok=True)
    
    total_chunks = 0
    
    for input_file in input_files:
        try:
            # Process file
            output_file = process_single_file(str(input_file), str(output_dir))
            
            # Count chunks in the output file
            if output_file:
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    num_chunks = len(data.get('chunks', []))
                    total_chunks += num_chunks
                
                print(f"Successfully processed {input_file}")
                print(f"Chunks created: {num_chunks}")
                print(f"Output saved to: {output_file}")
            
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")
    
    print(f"\nTotal chunks processed: {total_chunks}")

if __name__ == "__main__":
    main() 