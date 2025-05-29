import re
import json
import os
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """Clean and normalize text while preserving newlines."""
    # Normalize Unicode characters
    text = text.encode('utf-8', 'ignore').decode('utf-8')
    # Remove extra whitespace but preserve newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove extra newlines
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def extract_chapters(text: str) -> List[Dict[str, Any]]:
    """Extract chapters from text."""
    chapters = []
    chapter_pattern = r'Chương\s+([IVX]+)\s*\n(.*?)(?=Chương\s+[IVX]+|$)'
    
    for match in re.finditer(chapter_pattern, text, re.DOTALL):
        chapter_num = match.group(1)
        chapter_content = match.group(2).strip()
        chapters.append({
            'id': chapter_num,
            'content': chapter_content,
            'semantic_id': f'chapter_{chapter_num}'
        })
    
    return chapters

def extract_articles(text: str) -> List[Dict[str, Any]]:
    """Extract articles from text."""
    articles = []
    article_pattern = r'Điều\s+(\d+)\.\s*(.*?)(?=Điều\s+\d+\.|$)'
    
    for match in re.finditer(article_pattern, text, re.DOTALL):
        article_num = match.group(1)
        article_content = match.group(2).strip()
        articles.append({
            'id': article_num,
            'content': article_content,
            'semantic_id': f'article_{article_num}'
        })
    
    return articles

def extract_points(text: str) -> List[Dict[str, Any]]:
    """Extract numbered points from text."""
    points = []
    # First split by numbered points
    point_pattern = r'(?:^|\n)(\d+)\.\s*(.*?)(?=(?:^|\n)\d+\.|$)'
    
    for match in re.finditer(point_pattern, text, re.DOTALL):
        point_num = match.group(1)
        point_content = match.group(2).strip()
        
        # Check if point has sub-points
        sub_points = extract_sub_points(point_content)
        
        # If sub-points exist, clean the main point text
        if sub_points:
            # Remove sub-point content from main text
            main_text = re.sub(r'[a-z]\)\s*.*?(?=[a-z]\)|$)', '', point_content, flags=re.DOTALL).strip()
            # Remove the "bao gồm:" or similar text that introduces sub-points
            main_text = re.sub(r'bao gồm:.*?(?=[a-z]\)|$)', '', main_text, flags=re.DOTALL).strip()
        else:
            main_text = point_content
        
        points.append({
            'id': point_num,
            'text': main_text,
            'semantic_id': f'point_{point_num}',
            'sub_points': sub_points
        })
    
    return points

def extract_sub_points(text: str) -> List[Dict[str, Any]]:
    """Extract sub-points from text."""
    sub_points = []
    lines = text.split('\n')
    current_sub_point = None
    current_content = []
    in_table = False
    table_content = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check for table start
        if is_table_start(line):
            in_table = True
            table_content = [line]
            continue
            
        # Handle table content
        if in_table:
            if is_table_line(line) or is_table_continuation(line, lines[i-1] if i > 0 else ''):
                table_content.append(line)
            else:
                in_table = False
                if current_sub_point:
                    current_content.append('\n'.join(table_content))
                table_content = []
                
        # Check for sub-point marker
        sub_point_match = re.match(r'([a-z])\)\s*(.*)', line)
        if sub_point_match:
            # Save previous sub-point if exists
            if current_sub_point:
                sub_points.append({
                    'id': current_sub_point,
                    'text': '\n'.join(current_content),
                    'semantic_id': f'sub_point_{current_sub_point}'
                })
            # Start new sub-point
            current_sub_point = sub_point_match.group(1)
            current_content = [sub_point_match.group(2)]
        elif current_sub_point:
            current_content.append(line)
    
    # Add last sub-point
    if current_sub_point:
        sub_points.append({
            'id': current_sub_point,
            'text': '\n'.join(current_content),
            'semantic_id': f'sub_point_{current_sub_point}'
        })
    
    return sub_points

def is_table_start(line: str) -> bool:
    """Check if line indicates start of a table."""
    return bool(re.match(r'^\s*Đơn vị:', line))

def is_table_line(line: str) -> bool:
    """Check if line is part of a table structure."""
    # Skip lines that are just numbers or decimal numbers
    if re.match(r'^\s*\d+(?:\.\d+)?\s*$', line):
        return False
    # Check for common table patterns
    return bool(re.match(r'^\s*(?:\d+\.\d+|\d+|[a-z]\))\s+', line))

def is_table_continuation(line: str, prev_line: str) -> bool:
    """Check if line is a continuation of a table row."""
    if not prev_line:
        return False
    # If previous line was a table row and current line is just a number or decimal
    if is_table_line(prev_line) and re.match(r'^\s*\d+(?:\.\d+)?\s*$', line):
        return True
    return False

