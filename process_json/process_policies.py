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

def extract_chapters(text):
    """Extract chapters from text."""
    chapters = []
    
    # Split text into chapters
    chapter_pattern = r'Chương\s+[IVX]+\s*\n(.*?)(?=Chương\s+[IVX]+|$)'
    matches = re.finditer(chapter_pattern, text, re.DOTALL)
    
    for match in matches:
        chapter_text = match.group(1).strip()
        chapter_title = re.search(r'([^\n]+)', chapter_text).group(1).strip()
        
        # Extract articles from chapter
        articles = extract_articles(chapter_text)
        
        chapter = {
            'title': chapter_title,
            'articles': articles
        }
        
        chapters.append(chapter)
    
    return chapters

def extract_articles(text):
    """Extract articles from text."""
    articles = []
    
    # Split text into articles
    article_pattern = r'Điều\s+(\d+)\.\s*(.*?)(?=Điều\s+\d+\.|$)'
    matches = re.finditer(article_pattern, text, re.DOTALL)
    
    for match in matches:
        article_number = match.group(1)
        article_text = match.group(2).strip()
        
        # Extract article title and content
        title_match = re.search(r'([^\n]+)', article_text)
        title = clean_text(title_match.group(1)) if title_match else ""
        
        # Extract numbered points
        points = extract_points(article_text)
        
        article = {
            'id': article_number,
            'title': title,
            'content': points,
            'semantic_id': f"article_{article_number}"
        }
        
        articles.append(article)
    
    return articles

def extract_points(text):
    """Extract numbered points from text."""
    points = []
    
    # Split text into numbered points
    point_pattern = r'(\d+)\.\s*(.*?)(?=\d+\.|$)'
    matches = re.finditer(point_pattern, text, re.DOTALL)
    
    for match in matches:
        point_number = match.group(1)
        point_text = clean_text(match.group(2))
        
        point = {
            'id': point_number,
            'text': point_text,
            'semantic_id': f"point_{point_number}"
        }
        
        points.append(point)
    
    return points

def process_policy_file(file_path):
    """Process a policy text file into RAG-friendly format."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract header information
    header_match = re.search(r'(CHÍNH PHỦ.*?)(?=Chương\s+[IVX]+|$)', content, re.DOTALL)
    header = clean_text(header_match.group(1)) if header_match else ""
    
    # Extract chapters
    chapters = extract_chapters(content)
    
    # Create document structure
    document = {
        'document_id': f"policy_{file_path.stem}",
        'type': 'policy',
        'content': {
            'header': header,
            'chapters': chapters
        },
        'metadata': {
            'nguồn': file_path.name,
            'ngôn_ngữ': 'vi',
            'ngày_xử_lý': datetime.now().isoformat(),
            'phiên_bản': '1.0',
            'tổng_số_chương': len(chapters),
            'tổng_số_điều': sum(len(chapter['articles']) for chapter in chapters)
        }
    }
    
    return document

def main():
    # Define input and output paths
    input_files = [
        Path('data_done/8.txt')
    ]
    output_dir = Path('rag_data')
    output_dir.mkdir(exist_ok=True)
    
    for input_file in input_files:
        try:
            # Process policy file
            rag_document = process_policy_file(input_file)
            
            # Save processed document
            output_file = output_dir / f'rag_{input_file.stem}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(rag_document, f, ensure_ascii=False, indent=2)
                
            print(f"Successfully processed {input_file}")
            print(f"Total chapters processed: {len(rag_document['content']['chapters'])}")
            print(f"Total articles processed: {rag_document['metadata']['tổng_số_điều']}")
            print(f"Output saved to: {output_file}")
            
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")

if __name__ == "__main__":
    main() 