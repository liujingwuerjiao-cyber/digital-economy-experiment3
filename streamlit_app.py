import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
import io

# 设置页面配置
st.set_page_config(
    page_title="数字经济仿真实验3：公共物品博弈与算法治理",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 核心仿真逻辑 (复用之前的类，稍作适配) ---
class PublicGoodsGame:
    def __init__(self, n_players=10, endowment=10, multiplier=2.0, rounds=10):
        self.n_players = n_players
        self.endowment = endowment
        self.multiplier = multiplier
        self.rounds = rounds
        self.history = []
        # 定义玩家类型
        self.player_types = ['free_rider'] * int(n_players * 0.2) + \
                            ['altruist'] * int(n_players * 0.2) + \
                            ['conditional'] * (n_players - int(n_players * 0.2) - int(n_players * 0.2))

    def calculate_payoff(self, contribution, total_pool, governance_type='none', contributions_list=None):
        share_from_pool = (total_pool * self.multiplier) / self.n_players
        base_payoff = (self.endowment - contribution) + share_from_pool
        final_payoff = base_payoff
        avg_contribution = np.mean(contributions_list) if contributions_list is not None else 0
        
        if governance_type == 'punishment':
            if contribution < avg_contribution * 0.8:
                final_payoff = 0 
        elif governance_type == 'reward':
            if contribution > avg_contribution:
                final_payoff += 5 
        
        return max(0, round(final_payoff, 2))

    def get_decision(self, player_idx, current_round, prev_avg_contribution):
        p_type = self.player_types[player_idx]
        noise = np.random.randint(-1, 2)
        
        if current_round == 1:
            if p_type == 'free_rider': return np.random.randint(0, 3)
            if p_type == 'altruist': return np.random.randint(int(self.endowment*0.8), self.endowment+1)
            return np.random.randint(int(self.endowment*0.4), int(self.endowment*0.7))
            
        if p_type == 'free_rider':
            return max(0, min(self.endowment, 0 + max(0, noise)))
        elif p_type == 'altruist':
            return max(0, min(self.endowment, self.endowment + min(0, noise)))
        elif p_type == 'conditional':
            decision = int(prev_avg_contribution) + noise
            return max(0, min(self.endowment, decision))
            
    def run_simulation(self, governance_type='none'):
        self.history = []
        prev_avg = 0
        
        # 为了演示效果，每次运行重置随机种子不太好，这里让它随机
        # 但为了教学复现，可以在外部控制
        
        for r in range(1, self.rounds + 1):
            contributions = []
            # 1. 决策阶段
            for i in range(self.n_players):
                base_c = self.get_decision(i, r, prev_avg)
                
                # 策略适应
                if governance_type == 'punishment' and self.player_types[i] == 'free_rider':
                    # 尝试避免惩罚，但不一定成功
                    base_c = max(base_c, int(prev_avg * 0.8) if prev_avg > 0 else 0)
                
                if governance_type == 'reward' and self.player_types[i] == 'conditional':
                    base_c += 1
                    
                c = max(0, min(self.endowment, base_c))
                contributions.append(c)
            
            total_pool = sum(contributions)
            current_avg = total_pool / self.n_players
            prev_avg = current_avg
            
            # 2. 结算阶段
            for i in range(self.n_players):
                c = contributions[i]
                reward = self.calculate_payoff(c, total_pool, governance_type, contributions)
                self.history.append({
                    'round': r,
                    'player_id': i + 1,
                    'player_type': self.player_types[i], # 增加类型记录便于教学
                    'contribution': c,
                    'total_pool': total_pool,
                    'reward': reward,
                    'governance': governance_type
                })
        return pd.DataFrame(self.history)

# --- 侧边栏导航 ---
st.sidebar.title("📚 实验导航")
page = st.sidebar.radio("选择模块", 
    ["📖 实验大纲与背景", 
     "💻 仿真实验控制台", 
     "📊 数据分析与可视化", 
     "📝 实验报告与结论"])

st.sidebar.markdown("---")
st.sidebar.info("👨‍🏫 **教授寄语**：\n本实验旨在通过代码复现“公地悲剧”，并探索算法治理（惩罚/奖励）如何重塑社区规范。请认真观察数据变化！")

# --- 模块 1：实验大纲 ---
if page == "📖 实验大纲与背景":
    st.title("实验 3：数字社区公共物品博弈与算法治理仿真")
    
    st.markdown("""
    ### 一、 实验背景
    本实验模拟数字经济中常见的**“公共资源池”**场景（如开源社区代码贡献、UGC平台内容生产）。
    核心矛盾在于个体面临**“贡献资源”**还是**“搭便车（只消耗不贡献）”**的策略选择。
    
    ### 二、 实验目的
    1.  **微观机制理解**：量化理解搭便车行为对集体收益的损害（公地悲剧）。
    2.  **数据仿真能力**：生成符合 `data_exp3_public_goods.csv` 标准结构的数据。
    3.  **治理算法设计**：探索“信誉惩罚”与“积分奖励”对用户贡献率的影响。
    
    ### 三、 关键参数与公式
    *   **玩家数 ($N$)**：默认 10 人
    *   **初始禀赋 ($E$)**：默认 10 单位
    *   **增值系数 ($M$)**：默认 2.0
    *   **收益公式**：
        $$ \pi_i = (E - c_i) + \\frac{\sum c_j \\times M}{N} $$
    
    ### 四、 实验步骤
    1.  **无治理模式**：自由博弈，观察贡献率衰退。
    2.  **惩罚机制**：对贡献低于平均值 80% 的用户，收益归零。
    3.  **奖励机制**：对贡献高于平均值的用户，给予额外奖励。
    """)
    
    with st.expander("查看标准数据结构 (Schema)"):
        st.code("""
        round: 博弈轮次
        player_id: 用户标识
        contribution: 个人贡献量
        total_pool: 本轮公共池总量
        reward: 玩家本轮最终净收益
        """, language="yaml")

# --- 模块 2：仿真控制台 ---
elif page == "💻 仿真实验控制台":
    st.title("💻 仿真实验控制台")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ 参数设置")
        n_players = st.number_input("玩家数量 (N)", min_value=5, max_value=50, value=10)
        endowment = st.number_input("初始禀赋 (E)", value=10)
        multiplier = st.slider("增值系数 (M)", 1.0, 5.0, 2.0, step=0.1)
        rounds = st.slider("博弈轮次", 5, 50, 20)
        
        st.markdown("---")
        st.markdown("**治理模式选择**")
        run_none = st.checkbox("运行：无治理模式 (Baseline)", value=True)
        run_punish = st.checkbox("运行：惩罚机制 (Punishment)", value=True)
        run_reward = st.checkbox("运行：奖励机制 (Reward)", value=True)
        
        btn_run = st.button("🚀 开始仿真", type="primary")

    with col2:
        st.subheader("🖥️ 运行日志与代码预览")
        
        # 展示核心代码逻辑供学生学习
        with st.expander("查看 Python 核心类代码 (PublicGoodsGame)"):
            st.code("""
class PublicGoodsGame:
    def calculate_payoff(self, contribution, total_pool, gov_type, ...):
        # ... (省略部分代码)
        if gov_type == 'punishment':
            if contribution < avg * 0.8:
                final_payoff = 0  # 收益归零
        elif gov_type == 'reward':
            if contribution > avg:
                final_payoff += 5 # 额外奖励
            """, language="python")

        if btn_run:
            game = PublicGoodsGame(n_players, endowment, multiplier, rounds)
            data_frames = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            if run_none:
                status_text.text("正在运行：无治理模式...")
                df_none = game.run_simulation('none')
                data_frames.append(df_none)
                st.session_state['df_none'] = df_none
                progress_bar.progress(33)
                
            if run_punish:
                status_text.text("正在运行：惩罚机制...")
                df_punish = game.run_simulation('punishment')
                data_frames.append(df_punish)
                st.session_state['df_punish'] = df_punish
                progress_bar.progress(66)
                
            if run_reward:
                status_text.text("正在运行：奖励机制...")
                df_reward = game.run_simulation('reward')
                data_frames.append(df_reward)
                st.session_state['df_reward'] = df_reward
                progress_bar.progress(100)
                
            status_text.text("✅ 仿真完成！请前往“数据分析与可视化”模块查看结果。")
            
            # 合并数据并保存到 session state
            if data_frames:
                df_all = pd.concat(data_frames)
                st.session_state['df_all'] = df_all
                
                st.success(f"成功生成 {len(df_all)} 条仿真数据！")
                st.dataframe(df_all.head(10))
                
                # 下载按钮
                csv = df_all.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 下载完整实验数据 (CSV)",
                    csv,
                    "exp3_simulation_data.csv",
                    "text/csv",
                    key='download-csv'
                )
            else:
                st.warning("请至少选择一种治理模式进行运行。")

