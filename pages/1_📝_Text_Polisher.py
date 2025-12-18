import streamlit as st
from openai import OpenAI

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

# 设置页面配置
st.set_page_config(
    page_title="学术润色",
    page_icon="📝",
    layout="wide"
)

# 页面标题
st.title("📝 学术润色")
st.markdown("---")

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

# 功能说明
st.markdown("### 🎯 功能介绍")
st.markdown("学术润色工具可以帮助您：")
st.markdown("""
- 优化语法和表达
- 提升学术写作规范性
- 改善句子结构和逻辑性
- 统一文风和表达方式
""")

# 输入区域
st.markdown("### ✏️ 输入文本")
input_text = st.text_area(
    "请输入需要润色的学术文本：",
    placeholder="在此输入您的学术论文段落、摘要或其他需要润色的文本...",
    height=200
)

# 选项设置
col1, col2 = st.columns(2)

with col1:
    text_type = st.selectbox(
        "文本类型：",
        ["论文摘要", "正文段落", "方法描述", "结果讨论", "结论", "其他"]
    )

with col2:
    language_style = st.selectbox(
        "润色风格：",
        ["正式学术", "简洁明了", "详细阐述", "保持原风格"]
    )

# 根据风格选择生成系统提示词
def get_system_prompt(style, text_type):
    style_prompts = {
        "正式学术": "You are an academic editor. Please rewrite the text to be more formal and suitable for scientific publication.",
        "简洁明了": "You are a technical editor. Please rewrite the text to be more concise and clear while maintaining academic rigor.",
        "详细阐述": "You are an academic writing expert. Please rewrite the text with more detailed explanations and better elaboration.",
        "保持原风格": "You are a language editor. Please improve the grammar and expression while preserving the original writing style."
    }

    type_contexts = {
        "论文摘要": "This is an abstract for a research paper.",
        "正文段落": "This is a main body paragraph of an academic paper.",
        "方法描述": "This is a methods section describing experimental procedures.",
        "结果讨论": "This is a results or discussion section.",
        "结论": "This is a conclusion section.",
        "其他": "This is general academic text."
    }

    base_prompt = f"{style_prompts[style]} {type_contexts[text_type]} "
    base_prompt += "Please return only the polished text without any additional explanations or formatting."

    return base_prompt

# 润色按钮
if st.button("🚀 开始润色", type="primary"):
    if input_text.strip():
        # 检查 API Key 配置
        client, error_msg = get_client()
        if error_msg:
            st.error(error_msg)
            st.info("请在左侧配置区域输入有效的 API Key")
            st.stop()

        # 生成系统提示词
        system_prompt = get_system_prompt(language_style, text_type)

        # 显示加载动画
        with st.spinner("正在使用 AI 润色文本，请稍候..."):
            try:
                # 调用 DeepSeek API
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": input_text}
                    ],
                    max_tokens=2000,
                    temperature=0.3
                )

                # 获取润色结果
                polished_text = response.choices[0].message.content.strip()

                # 显示成功消息
                st.success("润色完成！")

                # 显示结果
                st.markdown("### 📄 润色结果")
                polished_display = st.text_area(
                    "润色后的文本：",
                    value=polished_text,
                    height=200,
                    disabled=True
                )

                # 对比显示
                st.markdown("### 📊 对比分析")
                tab1, tab2 = st.tabs(["原文", "润色后"])

                with tab1:
                    st.markdown("**原文：**")
                    st.info(input_text)

                with tab2:
                    st.markdown("**润色后：**")
                    st.success(polished_text)

                # 操作按钮
                col_download, col_copy = st.columns(2)

                with col_download:
                    st.download_button(
                        "📥 下载润色结果",
                        data=polished_text,
                        file_name="polished_text.txt",
                        mime="text/plain"
                    )

                with col_copy:
                    # 简化的复制功能
                    st.code(polished_text, language=None)

            except Exception as e:
                # 显示错误信息
                st.error(f"调用 API 时出现错误：{str(e)}")
                st.info("请检查网络连接、API Key 配置或稍后重试。")

    else:
        st.warning("请先输入需要润色的文本！")

# 侧边栏高级设置
st.sidebar.markdown("### ⚙️ 高级设置")
formal_level = st.sidebar.slider("正式程度", 1, 5, 3)
technical_terms = st.sidebar.checkbox("保留专业术语", value=True)
keep_structure = st.sidebar.checkbox("保持原文结构", value=True)

# 显示当前配置
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 当前配置")
st.sidebar.write(f"**润色风格**: {language_style}")
st.sidebar.write(f"**文本类型**: {text_type}")
st.sidebar.write(f"**正式程度**: {formal_level}/5")
st.sidebar.write(f"**保留专业术语**: {'是' if technical_terms else '否'}")
st.sidebar.write(f"**保持结构**: {'是' if keep_structure else '否'}")

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
st.sidebar.markdown("### 📝 使用提示")
st.sidebar.info("""
1. 配置有效的 API Key
2. 确保 Base URL 正确
3. 选择合适的文本类型和风格
4. 根据需要调整高级设置
5. 检查润色结果并微调
6. 建议分段润色长文本
""")

# 添加使用统计
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 连接状态")
if get_valid_api_key():
    st.sidebar.success("✅ API Key 已配置")
    st.sidebar.write(f"🔗 Base URL: {user_base_url if user_base_url else 'https://api.deepseek.com'}")
else:
    st.sidebar.warning("⚠️ 需要配置 API Key")
    st.sidebar.info("请在左侧输入 API Key")
