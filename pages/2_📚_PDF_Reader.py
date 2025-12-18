import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
import io
import re

# 设置页面配置
st.set_page_config(
    page_title="文献速读助手",
    page_icon="📚",
    layout="wide"
)

# 侧边栏配置区域
st.sidebar.markdown("### 🔑 API 配置")

# 用户自定义 API Key
user_api_key = st.sidebar.text_input(
    "API Key:",
    type="password",
    placeholder="输入你的 DeepSeek API Key（留空使用系统默认）",
    help="如果留空，将尝试使用系统配置的默认 Key"
)

# 用户自定义 Base URL
user_base_url = st.sidebar.text_input(
    "Base URL:",
    value="https://api.deepseek.com",
    placeholder="API 服务地址",
    help="DeepSeek API 服务地址，通常为 https://api.deepseek.com"
)

# 模型选择
model_name = st.sidebar.selectbox(
    "Model:",
    options=["deepseek-chat", "deepseek-coder"],
    index=0,
    help="选择使用的模型"
)

st.sidebar.markdown("---")

# 获取有效的 API Key（优先级逻辑）
def get_valid_api_key():
    """获取有效的 API Key，按优先级：用户输入 > 系统配置 > None"""
    if user_api_key and user_api_key.strip():
        return user_api_key.strip()

    try:
        return st.secrets["DEEPSEEK_API_KEY"]
    except KeyError:
        return None

# 初始化 OpenAI 客户端
def get_client():
    """获取配置好的 OpenAI 客户端"""
    final_api_key = get_valid_api_key()
    final_base_url = user_base_url.strip() if user_base_url and user_base_url.strip() else "https://api.deepseek.com"

    if not final_api_key:
        return None, "请输入 API Key 或确保系统配置了默认 Key"

    try:
        client = OpenAI(
            api_key=final_api_key,
            base_url=final_base_url
        )
        return client, None
    except Exception as e:
        return None, f"初始化客户端失败：{str(e)}"

# API 配置状态显示
api_status_col, api_key_info_col = st.sidebar.columns([1, 2])
with api_status_col:
    if get_valid_api_key():
        st.success("✅")
    else:
        st.error("❌")

with api_key_info_col:
    if user_api_key:
        st.caption("使用自定义 Key")
    elif get_valid_api_key():
        st.caption("使用系统默认 Key")
    else:
        st.caption("未配置 Key")

st.sidebar.markdown("---")

# 页面标题
st.title("📚 沉浸式文献速读")
st.markdown("---")

# 功能说明
st.markdown("### 📖 功能介绍")
st.markdown("""
文献速读助手帮助你：
- 📄 **一键上传**: 直接上传 PDF 文献进行解析
- 📑 **结构化总结**: 快速提取研究空白、方法论和核心结论
- 💬 **论文对话**: 像聊天一样与论文内容进行互动问答
- 🎯 **精准定位**: 快速找到论文中的关键信息
""")

# 初始化 session_state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = ""

# 文件上传区
st.markdown("### 📁 文件上传")
uploaded_file = st.file_uploader(
    "选择 PDF 文件:",
    type="pdf",
    help="上传需要阅读的学术论文 PDF 文件"
)

# PDF 文本提取函数
def extract_text_from_pdf(uploaded_file):
    """从上传的 PDF 文件中提取文本"""
    try:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        page_count = len(pdf_reader.pages)

        # 提取每页文本
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"

        # 清理文本（移除多余的空白字符）
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text, page_count
    except Exception as e:
        return None, 0

# 处理文件上传
if uploaded_file is not None:
    if st.session_state.pdf_filename != uploaded_file.name:
        with st.spinner("正在解析 PDF 文件..."):
            pdf_text, page_count = extract_text_from_pdf(uploaded_file)

            if pdf_text is not None:
                # 如果文本超过 20,000 字，进行截取
                max_length = 20000
                if len(pdf_text) > max_length:
                    pdf_text = pdf_text[:max_length] + f"\n\n[注意：文本已截取至 {max_length} 字符，完整内容请参考原文件]"
                    st.warning(f"📄 文本过长（{len(pdf_text)} 字符），已截取至 {max_length} 字符用于分析")

                st.session_state.pdf_text = pdf_text
                st.session_state.pdf_filename = uploaded_file.name

                # 显示提取结果
                st.success(f"✅ 成功提取 {page_count} 页，共 {len(pdf_text)} 字符")

                # 显示部分预览
                with st.expander("📋 文本预览"):
                    preview_text = pdf_text[:1000] + "..." if len(pdf_text) > 1000 else pdf_text
                    st.text_area("PDF 文本预览:", preview_text, height=200, disabled=True)

            else:
                st.error("❌ PDF 文件解析失败，请确保文件格式正确")