def extract_sections_by_colon(text: str) -> List[Dict[str, Any]]:
    """Extract sections from text where sections are separated by colons."""
    sections = []
    current_section = None
    current_content = []
    in_department = False
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts with department markers
        if re.match(r'^(Phòng|Trung|Khoa)\s+.*:', line):
            # Save previous section if exists
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content),
                    'semantic_id': f'section_{len(sections) + 1}',
                    'type': 'department' if in_department else 'general'
                })
            # Start new department section
            current_section = line[:-1]  # Remove the colon
            current_content = []
            in_department = True
        # Check for numbered sections (like in EL_HCMIU.txt)
        elif re.match(r'^\d+\.\s+', line):
            # Save previous section if exists
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content),
                    'semantic_id': f'section_{len(sections) + 1}',
                    'type': 'department' if in_department else 'general'
                })
            # Start new numbered section
            current_section = line
            current_content = []
        # Check if line ends with colon (indicating a new general section)
        elif line.endswith(':') and not in_department:
            # Save previous section if exists
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content),
                    'semantic_id': f'section_{len(sections) + 1}',
                    'type': 'general'
                })
            # Start new section
            current_section = line[:-1]  # Remove the colon
            current_content = []
        elif current_section:
            current_content.append(line)
    
    # Add last section
    if current_section:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content),
            'semantic_id': f'section_{len(sections) + 1}',
            'type': 'department' if in_department else 'general'
        })
    
    return sections

