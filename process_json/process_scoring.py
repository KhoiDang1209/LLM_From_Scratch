import json
from pathlib import Path
import re
import unicodedata
from datetime import datetime

def clean_text(text):
    """Clean and normalize text."""
    if not isinstance(text, str):
        return text
    
    # Normalize Unicode characters
    text = unicodedata.normalize('NFC', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove newlines within text
    text = re.sub(r'\n', ' ', text)
    
    return text.strip()

def process_scoring_table(data):
    """Process scoring criteria table into RAG-friendly format."""
    criteria = []
    current_category = None
    current_subcategory = None
    
    for table in data.get('tables', []):
        for row in table.get('data', []):
            if not isinstance(row, list) or len(row) < 2:
                continue
                
            # Clean the row data
            row = [clean_text(cell) for cell in row]
            
            # Check if this is a main category (e.g., "1", "2", "3")
            if re.match(r'^\d+$', row[0]):
                current_category = {
                    'id': row[0],
                    'name': row[1],
                    'max_points': re.search(r'\(0-(\d+)đ\)', row[1]).group(1) if re.search(r'\(0-(\d+)đ\)', row[1]) else None,
                    'subcategories': []
                }
                criteria.append(current_category)
                current_subcategory = None
                
            # Check if this is a subcategory (e.g., "1.1", "1.2")
            elif re.match(r'^\d+\.\d+$', row[0]):
                current_subcategory = {
                    'id': row[0],
                    'name': row[1],
                    'items': []
                }
                if current_category:
                    current_category['subcategories'].append(current_subcategory)
                    
            # This is a scoring item
            elif re.match(r'^\d+\.\d+\.\d+$', row[0]):
                item = {
                    'id': row[0],
                    'description': row[1],
                    'points': row[2] if len(row) > 2 else None,
                    'responsible_unit': row[3] if len(row) > 3 else None
                }
                if current_subcategory:
                    current_subcategory['items'].append(item)

    return criteria

def create_rag_document(criteria):
    """Create a RAG-friendly document structure."""
    document = {
        'document_id': 'quy_dinh_diem_ren_luyen',
        'type': 'diem_ren_luyen',
        'content': {
            'danh_sach_tieu_chi': criteria
        },
        'metadata': {
            'nguồn': '4.json',
            'ngôn_ngữ': 'vi',
            'ngày_xử_lý': datetime.now().isoformat(),
            'phiên_bản': '1.0',
            'tổng_số_tiêu_chí': len(criteria),
            'phân_bố_điểm': {
                'học_tập': next((c['max_points'] for c in criteria if c['id'] == '1'), None),
                'nội_quy': next((c['max_points'] for c in criteria if c['id'] == '2'), None),
                'hoạt_động': next((c['max_points'] for c in criteria if c['id'] == '3'), None)
            }
        }
    }
    
    return document

def main():
    # Define input and output paths
    input_file = Path('text_output/4.json')
    output_dir = Path('rag_data')
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process scoring criteria
        criteria = process_scoring_table(data)
        
        # Create RAG document
        rag_document = create_rag_document(criteria)
        
        # Save processed document
        output_file = output_dir / 'rag_diem_ren_luyen.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rag_document, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully processed scoring criteria from {input_file}")
        print(f"Total categories processed: {len(criteria)}")
        print(f"Output saved to: {output_file}")
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")

if __name__ == "__main__":
    main() 