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

# 主界面：功能模式选择
st.markdown("### 🎯 选择功能模式")
mode = st.radio(
    "选择润色模式：",
    options=[
        "✨ Standard Polish (标准润色)",
        "🛡️ Humanize / De-AIGC (降 AI 痕迹)",
        "🎭 Style Mimic (风格仿写)"
    ],
    index=0,
    help="选择不同的润色模式和策略"
)

# 提取模式类型
if "Standard Polish" in mode:
    mode_type = "standard"
elif "Humanize" in mode:
    mode_type = "humanize"
else:
    mode_type = "style_mimic"

# 动态显示模式说明
mode_descriptions = {
    "standard": "📝 **标准学术润色**：优化语法、提升表达规范性、改善句子结构",
    "humanize": "🔥 **去 AI 痕迹**：增加文本人性化特征、避免 AI 常用词汇、模仿真实写作节奏",
    "style_mimic": "🎨 **风格仿写**：分析参考文本的写作风格，将待润色文本改写成相同风格"
}

st.info(mode_descriptions[mode_type])

# 输入区域
st.markdown("### ✏️ 输入文本")

# 待润色文本（所有模式都需要）
input_text = st.text_area(
    "待润色文本 (Draft Text):",
    placeholder="在此输入您需要润色的学术文本...",
    height=200,
    help="请输入需要处理的学术论文段落、摘要或其他文本"
)

# 参考文本（仅风格仿写模式需要）
reference_text = ""
if mode_type == "style_mimic":
    st.markdown("#### 📚 风格参考 (Style Reference)")
    reference_text = st.text_area(
        "参考文本 (Reference Text):",
        placeholder="粘贴一段你想要模仿的期刊段落、论文引言或任何具有目标风格的文本...",
        height=150,
        help="参考文本用于分析目标写作风格，建议选择 200-500 字的段落"
    )

# 选项设置（根据模式动态显示）
if mode_type == "standard":
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

# 核心提示词系统
def get_system_prompt(mode_type, additional_config=None):
    """获取不同模式的系统提示词"""

    base_prompts = {
        "standard": {
            "base": "You are an expert academic editor and writing consultant.",
            "tasks": {
                "论文摘要": "polish this abstract for clarity, impact, and academic rigor",
                "正文段落": "improve this main body paragraph for better flow and academic expression",
                "方法描述": "enhance this methods section for clarity and precision",
                "结果讨论": "refine this results/discussion section for better analytical depth",
                "结论": "strengthen this conclusion section for impact and completeness",
                "其他": "improve this academic text for overall quality"
            },
            "styles": {
                "正式学术": "Use formal academic language suitable for scientific publication",
                "简洁明了": "Make the text more concise while maintaining academic rigor",
                "详细阐述": "Add depth and detailed explanations where appropriate",
                "保持原风格": "Preserve the original writing style while improving expression"
            }
        },

        "humanize": {
            "base": """You are an expert at humanizing AI-generated text. Your task is to make text sound more naturally written by humans.

            Increase burstiness and perplexity. Avoid clichéd AI words like 'delve', 'realm', 'underscore', 'paramount'.
            Use a mix of short, punchy sentences and complex clauses to mimic human writing rhythm.
            Vary sentence length and structure. Include natural-sounding transitions and occasional rhetorical devices.
            Remove overly formal or stilted language that sounds artificial."""
        },

        "style_mimic": {
            "base": """You are a linguistic expert skilled at analyzing and mimicking writing styles.

            Your task is to carefully analyze the writing style, tone, vocabulary choices, sentence structure,
            and rhetorical devices in a reference text, then rewrite a draft text to match that style exactly."""
        }
    }

    if mode_type == "standard":
        text_type = additional_config.get("text_type", "其他")
        language_style = additional_config.get("language_style", "保持原风格")

        task = base_prompts["standard"]["tasks"][text_type]
        style = base_prompts["standard"]["styles"][language_style]

        return f"{base_prompts['standard']['base']} Please {task}. {style}. Return only the polished text without explanations."

    elif mode_type == "humanize":
        return f"{base_prompts['humanize']['base']} Rewrite the given text to sound naturally human-written, maintaining the original meaning and academic content. Return only the rewritten text."

    elif mode_type == "style_mimic":
        return f"{base_prompts['style_mimic']['base']} Analyze the writing style of the reference text and rewrite the draft text to match that style precisely, without changing the core meaning. Return only the rewritten text."

# 构建用户提示词
def build_user_prompt(mode_type, draft_text, reference_text="", additional_config=None):
    """构建用户提示词"""

    if mode_type == "standard":
        text_type = additional_config.get("text_type", "其他")
        language_style = additional_config.get("language_style", "保持原风格")

        context = f"Text Type: {text_type}\nTarget Style: {language_style}\n\n"
        return context + f"Text to polish:\n{draft_text}"

    elif mode_type == "humanize":
        return f"Please humanize this academic text to remove any AI-like patterns:\n{draft_text}"

    elif mode_type == "style_mimic":
        return f"""REFERENCE TEXT (analyze this style):
{reference_text}

DRAFT TEXT (rewrite in reference style):
{draft_text}"""