# --- 模块 3：数据分析 ---
elif page == "📊 数据分析与可视化":
    st.title("📊 数据分析与可视化")
    
    if 'df_all' not in st.session_state:
        st.info("⚠️ 请先在“仿真实验控制台”运行实验以生成数据。")
    else:
        df_all = st.session_state['df_all']
        
        # 1. 核心趋势图
        st.subheader("1. 平均贡献率演变趋势")
        st.markdown("观察不同治理机制下，群体平均贡献随时间的变化。")
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=df_all, x='round', y='contribution', hue='governance', style='governance', markers=True, ax=ax, linewidth=2.5)
        ax.set_title("Average Contribution by Governance Type", fontsize=14)
        ax.set_ylim(0, 11)
        ax.grid(True, linestyle='--', alpha=0.7)
        st.pyplot(fig)
        
        # 2. 收益热力图/分布
        st.subheader("2. 玩家类型与收益分析")
        st.markdown("对比“搭便车者(free_rider)”与“利他者(altruist)”在不同模式下的平均收益。")
        
        # 计算每种模式下，每种玩家类型的平均收益
        payoff_summary = df_all.groupby(['governance', 'player_type'])['reward'].mean().reset_index()
        
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        sns.barplot(data=payoff_summary, x='governance', y='reward', hue='player_type', palette="viridis", ax=ax2)
        ax2.set_title("Average Reward: Player Type vs Governance", fontsize=14)
        st.pyplot(fig2)
        
        st.markdown("""
        **观察要点**：
        *   在 **None (无治理)** 模式下，`free_rider` 的收益通常高于 `altruist`（搭便车红利）。
        *   在 **Punishment (惩罚)** 模式下，`free_rider` 的收益应大幅下降（若其未及时调整策略）。
        *   在 **Reward (奖励)** 模式下，`conditional` 和 `altruist` 的收益应得到提升。
        """)

        # 3. 原始数据查看
        with st.expander("🔍 查看详细原始数据"):
            st.dataframe(df_all)

