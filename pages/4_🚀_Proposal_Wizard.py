import streamlit as st
from openai import OpenAI
import json
from datetime import datetime

# 设置页面配置
st.set_page_config(
    page_title="智能开题报告向导",
    page_icon="🚀",
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

# 页面标题
st.title("🚀 智能开题报告向导")
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

# 初始化状态管理
def init_session_state():
    """初始化 session_state"""
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'data' not in st.session_state:
        st.session_state.data = {
            'idea': '',
            'hypotheses': [],
            'selected_hypothesis': None,
            'methodology': None,
            'final_proposal': '',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# 初始化
init_session_state()

# 进度条显示
def show_progress():
    """显示进度条"""
    progress = (st.session_state.step - 1) / 2
    st.progress(progress)
    st.markdown(f"**当前进度**: 步骤 {st.session_state.step} / 3")

# 功能说明
st.markdown("### 📖 工作流介绍")
st.markdown("""
🎯 **智能开题报告向导**采用结构化工作流，助你从模糊想法到完整开题报告：

1. **💡 灵感风暴**: 将模糊想法转化为科学假设
2. **🔬 方法论构建**: 选择最适合的技术路线
3. **📄 终稿生成**: 自动生成完整的开题报告文档
""")

# 显示进度条
show_progress()

# API Key 检查
client, error_msg = get_client()
if error_msg and st.session_state.step == 1:
    st.error("⚠️ 请先在左侧配置有效的 API Key！")
    st.stop()

# Step 1: 灵感风暴 (Idea & Hypotheses)
def step1_idea_burst():
    """Step 1: 灵感风暴"""
    st.markdown("---")
    st.markdown("### 💡 Step 1: 灵感风暴")
    st.markdown("请描述你的研究想法，即使是模糊的想法也可以！")

    # 输入研究想法
    idea_input = st.text_area(
        "你的研究想法:",
        placeholder="例如：我想研究如何利用 AI 提高医疗诊断的准确性...",
        height=120,
        value=st.session_state.data['idea'],
        help="尽可能详细地描述你的研究想法，包括研究背景、目标、挑战等"
    )

    # 保存想法
    st.session_state.data['idea'] = idea_input

    # 生成假设按钮
    if st.button("🧠 生成科学假设", type="primary", disabled=not idea_input.strip()):
        with st.spinner("正在分析并生成科学假设..."):
            try:
                prompt = f"""基于以下研究想法，请生成3个具体的、可验证的科学假设，每个假设都包含：
1. 明确的研究问题
2. 具体的创新点
3. 研究的可行性分析

研究想法：{idea_input}

请以JSON格式返回，格式如下：
{{
    "hypotheses": [
        {{
            "id": 1,
            "hypothesis": "具体的假设描述",
            "innovation": "创新点说明",
            "feasibility": "可行性分析"
        }},
        {{
            "id": 2,
            "hypothesis": "具体的假设描述",
            "innovation": "创新点说明",
            "feasibility": "可行性分析"
        }},
        {{
            "id": 3,
            "hypothesis": "具体的假设描述",
            "innovation": "创新点说明",
            "feasibility": "可行性分析"
        }}
    ]
}}"""

                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的科研顾问，擅长将模糊的想法转化为具体的科学假设。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )

                result = response.choices[0].message.content.strip()

                # 解析JSON
                try:
                    hypotheses_data = json.loads(result)
                    st.session_state.data['hypotheses'] = hypotheses_data['hypotheses']
                    st.success("✅ 成功生成3个科学假设！")
                except json.JSONDecodeError:
                    st.error("解析AI回复时出错，请重试")
                    st.code(result)

            except Exception as e:
                st.error(f"生成假设时出现错误：{str(e)}")

    # 显示假设卡片
    if st.session_state.data['hypotheses']:
        st.markdown("### 🎯 选择最适合的假设")

        cols = st.columns(3)
        for i, hypothesis in enumerate(st.session_state.data['hypotheses']):
            with cols[i]:
                with st.container():
                    st.markdown(f"#### 假设 {hypothesis['id']}")
                    st.markdown(f"**假设描述**: {hypothesis['hypothesis']}")
                    st.markdown(f"**创新点**: {hypothesis['innovation']}")
                    st.markdown(f"**可行性**: {hypothesis['feasibility']}")

                    if st.button(f"选择此假设", key=f"select_hypo_{hypothesis['id']}"):
                        st.session_state.data['selected_hypothesis'] = hypothesis
                        st.session_state.step = 2
                        st.rerun()

# Step 2: 方法论构建 (Methodology)
def step2_methodology():
    """Step 2: 方法论构建"""
    st.markdown("---")
    st.markdown("### 🔬 Step 2: 方法论构建")

    selected_hypo = st.session_state.data['selected_hypothesis']
    st.markdown(f"**当前选择的假设**: {selected_hypo['hypothesis']}")

    # 生成技术路线按钮
    if st.button("🛠️ 生成技术路线", type="primary"):
        with st.spinner("正在设计技术路线..."):
            try:
                prompt = f"""基于以下研究假设，请生成2种不同的技术路线方案：

研究假设：{selected_hypo['hypothesis']}
创新点：{selected_hypo['innovation']}

请生成：
1. **低成本方案**: 适合有限预算和资源的情况
2. **高精度方案**: 追求最高精度和最可靠的结果

请以JSON格式返回，格式如下：
{{
    "routes": [
        {{
            "type": "低成本方案",
            "description": "详细的技术路线描述",
            "advantages": "优势分析",
            "limitations": "局限性",
            "estimated_cost": "预估成本",
            "timeline": "预期时间"
        }},
        {{
            "type": "高精度方案",
            "description": "详细的技术路线描述",
            "advantages": "优势分析",
            "limitations": "局限性",
            "estimated_cost": "预估成本",
            "timeline": "预期时间"
        }}
    ]
}}"""

                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的研究方法学家，擅长设计可行的研究方案和技术路线。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2500,
                    temperature=0.5
                )

                result = response.choices[0].message.content.strip()

                try:
                    methodology_data = json.loads(result)
                    st.session_state.data['methodology'] = methodology_data['routes']
                    st.success("✅ 成功生成技术路线方案！")
                except json.JSONDecodeError:
                    st.error("解析AI回复时出错，请重试")
                    st.code(result)

            except Exception as e:
                st.error(f"生成技术路线时出现错误：{str(e)}")

    # 显示技术路线选择
    if st.session_state.data['methodology']:
        st.markdown("### 🎛️ 选择技术路线")

        selected_route = st.radio(
            "请选择最适合的技术路线:",
            options=[route['type'] for route in st.session_state.data['methodology']],
            help="根据你的预算、时间和精度要求选择合适的方案"
        )

        # 显示选中方案的详细信息
        for route in st.session_state.data['methodology']:
            if route['type'] == selected_route:
                with st.expander(f"📋 {selected_route} 详情", expanded=True):
                    st.markdown(f"**方案描述**: {route['description']}")
                    st.markdown(f"**优势**: {route['advantages']}")
                    st.markdown(f"**局限性**: {route['limitations']}")
                    st.markdown(f"**预估成本**: {route['estimated_cost']}")
                    st.markdown(f"**预期时间**: {route['timeline']}")

                # 允许用户微调
                st.markdown("### ✏️ 微调方案")
                custom_methodology = st.text_area(
                    "如果你有任何修改或补充，请在这里说明:",
                    placeholder="例如：我想添加更多的实验组，或者调整某些参数...",
                    height=100
                )

                if custom_methodology:
                    # 保存用户的微调
                    route['custom_modifications'] = custom_methodology
                    st.success("✅ 已保存你的微调方案")

