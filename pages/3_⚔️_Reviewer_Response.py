import streamlit as st
from openai import OpenAI

# 设置页面配置
st.set_page_config(
    page_title="审稿意见回复助手",
    page_icon="⚔️",
    layout="wide"
)

# 页面标题
st.title("⚔️ 审稿意见回复助手")
st.markdown("---")

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

# 功能说明
st.markdown("### 📖 功能介绍")
st.markdown("""
审稿意见回复助手帮助你：
- 🎯 将真实的想法转化为专业的学术表达
- 💬 根据不同态度选择合适的回复策略
- ✍️ 生成结构化的审稿回复内容
- 📋 提供完整的回复模板和表达建议
""")

# 输入区域 A：审稿人意见
st.markdown("### 📝 审稿人意见 (Reviewer's Comment)")
reviewer_comment = st.text_area(
    "请粘贴审稿人的意见：",
    placeholder="例如：The authors should conduct additional experiments to validate their findings...",
    height=150,
    help="完整粘贴审稿人的具体意见和问题"
)

# 输入区域 B：用户真实想法
st.markdown("### 💭 我的真实想法 (My Raw Thoughts)")
raw_thoughts = st.text_area(
    "请输入你的真实想法（支持中文）：",
    placeholder="例如：这个实验没必要做，因为我们已经有足够的验证数据了；或者：我觉得这个建议很好，我们应该补充这部分内容...",
    height=120,
    help="坦诚表达你的真实想法，系统会帮你转化为专业表达"
)

# 态度策略选择
st.markdown("### 🎭 回复策略 (Tone Strategy)")
tone_strategy = st.slider(
    "选择回复态度：",
    min_value=1,
    max_value=3,
    value=2,
    step=1,
    format="%d. %s",
    help="滑动选择回复的语气和策略"
)

# 显示态度选项说明
tone_descriptions = {
    1: {
        "title": "全盘接受 (Accept & Thank)",
        "description": "完全接受审稿人意见，表示感谢并愿意修改",
        "style": "🟢 **合作态度**：体现对审稿意见的重视和积极配合"
    },
    2: {
        "title": "解释说明 (Clarify & Explain)",
        "description": "礼貌地解释可能存在的误会，提供更多上下文信息",
        "style": "🟡 **平衡态度**：保持尊重的同时说明实际情况"
    },
    3: {
        "title": "礼貌回怼 (Respectfully Disagree)",
        "description": "尊重地表达不同意见，提供充分的理由和证据",
        "style": "🔴 **专业态度**：基于学术原则进行专业讨论"
    }
}

col1, col2, col3 = st.columns(3)
with col1:
    if tone_strategy >= 1:
        st.success(tone_descriptions[1]["title"])
        st.caption(tone_descriptions[1]["style"])
with col2:
    if tone_strategy >= 2:
        st.warning(tone_descriptions[2]["title"])
        st.caption(tone_descriptions[2]["style"])
with col3:
    if tone_strategy >= 3:
        st.error(tone_descriptions[3]["title"])
        st.caption(tone_descriptions[3]["style"])

# 核心提示词系统
def get_system_prompt(tone_level):
    """根据态度级别生成系统提示词"""

    base_prompt = """You are an expert academic communications coach. Your goal is to help researchers write polite, professional, and convincing responses to reviewers."""

    tone_instructions = {
        1: """
        Tone Strategy: Accept & Thank (完全接受)
        - Express gratitude for the reviewer's valuable suggestion
        - Accept the feedback positively and constructively
        - Show willingness to make improvements
        - Use phrases like: "We thank the reviewer for this insightful suggestion...", "We agree that...", "We have revised..."
        """,

        2: """
        Tone Strategy: Clarify & Explain (解释说明)
        - Acknowledge the reviewer's concern respectfully
        - Provide additional context or clarification if needed
        - Explain the reasoning behind current approach
        - Use balanced phrases like: "We appreciate the reviewer's concern...", "We would like to clarify that...", "The rationale is..."
        """,

        3: """
        Tone Strategy: Respectfully Disagree (礼貌回怼)
        - Respect the reviewer's perspective while maintaining your position
        - Provide strong evidence and logical reasoning
        - Cite literature or established methodology when appropriate
        - Use confident but respectful language: "While we understand the reviewer's concern...", "However, based on our findings...", "Current literature supports..."
        """
    }

    structure_guide = """
    Response Structure:
    1. Acknowledgment: Start by thanking the reviewer
    2. The Response: Address the specific point with academic reasoning
    3. Action Taken: Describe what changes (if any) will be made

    Input Format:
    - Reviewer's comment
    - Your raw thoughts/true feelings

    Output Format:
    A complete, professional response in formal academic English.
    """

    return f"{base_prompt}\n\n{tone_instructions[tone_level]}\n\n{structure_guide}\n\nGenerate a complete, professional response based on the reviewer's comment and your raw thoughts."

