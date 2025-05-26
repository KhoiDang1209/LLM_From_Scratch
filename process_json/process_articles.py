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

def process_articles(data):
    """Process articles into RAG-friendly format."""
    articles = []
    
    # Process main articles
    for article in data.get('articles', []):
        if not isinstance(article, dict):
            continue
            
        # Clean article data
        article_number = clean_text(article.get('number', ''))
        article_title = clean_text(article.get('title', ''))
        article_content = [clean_text(content) for content in article.get('content', [])]
        
        # Create article object
        article_obj = {
            'id': article_number,
            'title': article_title,
            'content': article_content,
            'semantic_id': f"article_{article_number.replace('.', '')}"
        }
        
        articles.append(article_obj)
    
    # Process sections if they exist
    sections = []
    for section in data.get('sections', []):
        if not isinstance(section, dict):
            continue
            
        # Clean section data
        section_number = clean_text(section.get('number', ''))
        section_text = clean_text(section.get('text', ''))
        section_level = section.get('level', 1)
        
        # Create section object
        section_obj = {
            'id': section_number,
            'text': section_text,
            'level': section_level,
            'semantic_id': f"section_{section_number.replace('.', '')}"
        }
        
        sections.append(section_obj)
    
    return articles, sections

def create_rag_document(articles, sections, source_file):
    """Create a RAG-friendly document structure."""
    document = {
        'document_id': f"quy_dinh_{source_file.stem}",
        'type': 'quy_dinh',
        'content': {
            'articles': articles,
            'sections': sections
        },
        'metadata': {
            'nguồn': source_file.name,
            'ngôn_ngữ': 'vi',
            'ngày_xử_lý': datetime.now().isoformat(),
            'phiên_bản': '1.0',
            'tổng_số_điều': len(articles),
            'tổng_số_mục': len(sections)
        }
    }
    
    return document

def main():
    # Define input and output paths
    input_files = [
        Path('text_output/12.json'),
        Path('text_output/13.json'),
        Path('text_output/14.json'),
        Path('text_output/15.json'),
        Path('text_output/16.json'),
        Path('text_output/17.json'),
        Path('text_output/18.json'),
    ]
    output_dir = Path('rag_data')
    output_dir.mkdir(exist_ok=True)
    
    for input_file in input_files:
        try:
            # Read input file
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process articles and sections
            articles, sections = process_articles(data)
            
            # Create RAG document
            rag_document = create_rag_document(articles, sections, input_file)
            
            # Save processed document
            output_file = output_dir / f'rag_{input_file.stem}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(rag_document, f, ensure_ascii=False, indent=2)
                
            print(f"Successfully processed {input_file}")
            print(f"Total articles processed: {len(articles)}")
            print(f"Total sections processed: {len(sections)}")
            print(f"Output saved to: {output_file}")
            
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")

if __name__ == "__main__":
    main() 