# 功能选择区
if st.session_state.pdf_text:
    st.markdown("---")
    st.markdown("### 🎯 功能选择")

    # 使用列布局
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📑 生成核心摘要", type="primary", use_container_width=True):
            st.markdown("---")
            st.markdown("### 📄 结构化总结")

            # 检查 API Key 配置
            client, error_msg = get_client()
            if error_msg:
                st.error(error_msg)
                st.info("请在左侧配置区域输入有效的 API Key")
                st.stop()

            # 构建总结提示词
            summary_prompt = """请阅读这篇学术论文，并严格按照以下结构进行总结，用中文回答：

1. **研究空白 (Research Gap)**
   - 现有研究的不足之处
   - 作者试图解决的具体问题
   - 研究的重要性和必要性

2. **方法论 (Methodology)**
   - 主要研究方法和技术路线
   - 实验设计和数据收集方式
   - 分析方法和验证手段

3. **核心结论 (Key Results)**
   - 主要发现和创新点
   - 数据支持的重要结论
   - 研究的理论和实践意义

请确保回答准确、简洁、专业。"""

            with st.spinner("正在生成结构化总结..."):
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "你是一个专业的学术文献分析师，擅长从学术论文中提取关键信息并进行结构化总结。"},
                            {"role": "user", "content": f"{summary_prompt}\n\n论文内容：\n{st.session_state.pdf_text}"}
                        ],
                        max_tokens=2000,
                        temperature=0.3
                    )

                    summary_result = response.choices[0].message.content.strip()

                    # 显示总结结果
                    st.markdown(summary_result)

                    # 下载按钮
                    st.download_button(
                        "📥 下载总结",
                        data=summary_result,
                        file_name=f"{st.session_state.pdf_filename}_总结.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"生成总结时出现错误：{str(e)}")
                    st.info("请检查网络连接、API Key 配置或稍后重试。")

    with col2:
        st.markdown("### 💬 论文对话模式")
        st.info("💡 **使用提示**: 上传 PDF 后，你可以在下方与论文进行智能对话")
        st.caption("• 这篇论文的主要贡献是什么？")
        st.caption("• 实验结果如何支持结论？")
        st.caption("• 研究方法有什么局限性？")

# 论文对话界面
if st.session_state.pdf_text:
    st.markdown("---")
    st.markdown("### 💬 论文对话")
    st.info("💡 **使用提示**: 你可以询问关于论文内容的任何问题，例如：")
    st.caption("• 这篇论文的主要贡献是什么？")
    st.caption("• 实验结果如何支持结论？")
    st.caption("• 研究方法有什么局限性？")

    # 清除对话按钮
    if st.session_state.messages:
        if st.button("🗑️ 清除对话历史", type="secondary"):
            st.session_state.messages = []
            st.rerun()

    # 显示对话历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 用户输入
    if prompt := st.chat_input("请输入你想了解的问题："):
        # 添加用户消息到对话历史
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # 检查 API Key 配置
        client, error_msg = get_client()
        if error_msg:
            st.error(error_msg)
            st.info("请在左侧配置区域输入有效的 API Key")
        else:
            with st.chat_message("assistant"):
                with st.spinner("正在思考回答..."):
                    try:
                        # 构建对话提示词
                        chat_prompt = f"""你是一个专业的学术顾问，正在帮助用户理解一篇学术论文。

Context: 以下是论文的完整内容：
{st.session_state.pdf_text}

User Question: {prompt}

请基于论文内容回答用户的问题。如果论文中没有相关信息，请诚实说明。回答要准确、专业、有帮助。"""

                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": "你是一个专业的学术顾问，擅长解读学术论文并回答相关问题。"},
                                {"role": "user", "content": chat_prompt}
                            ],
                            max_tokens=1500,
                            temperature=0.3
                        )

                        assistant_response = response.choices[0].message.content.strip()
                        st.markdown(assistant_response)

                        # 添加助手回复到对话历史
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

                    except Exception as e:
                        error_message = f"生成回答时出现错误：{str(e)}"
                        st.error(error_message)
                        st.session_state.messages.append({"role": "assistant", "content": error_message})

# 侧边栏高级设置
st.sidebar.markdown("### ⚙️ 高级设置")
temperature = st.sidebar.slider(
    "创造性 (Temperature):",
    min_value=0.0,
    max_value=1.0,
    value=0.3,
    step=0.1,
    help="控制回答的创造性，学术分析建议保持较低值"
)

max_tokens = st.sidebar.slider(
    "最大长度 (Tokens):",
    min_value=500,
    max_value=4000,
    value=2000,
    step=100,
    help="限制生成内容的最大长度"
)

# 显示当前配置
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 当前配置")
st.sidebar.write(f"**模型**: {model_name}")
st.sidebar.write(f"**Temperature**: {temperature}")
st.sidebar.write(f"**Max Tokens**: {max_tokens}")

if st.session_state.pdf_filename:
    st.sidebar.write(f"**当前文件**: {st.session_state.pdf_filename}")
    st.sidebar.write(f"**文本长度**: {len(st.session_state.pdf_text)} 字符")

# API 配置详情
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 API 配置详情")
with st.sidebar.expander("查看配置详情"):
    if user_api_key:
        st.code(f"自定义 Key: {user_api_key[:10]}...{user_api_key[-4:]}", language=None)
    elif get_valid_api_key():
        st.code("使用系统默认 Key", language=None)
    else:
        st.code("未配置", language=None)
    st.code(f"Base URL: {user_base_url if user_base_url else 'https://api.deepseek.com'}", language=None)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 使用技巧")
st.sidebar.info("""
1. 📄 **上传清晰**的 PDF 文件
2. 📑 **先看摘要**了解整体内容
3. 💬 **精准提问**获得更好回答
4. 🔍 **追问细节**深入了解内容
5. 📋 **总结下载**保存关键信息
""")

# 连接状态
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 连接状态")
if get_valid_api_key():
    st.sidebar.success("✅ API Key 已配置")
    st.sidebar.write(f"🔗 Base URL: {user_base_url if user_base_url else 'https://api.deepseek.com'}")
else:
    st.sidebar.warning("⚠️ 需要配置 API Key")
    st.sidebar.info("请在左侧输入 API Key")

# 页脚信息
st.markdown("---")
st.markdown("### 📖 关于")
st.caption("""
📚 **沉浸式文献速读** - 智能化论文阅读助手
帮助你快速理解学术论文，提取关键信息，提升阅读效率
""")