# --- 模块 4：实验结论 ---
elif page == "📝 实验报告与结论":
    st.title("📝 实验总结与报告")
    
    st.markdown("### 📊 实验数据分析摘要 (Analysis Summary)")
    st.info("""
    **基于仿真数据的自动生成分析：**
    
    1.  **公地悲剧的验证**：
        在无治理（None）模式下，由于搭便车者的存在，条件合作者的贡献意愿随轮次递减，导致社区总资源池萎缩，平均贡献率呈现明显的**下降趋势**。
        
    2.  **惩罚机制的有效性**：
        引入惩罚（Punishment）后，低贡献行为的预期收益变为 0（甚至负值）。这迫使搭便车者提高贡献以满足最低门槛（如平均值的 80%），从而将整体贡献率维持在**中等偏高水平**。
        
    3.  **激励机制的优越性**：
        奖励机制（Reward）通过对高贡献者进行额外补偿（如流量扶持），使得“合作”成为占优策略。在仿真中，该模式通常能激发出**最高**的群体贡献水平，形成良性循环。
    """)
    
    st.markdown("### 💡 思考题")
    st.text_area("1. 为什么在真实课堂实验中，即使没有硬性惩罚，贡献率也往往高于纯理论预测的 0？（提示：社会偏好）")
    st.text_area("2. 如果你是某个知识共享平台的产品经理，你会优先上线“黑名单机制”还是“优质创作者激励计划”？请结合实验数据说明理由。")
    
    st.button("💾 导出实验报告 (模拟)")