# 构建用户提示词
def build_user_prompt(reviewer_comment, raw_thoughts, tone_level):
    """构建用户提示词"""

    prompt = f"""REVIEWER'S COMMENT:
{reviewer_comment}

MY RAW THOUGHTS:
{raw_thoughts}

TONE STRATEGY: {tone_descriptions[tone_level]['title']}

Please generate a professional response following the structure above."""

    return prompt

# 生成回复按钮
if st.button("🚀 生成回复", type="primary"):
    if reviewer_comment.strip() and raw_thoughts.strip():
        # 检查 API Key 配置
        client, error_msg = get_client()
        if error_msg:
            st.error(error_msg)
            st.info("请在左侧配置区域输入有效的 API Key")
            st.stop()

        # 构建提示词
        system_prompt = get_system_prompt(tone_strategy)
        user_prompt = build_user_prompt(reviewer_comment, raw_thoughts, tone_strategy)

        # 显示加载动画
        with st.spinner("正在生成专业的审稿回复，请稍候..."):
            try:
                # 调用 API
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.4
                )

                # 获取结果
                response_text = response.choices[0].message.content.strip()

                # 显示成功消息
                st.success("回复生成完成！")

                # 显示结果
                st.markdown("### 📄 生成的回复")

                # 格式化显示结果
                st.markdown(response_text)

                # 复制区域
                st.markdown("### 📋 复制回复")
                st.code(response_text, language=None)

                # 一键复制按钮
                st.markdown("---")
                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "📥 下载回复",
                        data=response_text,
                        file_name="reviewer_response.txt",
                        mime="text/plain"
                    )

                with col2:
                    st.markdown("💡 **使用提示**：复制上方文本框中的内容粘贴到回复文档中")

                # 显示完整提示词（学习用途）
                with st.expander("🔍 查看发送给 AI 的完整提示词"):
                    st.markdown("##### System Prompt:")
                    st.code(system_prompt, language=None)

                    st.markdown("##### User Prompt:")
                    st.code(user_prompt, language=None)

                    st.caption("💡 你可以学习这些提示词的写法，用于自己的项目中！")

                # 使用建议
                st.markdown("---")
                st.markdown("### 📚 使用建议")

                suggestion_cols = st.columns(3)
                with suggestion_cols[0]:
                    st.info("🎯 **针对性回复**")
                    st.caption("确保每个审稿意见都有具体回应")

                with suggestion_cols[1]:
                    st.warning("📝 **个性化调整**")
                    st.caption("根据实际情况微调生成的回复")

                with suggestion_cols[2]:
                    st.success("📊 **引用支持**")
                    st.caption("必要时添加文献或数据支持")

            except Exception as e:
                # 显示错误信息
                st.error(f"调用 API 时出现错误：{str(e)}")
                st.info("请检查网络连接、API Key 配置或稍后重试。")

    else:
        st.warning("请填写审稿人意见和你的真实想法！")

# 侧边栏高级设置
st.sidebar.markdown("### ⚙️ 高级设置")
temperature = st.sidebar.slider(
    "创造性 (Temperature):",
    min_value=0.0,
    max_value=1.0,
    value=0.4,
    step=0.1,
    help="控制回复的创造性，学术写作建议保持较低值"
)

max_tokens = st.sidebar.slider(
    "最大长度 (Tokens):",
    min_value=500,
    max_value=2000,
    value=1500,
    step=100,
    help="限制生成回复的最大长度"
)

# 显示当前配置
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 当前配置")
st.sidebar.write(f"**回复策略**: {tone_descriptions[tone_strategy]['title']}")
st.sidebar.write(f"**模型**: {model_name}")
st.sidebar.write(f"**Temperature**: {temperature}")
st.sidebar.write(f"**Max Tokens**: {max_tokens}")

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
1. 📋 **完整粘贴**审稿人原话
2. 💭 **坦诚表达**真实想法
3. 🎯 **选择合适**的回复策略
4. ✍️ **适当调整**生成的内容
5. 📚 **添加引用**支持论点
6. 📖 **多次使用**处理不同意见
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
⚔️ **审稿意见回复助手** - 专为科研工作者设计的专业回复工具
帮助您将真实想法转化为专业、礼貌、有说服力的学术表达
""")