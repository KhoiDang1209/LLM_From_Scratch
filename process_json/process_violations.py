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

def extract_severity_level(penalties):
    """Determine severity level based on penalties."""
    if penalties['buộc_thôi_học']:
        return 4, 'buộc thôi học'
    elif penalties['đình_chỉ_học_tập']:
        return 3, 'đình chỉ học tập'
    elif penalties['cảnh_cáo']:
        return 2, 'cảnh cáo'
    elif penalties['khiển_trách']:
        return 1, 'khiển trách'
    return 0, 'không có'

def process_violations_table(data):
    """Process violations table into RAG-friendly format."""
    violations = []
    
    for table in data.get('tables', []):
        for row in table.get('data', []):
            if not isinstance(row, dict) or 'cells' not in row:
                continue
                
            cells = row['cells']
            
            # Extract and clean basic information
            violation_id = clean_text(cells.get('TT - TT', ''))
            description = clean_text(cells.get('Nội dung vi phạm - Nội dung vi phạm', ''))
            
            # Extract and clean penalties
            penalties = {
                'khiển_trách': clean_text(cells.get('Số lần vi phạm và hình thức xử lý\n(Số lần tính trong cả khoá học) - Khiển trách', '')),
                'cảnh_cáo': clean_text(cells.get('Số lần vi phạm và hình thức xử lý\n(Số lần tính trong cả khoá học) - Cảnh cáo', '')),
                'đình_chỉ_học_tập': clean_text(cells.get('Số lần vi phạm và hình thức xử lý\n(Số lần tính trong cả khoá học) - Đình chỉ học tập có\nthời hạn', '')),
                'buộc_thôi_học': clean_text(cells.get('Số lần vi phạm và hình thức xử lý\n(Số lần tính trong cả khoá học) - Buộc thôi học', ''))
            }
            
            # Extract notes
            notes = clean_text(cells.get('Ghi chú - Ghi chú', ''))
            
            # Determine severity level
            severity_level, severity_type = extract_severity_level(penalties)
            
            # Create violation object
            violation = {
                'id': violation_id,
                'description': description,
                'hình_thức_xử_lý': penalties,
                'ghi_chú': notes,
                'mức_độ': {
                    'cấp_độ': severity_level,
                    'loại': severity_type
                },
                'semantic_id': f"vi_pham_{violation_id.replace('.', '')}"
            }
            
            violations.append(violation)
    
    return violations

def create_rag_document(violations):
    """Create a RAG-friendly document structure."""
    document = {
        'document_id': 'quy_dinh_vi_pham',
        'type': 'vi_pham',
        'content': {
            'danh_sach_vi_pham': violations
        },
        'metadata': {
            'nguồn': '3.json',
            'ngôn_ngữ': 'vi',
            'ngày_xử_lý': datetime.now().isoformat(),
            'phiên_bản': '1.0',
            'tổng_số_vi_pham': len(violations),
            'phân_bố_mức_độ': {
                'khiển_trách': len([v for v in violations if v['mức_độ']['loại'] == 'khiển trách']),
                'cảnh_cáo': len([v for v in violations if v['mức_độ']['loại'] == 'cảnh cáo']),
                'đình_chỉ_học_tập': len([v for v in violations if v['mức_độ']['loại'] == 'đình chỉ học tập']),
                'buộc_thôi_học': len([v for v in violations if v['mức_độ']['loại'] == 'buộc thôi học'])
            }
        }
    }
    
    return document

def main():
    # Define input and output paths
    input_file = Path('text_output/3.json')
    output_dir = Path('rag_data')
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process violations
        violations = process_violations_table(data)
        
        # Create RAG document
        rag_document = create_rag_document(violations)
        
        # Save processed document
        output_file = output_dir / 'rag_vi_pham.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rag_document, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully processed violations from {input_file}")
        print(f"Total violations processed: {len(violations)}")
        print(f"Output saved to: {output_file}")
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")

if __name__ == "__main__":
    main() 