# Step 3: 终稿生成与导出 (Assembly & Export)
def step3_final_export():
    """Step 3: 终稿生成与导出"""
    st.markdown("---")
    st.markdown("### 📄 Step 3: 终稿生成与导出")

    # 显示选择总结
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🎯 选中的研究假设")
        st.markdown(f"**假设**: {st.session_state.data['selected_hypothesis']['hypothesis']}")
        st.markdown(f"**创新点**: {st.session_state.data['selected_hypothesis']['innovation']}")

    with col2:
        st.markdown("#### 🔧 选中的技术路线")
        selected_route_type = st.radio("", options=[route['type'] for route in st.session_state.data['methodology']], key='final_route_display')
        for route in st.session_state.data['methodology']:
            if route['type'] == selected_route_type:
                st.markdown(f"**方案**: {route['description'][:100]}...")
                if 'custom_modifications' in route:
                    st.markdown(f"**用户微调**: {route['custom_modifications'][:50]}...")

    # 生成终稿按钮
    if st.button("🚀 生成完整开题报告", type="primary"):
        with st.spinner("正在生成完整的开题报告..."):
            try:
                selected_hypo = st.session_state.data['selected_hypothesis']
                selected_route = None
                for route in st.session_state.data['methodology']:
                    if route['type'] == selected_route_type:
                        selected_route = route
                        break

                prompt = f"""请基于以下信息，生成一份完整的学术开题报告，使用Markdown格式：

## 研究假设
{selected_hypo['hypothesis']}

## 创新点
{selected_hypo['innovation']}

## 可行性分析
{selected_hypo['feasibility']}

## 技术路线
{selected_route['description']}

## 方案优势
{selected_route['advantages']}

## 方案局限性
{selected_route['limitations']}

## 预估成本与时间
成本：{selected_route['estimated_cost']}
时间：{selected_route['timeline']}

{'## 用户微调\n' + selected_route['custom_modifications'] if 'custom_modifications' in selected_route else ''}

请生成包含以下部分的开题报告：
1. 标题
2. 摘要
3. 研究背景与意义
4. 研究假设
5. 研究目标
6. 研究方法
7. 技术路线
8. 预期成果
9. 创新点
10. 研究计划与时间安排
11. 参考文献（示例）

请确保内容专业、逻辑清晰、格式规范。"""

                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的学术写作专家，擅长撰写高质量的开题报告和研究计划。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.4
                )

                proposal_content = response.choices[0].message.content.strip()
                st.session_state.data['final_proposal'] = proposal_content
                st.success("✅ 开题报告生成完成！")

            except Exception as e:
                st.error(f"生成开题报告时出现错误：{str(e)}")

    # 显示终稿
    if st.session_state.data['final_proposal']:
        st.markdown("---")
        st.markdown("### 📋 生成的开题报告")

        # 提供两种显示方式
        tab1, tab2 = st.tabs(["📄 Markdown 预览", "🔍 纯文本"])

        with tab1:
            st.markdown(st.session_state.data['final_proposal'])

        with tab2:
            st.text_area(
                "完整文本内容:",
                value=st.session_state.data['final_proposal'],
                height=600,
                disabled=True
            )

        # 下载按钮
        st.markdown("---")
        st.markdown("### 💾 导出选项")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "📥 下载 Markdown 文件 (.md)",
                data=st.session_state.data['final_proposal'],
                file_name="research_proposal.md",
                mime="text/markdown"
            )

        with col2:
            # 创建带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "📄 下载文本文件 (.txt)",
                data=st.session_state.data['final_proposal'],
                file_name=f"research_proposal_{timestamp}.txt",
                mime="text/plain"
            )