def extract_course_sections(text: str) -> List[Dict[str, Any]]:
    """Extract sections from text with hierarchical structure."""
    sections = []
    current_faculty = None
    current_major = None
    current_year = None
    current_semester = None
    current_content = []
    current_section = None
    in_special_section = False
    special_section_content = []
    in_specialized_track = False
    current_track = None
    track_content = []
    in_roman_section = False
    current_roman_section = None
    roman_section_content = []
    in_elective_list = False
    current_elective = None
    elective_content = []
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for faculty (Khoa)
        if line.startswith('Khoa ') and line.endswith(':'):
            # Save previous sections if exists
            if current_semester and current_year:
                current_year['semesters'].append({
                    'title': current_semester,
                    'content': '\n'.join(current_content),
                    'semantic_id': f'semester_{len(current_year["semesters"]) + 1}'
                })
            if current_year and current_major:
                current_major['years'].append(current_year)
            if current_major and current_faculty:
                current_faculty['majors'].append(current_major)
            if current_faculty:
                sections.append(current_faculty)
            
            # Start new faculty
            current_faculty = {
                'title': line[:-1],
                'majors': [],
                'semantic_id': f'faculty_{len(sections) + 1}'
            }
            current_major = None
            current_year = None
            current_semester = None
            current_content = []
            current_section = None
            in_special_section = False
            special_section_content = []
            in_specialized_track = False
            current_track = None
            track_content = []
            in_roman_section = False
            current_roman_section = None
            roman_section_content = []
            in_elective_list = False
            current_elective = None
            elective_content = []
            
        # Check for major (Ngành)
        elif line.startswith('Ngành ') and line.endswith(':'):
            # Save previous sections if exists
            if current_semester and current_year:
                current_year['semesters'].append({
                    'title': current_semester,
                    'content': '\n'.join(current_content),
                    'semantic_id': f'semester_{len(current_year["semesters"]) + 1}'
                })
            if current_year and current_major:
                current_major['years'].append(current_year)
            if current_major and current_faculty:
                current_faculty['majors'].append(current_major)
            
            # Start new major
            current_major = {
                'title': line[:-1],
                'career_opportunities': '',
                'training_objectives': [],
                'years': [],
                'special_sections': {
                    'content': ''
                },
                'specialized_tracks': [],
                'roman_sections': [],
                'elective_courses': [],
                'semantic_id': f'major_{len(current_faculty["majors"]) + 1}' if current_faculty else 'major_1'
            }
            current_year = None
            current_semester = None
            current_content = []
            current_section = None
            in_special_section = False
            special_section_content = []
            in_specialized_track = False
            current_track = None
            track_content = []
            in_roman_section = False
            current_roman_section = None
            roman_section_content = []
            in_elective_list = False
            current_elective = None
            elective_content = []
            
        # Check for Roman numeral sections (I, II, III, etc.)
        elif re.match(r'^[IV]+\.\s+', line):
            # Save previous sections if exists
            if current_roman_section and roman_section_content:
                current_major['roman_sections'].append({
                    'title': current_roman_section,
                    'content': '\n'.join(roman_section_content),
                    'semantic_id': f'roman_section_{len(current_major["roman_sections"]) + 1}'
                })
            
            # Start new Roman section
            current_roman_section = line
            roman_section_content = []
            in_roman_section = True
            
        # Check for elective courses list
        elif line == 'Danh sách các môn học tự chọn,':
            # Save previous Roman section if exists
            if current_roman_section and roman_section_content:
                current_major['roman_sections'].append({
                    'title': current_roman_section,
                    'content': '\n'.join(roman_section_content),
                    'semantic_id': f'roman_section_{len(current_major["roman_sections"]) + 1}'
                })
            
            in_elective_list = True
            current_elective = None
            elective_content = []
            
        # Check for elective course sections
        elif in_elective_list and line.startswith('Môn tự chọn '):
            # Save previous elective if exists
            if current_elective and elective_content:
                current_major['elective_courses'].append({
                    'title': current_elective,
                    'content': '\n'.join(elective_content),
                    'semantic_id': f'elective_{len(current_major["elective_courses"]) + 1}'
                })
            
            # Start new elective section
            current_elective = line[:-1] if line.endswith(',') else line
            elective_content = []
            
        # Check for year (Năm X)
        elif line.startswith('Năm ') and line.endswith(':'):
            # Save previous sections if exists
            if current_semester and current_year:
                current_year['semesters'].append({
                    'title': current_semester,
                    'content': '\n'.join(current_content),
                    'semantic_id': f'semester_{len(current_year["semesters"]) + 1}'
                })
            if current_year and current_major:
                current_major['years'].append(current_year)
            
            # Start new year
            current_year = {
                'title': line[:-1],
                'semesters': [],
                'semantic_id': f'year_{len(current_major["years"]) + 1}' if current_major else 'year_1'
            }
            current_semester = None
            current_content = []
            current_section = None
            in_special_section = False
            
        # Check for semester (Học kì X)
        elif line.startswith('Học kì ') and line.endswith(':'):
            # Save previous semester if exists
            if current_semester and current_year:
                current_year['semesters'].append({
                    'title': current_semester,
                    'content': '\n'.join(current_content),
                    'semantic_id': f'semester_{len(current_year["semesters"]) + 1}'
                })
            
            # Start new semester
            current_semester = line[:-1]
            current_content = []
            current_section = None
            in_special_section = False
            
        # Check for section headers in major content
        elif current_major and (line.endswith(':') or line == 'Mục tiêu đào tạo' or line == 'Cơ hội nghề nghiệp'):
            # Save previous section content if exists
            if current_section and current_content:
                if current_section == 'Cơ hội nghề nghiệp':
                    current_major['career_opportunities'] = '\n'.join(current_content)
                elif current_section == 'Mục tiêu đào tạo':
                    current_major['training_objectives'] = current_content
            current_section = line[:-1] if line.endswith(':') else line
            current_content = []
            
        # Regular content line
        elif current_semester and current_year:
            current_content.append(line)
        elif current_year:
            # If we have content in a year but no semester, it might be a special section
            if current_content and not current_semester and not in_special_section:
                if current_major:
                    current_major['special_sections']['content'] = '\n'.join(current_content)
                current_content = []
            current_content.append(line)
        elif current_major:
            if in_elective_list:
                if current_elective:
                    elective_content.append(line)
            elif in_roman_section:
                roman_section_content.append(line)
            elif in_specialized_track:
                track_content.append(line)
            elif in_special_section:
                special_section_content.append(line)
            else:
                current_content.append(line)
        elif current_faculty:
            current_content.append(line)
    
    # Save last sections
    if current_semester and current_year:
        current_year['semesters'].append({
            'title': current_semester,
            'content': '\n'.join(current_content),
            'semantic_id': f'semester_{len(current_year["semesters"]) + 1}'
        })
    elif current_year and not current_semester and special_section_content:
        if current_year['title'] == 'Năm 5':
            if not current_year['semesters']:
                current_year['semesters'].append({
                    'title': 'Học kì 1',
                    'content': '\n'.join(current_content + special_section_content),
                    'semantic_id': 'semester_1'
                })
            else:
                current_year['semesters'][0]['content'] += '\n' + '\n'.join(special_section_content)
    
    # Save last Roman section
    if current_roman_section and roman_section_content:
        current_major['roman_sections'].append({
            'title': current_roman_section,
            'content': '\n'.join(roman_section_content),
            'semantic_id': f'roman_section_{len(current_major["roman_sections"]) + 1}'
        })
    
    # Save last elective
    if current_elective and elective_content:
        current_major['elective_courses'].append({
            'title': current_elective,
            'content': '\n'.join(elective_content),
            'semantic_id': f'elective_{len(current_major["elective_courses"]) + 1}'
        })
    
    # Save last track
    if current_track and track_content:
        current_major['specialized_tracks'].append({
            'title': current_track,
            'content': '\n'.join(track_content),
            'semantic_id': f'track_{len(current_major["specialized_tracks"]) + 1}'
        })
    
    if current_year and current_major:
        if current_content and not current_semester and not in_special_section:
            current_major['special_sections']['content'] = '\n'.join(current_content)
        current_major['years'].append(current_year)
    if current_major:
        if current_section and current_content:
            if current_section == 'Cơ hội nghề nghiệp':
                current_major['career_opportunities'] = '\n'.join(current_content)
            elif current_section == 'Mục tiêu đào tạo':
                current_major['training_objectives'] = current_content
        if current_faculty:
            current_faculty['majors'].append(current_major)
    if current_faculty:
        sections.append(current_faculty)
    
    return sections