# 润色按钮
if st.button("🚀 开始润色", type="primary"):
    if input_text.strip():
        # 检查模式特定要求
        if mode_type == "style_mimic" and not reference_text.strip():
            st.error("🎭 风格仿写模式需要提供参考文本！")
            st.stop()

        # 检查 API Key 配置
        client, error_msg = get_client()
        if error_msg:
            st.error(error_msg)
            st.info("请在左侧配置区域输入有效的 API Key")
            st.stop()

        # 构建提示词
        if mode_type == "standard":
            additional_config = {
                "text_type": text_type,
                "language_style": language_style
            }
        else:
            additional_config = {}

        system_prompt = get_system_prompt(mode_type, additional_config)
        user_prompt = build_user_prompt(mode_type, input_text, reference_text, additional_config)

        # 显示加载动画
        with st.spinner(f"正在进行{mode}处理，请稍候..."):
            try:
                # 调用 API
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=3000,
                    temperature=0.3 if mode_type == "standard" else 0.5
                )

                # 获取结果
                result_text = response.choices[0].message.content.strip()

                # 显示成功消息
                st.success("润色完成！")

                # 显示结果
                st.markdown("### 📄 处理结果")
                result_display = st.text_area(
                    "润色后的文本：",
                    value=result_text,
                    height=200,
                    disabled=True
                )

                # 对比显示
                st.markdown("### 📊 对比分析")
                if mode_type == "style_mimic":
                    tab1, tab2, tab3 = st.tabs(["原文", "参考风格", "润色后"])

                    with tab1:
                        st.markdown("**原文：**")
                        st.info(input_text)

                    with tab2:
                        st.markdown("**参考文本：**")
                        st.warning(reference_text)

                    with tab3:
                        st.markdown("**仿写结果：**")
                        st.success(result_text)
                else:
                    tab1, tab2 = st.tabs(["原文", "润色后"])

                    with tab1:
                        st.markdown("**原文：**")
                        st.info(input_text)

                    with tab2:
                        if mode_type == "humanize":
                            st.markdown("**去 AI 痕迹后：**")
                        else:
                            st.markdown("**润色后：**")
                        st.success(result_text)

                # 操作按钮
                col_download, col_copy = st.columns(2)

                with col_download:
                    suffix = "_style_mimic" if mode_type == "style_mimic" else "_humanized" if mode_type == "humanize" else "_polished"
                    st.download_button(
                        "📥 下载结果",
                        data=result_text,
                        file_name=f"academic_text{suffix}.txt",
                        mime="text/plain"
                    )

                with col_copy:
                    st.code(result_text, language=None)

                # 显示完整提示词（学习用途）
                with st.expander("🔍 查看发送给 AI 的完整提示词"):
                    st.markdown("##### System Prompt:")
                    st.code(system_prompt, language=None)

                    st.markdown("##### User Prompt:")
                    st.code(user_prompt, language=None)

                    st.caption("💡 提示：你可以学习这些提示词的写法，用于自己的项目中！")

            except Exception as e:
                # 显示错误信息
                st.error(f"调用 API 时出现错误：{str(e)}")
                st.info("请检查网络连接、API Key 配置或稍后重试。")

    else:
        st.warning("请先输入需要润色的文本！")

# 侧边栏高级设置
st.sidebar.markdown("### ⚙️ 高级设置")
temperature = st.sidebar.slider(
    "创造性 (Temperature):",
    min_value=0.0,
    max_value=1.0,
    value=0.3 if mode_type == "standard" else 0.5,
    step=0.1,
    help="控制输出的创造性，数值越高越有创意"
)

max_tokens = st.sidebar.slider(
    "最大长度 (Tokens):",
    min_value=500,
    max_value=4000,
    value=2000,
    step=100,
    help="限制生成文本的最大长度"
)

# 显示当前配置
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 当前配置")
st.sidebar.write(f"**功能模式**: {mode}")
st.sidebar.write(f"**模型**: {model_name}")
st.sidebar.write(f"**Temperature**: {temperature}")
st.sidebar.write(f"**Max Tokens**: {max_tokens}")

if mode_type == "standard":
    st.sidebar.write(f"**文本类型**: {text_type}")
    st.sidebar.write(f"**润色风格**: {language_style}")

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
if mode_type == "standard":
    st.sidebar.info("""
1. 配置有效的 API Key
2. 选择合适的文本类型和风格
3. 输入待润色文本
4. 调整高级设置参数
5. 查看结果并学习提示词技巧
""")
elif mode_type == "humanize":
    st.sidebar.info("""
1. 适用于去除 AI 生成痕迹
2. 增加文本的节奏感和自然度
3. 避免常见的 AI 写作模式
4. 保持原文的学术内容
5. 可适当提高温度参数
""")
else:
    st.sidebar.info("""
1. 准备目标风格的参考文本
2. 输入需要改写的原文
3. 参考文本建议 200-500 字
4. 确保两段文本主题相关
5. 查看风格分析结果
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
