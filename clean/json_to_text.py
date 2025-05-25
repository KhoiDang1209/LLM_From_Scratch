import json
import os
import sys
from pathlib import Path

def format_table(table_data):
    """
    Format table data as simple comma-separated lines.
    """
    if not table_data or not isinstance(table_data, list):
        return []
    
    formatted_rows = []
    for row in table_data:
        # Join all cells with commas
        formatted_row = ','.join(str(cell).strip() for cell in row)
        formatted_rows.append(formatted_row)
    
    return formatted_rows

def convert_json_to_text(json_file_path, output_file_path):
    """
    Convert a JSON file to a readable text format.
    Handles various JSON structures including nested content and tables.
    """
    try:
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create output text
        text_content = []
        
        # Add metadata if exists
        metadata_fields = {
            'title': 'Tiêu đề',
            'document_number': 'Số',
            'date': 'Ngày',
            'issuer': 'Người ban hành'
        }
        
        for field, label in metadata_fields.items():
            if data.get(field):
                text_content.append(f"{label}: {data[field]}")
        
        # Add sections if they exist
        if data.get('sections'):
            text_content.append('')  # Add empty line
            for section in data['sections']:
                section_text = []
                if section.get('number'):
                    section_text.append(f"{section['number']}")
                if section.get('text'):
                    section_text.append(section['text'])
                if section_text:
                    text_content.append(' '.join(section_text))
        
        # Add articles if they exist
        if data.get('articles'):
            text_content.append('')  # Add empty line
            for article in data['articles']:
                # Add article number and title
                article_header = []
                if article.get('number'):
                    article_header.append(f"Điều {article['number']}.")
                if article.get('title'):
                    article_header.append(article['title'])
                if article_header:
                    text_content.append(' '.join(article_header))
                
                # Add article content
                if article.get('content'):
                    for content_item in article['content']:
                        if isinstance(content_item, str):
                            text_content.append(content_item)
                        elif isinstance(content_item, dict):
                            # Handle nested content
                            for key, value in content_item.items():
                                if isinstance(value, str):
                                    text_content.append(f"{key}: {value}")
                                elif isinstance(value, list):
                                    for item in value:
                                        text_content.append(f"{key}: {item}")
                
                text_content.append('')  # Add empty line between articles
        
        # Add tables if they exist
        if data.get('tables'):
            text_content.append('')  # Add empty line
            for table in data['tables']:
                if isinstance(table, dict):
                    # Handle table with table_id and data
                    if 'table_id' in table and 'data' in table:
                        text_content.append(f"Bảng {table['table_id']}")
                        text_content.append('')  # Add empty line before table
                        
                        # Format and add table data
                        formatted_table = format_table(table['data'])
                        text_content.extend(formatted_table)
                        
                        text_content.append('')  # Add empty line after table
                    else:
                        # Handle other table formats
                        for key, value in table.items():
                            if isinstance(value, str):
                                text_content.append(f"{key}: {value}")
                            elif isinstance(value, list):
                                formatted_table = format_table(value)
                                text_content.extend(formatted_table)
                elif isinstance(table, str):
                    text_content.append(table)
        
        # Write to output file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(text_content))
            
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {json_file_path}")
        print(f"Details: {str(e)}")
        return False
    except Exception as e:
        print(f"Error processing {json_file_path}")
        print(f"Details: {str(e)}")
        return False

def process_directory(input_dir, output_dir):
    """
    Process all JSON files in the input directory and save converted text files to output directory.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all JSON files
    json_files = list(Path(input_dir).glob('**/*.json'))
    
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return
    
    # Process each JSON file
    success_count = 0
    for json_path in json_files:
        # Create corresponding output path
        relative_path = json_path.relative_to(input_dir)
        output_path = Path(output_dir) / relative_path.with_suffix('.txt')
        
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Converting {relative_path}...")
        if convert_json_to_text(str(json_path), str(output_path)):
            success_count += 1
            print(f"Successfully converted to {output_path}")
    
    print(f"\nConversion complete!")
    print(f"Successfully converted {success_count} out of {len(json_files)} files")

def main():
    # Get the directory of the script
    script_dir = Path(__file__).parent.absolute()
    
    # Set input and output directories
    input_dir = script_dir / 'data_done'
    output_dir = script_dir / 'text_output'
    
    # Check if input directory exists
    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        sys.exit(1)
    
    # Process the directory
    process_directory(input_dir, output_dir)

if __name__ == "__main__":
    main() 