def process_policy_file(file_path: str) -> Dict[str, Any]:
    """Process a policy text file into a structured format."""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Check if file is a course structure file
    if 'Khoa ' in text and 'Ngành ' in text:
        sections = extract_course_sections(text)
        document = {
            'document_id': os.path.splitext(os.path.basename(file_path))[0],
            'type': 'course_structure',
            'content': {
                'faculties': sections
            },
            'metadata': {
                'total_faculties': len(sections),
                'total_majors': sum(len(faculty['majors']) for faculty in sections),
                'total_years': sum(len(major['years']) for faculty in sections for major in faculty['majors']),
                'total_semesters': sum(
                    len(year['semesters'])
                    for faculty in sections
                    for major in faculty['majors']
                    for year in major['years']
                ),
                'total_roman_sections': sum(
                    len(major['roman_sections'])
                    for faculty in sections
                    for major in faculty['majors']
                ),
                'total_elective_courses': sum(
                    len(major['elective_courses'])
                    for faculty in sections
                    for major in faculty['majors']
                )
            }
        }
    # Check if file is in colon-separated format
    elif ':' in text and not re.search(r'Điều\s+\d+\.', text):
        sections = extract_sections_by_colon(text)
        document = {
            'document_id': os.path.splitext(os.path.basename(file_path))[0],
            'type': 'policy',
            'content': {
                'sections': sections
            },
            'metadata': {
                'total_sections': len(sections),
                'total_departments': sum(1 for section in sections if section['type'] == 'department'),
                'total_general_sections': sum(1 for section in sections if section['type'] == 'general')
            }
        }
    else:
        # Process as regular policy document with articles
        header_pattern = r'^(.*?)(?=\d+\.|Điều\s+1\.)'
        header_match = re.search(header_pattern, text, re.DOTALL)
        header = header_match.group(1).strip() if header_match else ''
        
        # Check if document has chapters and articles
        has_chapters = bool(re.search(r'Chương\s+[IVX]+', text))
        
        if has_chapters:
            # Process hierarchical document
            chapters = extract_chapters(text)
            for chapter in chapters:
                chapter['articles'] = extract_articles(chapter['content'])
                for article in chapter['articles']:
                    article['points'] = extract_points(article['content'])
            
            document = {
                'document_id': os.path.splitext(os.path.basename(file_path))[0],
                'type': 'policy',
                'content': {
                    'header': header,
                    'chapters': chapters
                },
                'metadata': {
                    'total_chapters': len(chapters),
                    'total_articles': sum(len(chapter['articles']) for chapter in chapters),
                    'total_points': sum(len(article['points']) for chapter in chapters for article in chapter['articles']),
                    'total_sub_points': sum(
                        sum(len(point['sub_points']) for point in article['points'])
                        for chapter in chapters for article in chapter['articles']
                    )
                }
            }
        else:
            # Process simple numbered list
            points = extract_points(text)
            
            document = {
                'document_id': os.path.splitext(os.path.basename(file_path))[0],
                'type': 'policy',
                'content': {
                    'header': header,
                    'points': points
                },
                'metadata': {
                    'total_points': len(points),
                    'total_sub_points': sum(len(point['sub_points']) for point in points)
                }
            }
    
    return document

def main():
    # Define input and output paths
    input_dir = 'data_done'
    output_dir = 'rag_data'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process files
    input_files = ['AS_HCMIU.txt']
    
    for file_name in input_files:
        input_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, f'rag_{os.path.splitext(file_name)[0]}.json')
        
        print(f'Processing {file_name}...')
        document = process_policy_file(input_path)
        
        # Save processed document
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
        
        print(f'Created {output_path}')

if __name__ == '__main__':
    main() 