# 导航按钮
def navigation_buttons():
    """导航按钮"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.session_state.step > 1:
            if st.button("⬅️ 上一步"):
                st.session_state.step -= 1
                st.rerun()

    with col2:
        if st.session_state.step < 3:
            if st.button("➡️ 下一步", type="primary", use_container_width=True):
                # 检查是否可以进入下一步
                if st.session_state.step == 1 and not st.session_state.data['selected_hypothesis']:
                    st.warning("请先选择一个研究假设！")
                    return
                if st.session_state.step == 2 and not st.session_state.data['methodology']:
                    st.warning("请先生成技术路线！")
                    return

                st.session_state.step += 1
                st.rerun()
        else:
            # 重新开始按钮
            if st.button("🔄 重新开始", use_container_width=True):
                # 清空数据但保留API配置
                current_api = {
                    'user_api_key': user_api_key,
                    'user_base_url': user_base_url,
                    'model_name': model_name
                }

                # 重置状态
                st.session_state.step = 1
                st.session_state.data = {
                    'idea': '',
                    'hypotheses': [],
                    'selected_hypothesis': None,
                    'methodology': None,
                    'final_proposal': '',
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.rerun()

    with col3:
        # 当前步骤指示
        st.markdown(f"**步骤 {st.session_state.step}/3**")

# 显示当前步骤
if st.session_state.step == 1:
    step1_idea_burst()
elif st.session_state.step == 2:
    step2_methodology()
elif st.session_state.step == 3:
    step3_final_export()

# 导航按钮
st.markdown("---")
navigation_buttons()

# 侧边栏高级设置
st.sidebar.markdown("### ⚙️ 高级设置")
temperature = st.sidebar.slider(
    "创造性 (Temperature):",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.1,
    help="控制生成的创造性"
)

# 显示当前配置
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 当前进度")
st.sidebar.write(f"**当前步骤**: {st.session_state.step}/3")
st.sidebar.write(f"**模型**: {model_name}")
st.sidebar.write(f"**Temperature**: {temperature}")
st.sidebar.write(f"**创建时间**: {st.session_state.data['timestamp']}")

# 数据状态显示
st.sidebar.markdown("### 📊 数据状态")
data_status = {
    'idea': "✅" if st.session_state.data['idea'] else "❌",
    'hypotheses': "✅" if st.session_state.data['hypotheses'] else "❌",
    'selected_hypothesis': "✅" if st.session_state.data['selected_hypothesis'] else "❌",
    'methodology': "✅" if st.session_state.data['methodology'] else "❌",
    'final_proposal': "✅" if st.session_state.data['final_proposal'] else "❌"
}

for key, status in data_status.items():
    st.sidebar.write(f"**{key}**: {status}")

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
1. 📋 **按步骤完成**每个环节
2. 💾 **数据自动保存**不用担心丢失
3. 🔄 **随时回退**修改之前的决定
4. 📄 **直接导出**Markdown格式文档
5. ⚡ **流程化设计**比聊天更高效
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
🚀 **智能开题报告向导** - 结构化研究计划生成工具
通过三步工作流，帮你从模糊想法到完整开题报告，比传统聊天更高效！
""")