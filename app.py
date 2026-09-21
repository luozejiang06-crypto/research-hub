import streamlit as st
import os
from datetime import datetime
import pypdfium2 as pdfium
from PIL import Image
import numpy as np
from deep_translator import GoogleTranslator, MyMemoryTranslator
from rapidocr_onnxruntime import RapidOCR

st.set_page_config(
    page_title="金融研报智库",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

VAULT_DIR = "pdf_vault"
os.makedirs(VAULT_DIR, exist_ok=True)

# 初始化 OCR 引擎
@st.cache_resource
def load_ocr():
    return RapidOCR()

ocr_engine = load_ocr()

# ----------------- 主题配色 -----------------
THEMES = {
    "深蓝夜间": "radial-gradient(ellipse at 20% 20%, #0d1527 0%, #05070d 100%)",
    "极简纯黑": "linear-gradient(135deg, #090a0f 0%, #121620 100%)",
    "深海深蓝": "radial-gradient(circle at 50% 0%, #0f1c3f 0%, #060913 100%)",
    "暗黑暖棕": "linear-gradient(180deg, #0a0805 0%, #140e06 100%)"
}

# ----------------- 侧边栏：主题设置 -----------------
st.sidebar.markdown("<h4 style='color: #f59e0b;'>🎨 主题设置</h4>", unsafe_allow_html=True)
selected_theme = st.sidebar.selectbox("主题选择：", list(THEMES.keys()), index=0)
bg_style = f"background: {THEMES[selected_theme]};"

st.markdown(f"""
<style>
    html, body, [class*="css"], .stApp {{
        font-family: "Meiryo", "PingFang SC", "Microsoft YaHei", sans-serif !important;
        {bg_style}
        color: #f1f5f9 !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: rgba(6, 9, 16, 0.85) !important;
        border-right: 1px solid rgba(245, 158, 11, 0.25) !important;
    }}
    .terminal-title {{
        font-size: 1.8rem;
        font-weight: 800;
        color: #f1f5f9;
    }}
    .glass-card {{
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }}
    div[data-testid="stImage"] img {{
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 14px;
    }}
    textarea, input {{
        background-color: rgba(15, 23, 42, 0.9) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
    }}
</style>
""", unsafe_allow_html=True)

# ----------------- 顶栏：标题与三站互通导航条 -----------------
st.markdown("""
<div style="margin-bottom: 8px;">
    <span class="terminal-title">📑 金融研报智库</span>
</div>
<div style="display: flex; gap: 10px; margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px;">
    <a href="https://nikkei225-terminal-mzohipvya5trccentexb77.streamlit.app/" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 0.85rem; padding: 5px 12px; border-radius: 4px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25);">⚡ 日经225量化终端</a>
    <a href="https://lzjppy123.streamlit.app/" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 0.85rem; padding: 5px 12px; border-radius: 4px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25);">🇺🇸 标普500量化终端</a>
    <span style="color: #f59e0b; font-size: 0.85rem; padding: 5px 12px; border-radius: 4px; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); font-weight: bold;">📑 机构研报智库 (当前)</span>
</div>
""", unsafe_allow_html=True)

# ----------------- 翻译引擎 -----------------
@st.cache_data(ttl=86400)
def translate_text(text, src='auto', tgt='zh-CN'):
    if not text or not text.strip():
        return ""
    cleaned = " ".join(text.split())[:2000]
    try:
        res = GoogleTranslator(source=src, target=tgt).translate(cleaned)
        if res: return res
    except Exception:
        pass
    try:
        res = MyMemoryTranslator(source=src, target=tgt).translate(cleaned[:800])
        if res and "MYMEMORY" not in str(res).upper(): return res
    except Exception:
        pass
    return "翻译服务响应超时，请稍后重试。"

# ----------------- 侧边栏：研报文库与检索 -----------------
st.sidebar.markdown("<hr style='border: 1px solid rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
st.sidebar.markdown("<h4 style='color: #38bdf8;'>📁 研报搜索与上传</h4>", unsafe_allow_html=True)

all_files = sorted([f for f in os.listdir(VAULT_DIR) if f.lower().endswith('.pdf')])

# 监听来自日经/标普终端传递的股票代码参数
url_param = st.query_params.get("q", "")
search_query = st.sidebar.text_input("搜索研报名称：", value=url_param)
filtered_files = [f for f in all_files if search_query.lower() in f.lower()] if search_query else all_files

st.sidebar.caption(f"当前共有 {len(all_files)} 份研报 // 筛选出 {len(filtered_files)} 份")

with st.sidebar.expander("上传新研报 (PDF)", expanded=False):
    uploaded = st.file_uploader("选择或拖拽 PDF 文件：", type=["pdf"])
    if uploaded:
        target_path = os.path.join(VAULT_DIR, uploaded.name)
        with open(target_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"已上传：{uploaded.name}")
        st.rerun()

st.sidebar.markdown("<hr style='border: 1px solid rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
st.sidebar.markdown("<h4 style='color: #38bdf8;'>⚙️ 阅读设置</h4>", unsafe_allow_html=True)
view_mode = st.sidebar.radio("阅读模式：", ["单页翻页模式", "连续长图模式"], index=0)
render_scale = st.sidebar.select_slider("清晰度：", options=[1.5, 2.0, 2.5], value=2.0)

# ----------------- 主界面 -----------------
if not filtered_files:
    st.info("研报库中暂无匹配的 PDF 文件。可以在左侧上传，或将文件放入 `pdf_vault` 文件夹。")
else:
    selected_pdf_name = st.selectbox("选择要阅读的研报：", filtered_files, index=0)
    pdf_full_path = os.path.join(VAULT_DIR, selected_pdf_name)
    
    with open(pdf_full_path, "rb") as f:
        pdf_bytes = f.read()
    
    file_size_mb = round(len(pdf_bytes) / (1024 * 1024), 2)
    mod_time = datetime.fromtimestamp(os.path.getmtime(pdf_full_path)).strftime('%Y-%m-%d %H:%M')

    col_meta, col_act = st.columns([3, 1])
    with col_meta:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 1.1rem; font-weight: bold; color: #f1f5f9; word-break: break-all;">{selected_pdf_name}</div>
            <div style="color: #94a3b8; font-size: 0.82rem; margin-top: 6px;">
                更新时间: {mod_time} &nbsp;|&nbsp; 大小: {file_size_mb} MB
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_act:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.download_button(
            label="⬇️ 下载 PDF 原件",
            data=pdf_bytes,
            file_name=selected_pdf_name,
            mime="application/pdf",
            use_container_width=True
        )

    doc = pdfium.PdfDocument(pdf_full_path)
    total_pages = len(doc)

    # 左右双栏：左侧看原件，右侧直接一键识图翻译
    col_pdf, col_trans = st.columns([1.15, 1])

    with col_pdf:
        st.markdown("<h5 style='color: #38bdf8;'>📑 研报原件阅读</h5>", unsafe_allow_html=True)
        if view_mode == "单页翻页模式":
            page_num = st.slider("阅读页码：", min_value=1, max_value=total_pages, value=1)
            page = doc[page_num - 1]
            pil_img = page.render(scale=render_scale).to_pil()
            st.image(pil_img, caption=f"第 {page_num} / {total_pages} 页", use_container_width=True)
        else:
            page_num = 1
            st.caption(f"全文共 {total_pages} 页")
            for i in range(total_pages):
                page = doc[i]
                pil_img = page.render(scale=render_scale).to_pil()
                st.image(pil_img, caption=f"第 {i + 1} 页", use_container_width=True)

    with col_trans:
        st.markdown("<h5 style='color: #38bdf8;'>🌐 当前页原生识图与精译</h5>", unsafe_allow_html=True)
        st.caption(f"直接对正在阅读的 **第 {page_num} 页** 执行纯图像深度识别（无需截图，无视投行排版图层）：")

        if st.button(f"⚡ 提取并翻译第 {page_num} 页", use_container_width=True):
            with st.spinner("正在对当前页面进行 OCR 识图解析..."):
                # 获取当前查看的这一页渲染图
                curr_page = doc[page_num - 1]
                ocr_img = curr_page.render(scale=2.0).to_pil()
                img_np = np.array(ocr_img.convert('RGB'))
                
                # 直接通过 OCR 模型识别整页图像
                ocr_result, _ = ocr_engine(img_np)
                
                if not ocr_result:
                    st.warning("该页未识别出文字内容。")
                else:
                    lines = [item[1] for item in ocr_result]
                    full_page_text = "\n".join(lines)
                    st.session_state["curr_page_ocr"] = full_page_text
                    st.session_state["curr_page_zh"] = translate_text(full_page_text, tgt='zh-CN')

        if "curr_page_ocr" in st.session_state:
            st.markdown("<b>🇨🇳 中文翻译结果：</b>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid #10b981; font-size: 0.95rem; line-height: 1.7; max-height: 400px; overflow-y: auto;">
                {st.session_state["curr_page_zh"]}
            </div>
            """, unsafe_allow_html=True)

            with st.expander("查看识图提取到的原文 (OCR 文本)", expanded=False):
                st.text_area("提取文本：", value=st.session_state["curr_page_ocr"], height=200)

        st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.06); margin: 15px 0;'>", unsafe_allow_html=True)
        with st.expander("✂️ 手动上传局部截图翻译 (备用)", expanded=False):
            uploaded_snap = st.file_uploader("拖入局部截图：", type=["png", "jpg", "jpeg"])
            if uploaded_snap:
                snap_img = Image.open(uploaded_snap).convert('RGB')
                if st.button("识别该截图", use_container_width=True):
                    with st.spinner("识别中..."):
                        res, _ = ocr_engine(np.array(snap_img))
                        if res:
                            txt = "\n".join([x[1] for x in res])
                            zh = translate_text(txt, tgt='zh-CN')
                            st.markdown(f"<div class='glass-card' style='border-left: 4px solid #38bdf8;'>{zh}</div>", unsafe_allow_html=True)
