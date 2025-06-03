import streamlit as st
import base64

# Helper to encode image to base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

bg_img_base64 = get_base64_of_bin_file('images/hcmiu-thu-duc-background.jpg')

# Set page config
st.set_page_config(
    page_title="HCMIU Information System",
    page_icon="🎓",
    layout="wide"
)

# Inject CSS for background and light font
st.markdown(f"""
    <style>
    /* Set background image */
    .stApp {{
        background: url("data:image/png;base64,{bg_img_base64}") no-repeat center center fixed;
        background-size: cover;
    }}
    /* Make all text lighter */
    html, body, [class^="css"] {{
        color: #f5f6fa !important;
        background-color: rgba(24,28,47,0.85) !important;
        text-shadow: 0 0 8px #23284d, 0 0 12px #23284d;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: #f5f6fa !important;
        text-shadow: 0 0 8px #23284d, 0 0 12px #23284d;
    }}
    .stTextInput>div>div>input {{
        background-color: #23284d;
        color: #f5f6fa;
        border-radius: 5px;
        border: 1px solid #444;
        text-shadow: 0 0 8px #23284d;
    }}
    .stButton>button {{
        background-color: #1a237e;
        color: #f5f6fa;
        text-shadow: 0 0 8px #23284d;
    }}
    .stButton>button:hover {{
        background-color: #0d47a1;
    }}
    .stSidebar, .css-1d391kg {{
        background-color: #23284d !important;
        color: #f5f6fa !important;
        text-shadow: 0 0 8px #23284d;
    }}
    /* Add blur/glow to all markdown text */
    .markdown-text-container, .stMarkdown, .stText, .stHeader, .stSubheader {{
        color: #f5f6fa !important;
        text-shadow: 0 0 8px #23284d, 0 0 12px #23284d;
    }}
    </style>
""", unsafe_allow_html=True)

# Custom CSS for university theme
st.markdown("""
<style>
    /* Main theme colors - you can adjust these */
    :root {
        --primary-color: #1a237e;  /* Deep blue */
        --secondary-color: #0d47a1;  /* Lighter blue */
        --accent-color: #ffc107;  /* Gold */
        --text-color: #333333;
        --background-color: #f5f5f5;
    }

    /* Main container */
    .main {
        background-color: var(--background-color);
    }

    /* Headers */
    h1, h2, h3 {
        color: var(--primary-color);
        font-family: 'Arial', sans-serif;
    }

    /* Cards */
    .stCard {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    /* Buttons */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
    }

    .stButton>button:hover {
        background-color: var(--secondary-color);
    }

    /* Input fields */
    .stTextInput>div>div>input {
        border-radius: 5px;
        border: 1px solid #ddd;
    }

    /* Sidebar */
    .css-1d391kg {
        background-color: var(--primary-color);
    }

    /* Background image */
    .main .block-container {
        background-image: url('images/hcmiu-thu-duc-background.png');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
</style>
""", unsafe_allow_html=True)

# Header with university logo and name
col1, col2 = st.columns([1, 3])
with col1:
    st.image("images/logo-vector-IU-01.png", width=150)
with col2:
    st.title("HCMIU - Đại học Quốc tế ĐHQG TP.HCM")
    st.subheader("Hệ thống Thông tin Sinh viên")

# Main content area (inside the frosted card)
st.markdown("---")
st.header("🔍 Tìm kiếm thông tin")
search_query = st.text_input("Nhập câu hỏi của bạn:", placeholder="Ví dụ: Điểm rèn luyện được tính như thế nào?")

st.header("📚 Danh mục thông tin")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    ### 🎓 Chương trình đào tạo
    - Cấu trúc chương trình
    - Môn học
    - Tín chỉ
    """)
with col2:
    st.markdown("""
    ### 📋 Quy định
    - Quy chế học tập
    - Quy định điểm rèn luyện
    - Quy định vi phạm
    """)
with col3:
    st.markdown("""
    ### 💰 Học phí
    - Chính sách học phí
    - Học bổng
    - Miễn giảm học phí
    """)

# Sidebar
with st.sidebar:
    st.header("ℹ️ Thông tin")
    st.markdown("""
    ### Giờ làm việc
    - Thứ 2 - Thứ 6: 8:00 - 17:00
    - Thứ 7: 8:00 - 12:00
    
    ### Liên hệ
    - Email: info@hcmiu.edu.vn
    - Điện thoại: (028) 3724 4270
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ### Hỗ trợ
    - Hướng dẫn sử dụng
    - Câu hỏi thường gặp
    - Góp ý
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>© 2024 HCMIU - Đại học Quốc tế ĐHQG TP.HCM. All rights reserved.</p>
</div>
""", unsafe_allow_html=True) 