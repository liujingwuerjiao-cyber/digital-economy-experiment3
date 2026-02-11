"""
公共物品博弈仿真模块
====================
实现 N 人公共物品博弈（Public Goods Game）的核心仿真逻辑。
支持三种治理模式：无治理、惩罚机制、奖励机制。
"""

import random
import csv
import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


# ──────────────────────── 玩家类 ────────────────────────
@dataclass
class Player:
    """
    博弈玩家。
    策略类型：
      - cooperator（合作者）：倾向于高贡献
      - free_rider（搭便车者）：倾向于低贡献
      - conditional（条件合作者）：根据上一轮平均贡献调整
    """
    player_id: int
    strategy: str          # cooperator / free_rider / conditional
    endowment: int = 10
    history: List[int] = field(default_factory=list)   # 历史贡献
    rewards: List[float] = field(default_factory=list)  # 历史收益

    def decide_contribution(self, round_num: int, prev_avg: float = 5.0) -> int:
        """
        根据策略类型决定本轮贡献值。
        增加了一定随机噪声以体现个体差异。
        """
        if self.strategy == "cooperator":
            base = random.randint(6, 10)
        elif self.strategy == "free_rider":
            base = random.randint(0, 3)
        else:  # conditional
            # 跟随上一轮平均值并加微调
            base = max(0, min(10, int(prev_avg) + random.randint(-2, 2)))

        # 随轮次增加，行为可能漂移
        if round_num > 10 and self.strategy == "conditional":
            # 后期条件合作者可能降低贡献（疲劳效应）
            base = max(0, base - random.randint(0, 2))

        return max(0, min(self.endowment, base))


# ──────────────────────── 博弈引擎 ────────────────────────
class PublicGoodsGame:
    """
    N 人公共物品博弈仿真引擎。

    参数
    ----
    n_players : int   玩家人数，默认 10
    endowment : int   每轮初始禀赋，默认 10
    multiplier : float 公共池增值系数，默认 2.0
    n_rounds : int    博弈轮次，默认 15
    seed : int        随机种子（可选）
    """

    def __init__(
        self,
        n_players: int = 10,
        endowment: int = 10,
        multiplier: float = 2.0,
        n_rounds: int = 15,
        seed: int = None,
    ):
        self.n_players = n_players
        self.endowment = endowment
        self.multiplier = multiplier
        self.n_rounds = n_rounds
        if seed is not None:
            random.seed(seed)

        # 分配策略：3 合作者、3 搭便车、4 条件合作
        strategies = (
            ["cooperator"] * 3
            + ["free_rider"] * 3
            + ["conditional"] * 4
        )
        random.shuffle(strategies)

        self.players: List[Player] = [
            Player(player_id=i + 1, strategy=strategies[i], endowment=endowment)
            for i in range(n_players)
        ]

    # ───────────── 收益计算核心 ─────────────
    @staticmethod
    def _base_reward(contribution: int, total_pool: int, multiplier: float,
                     n_players: int, endowment: int) -> float:
        """基础收益公式：π_i = (E - c_i) + (Σc_j × M) / N"""
        return (endowment - contribution) + (total_pool * multiplier) / n_players

    # ───────────── 单轮模拟 ─────────────
    def _simulate_round(
        self, round_num: int, governance: str, prev_avg: float
    ) -> List[Dict]:
        """
        模拟一轮博弈。

        governance: "none" | "punishment" | "reward"
        prev_avg  : 上一轮平均贡献值（用于条件合作者决策）
        """
        # 1) 每位玩家做出贡献决策
        contributions = {}
        for p in self.players:
            c = p.decide_contribution(round_num, prev_avg)
            contributions[p.player_id] = c
            p.history.append(c)

        total_pool = sum(contributions.values())
        avg_contribution = total_pool / self.n_players

        # 2) 计算每位玩家收益
        records = []
        for p in self.players:
            c_i = contributions[p.player_id]
            reward = self._base_reward(
                c_i, total_pool, self.multiplier, self.n_players, self.endowment
            )

            # ──── 治理机制 ────
            if governance == "punishment":
                # 惩罚：贡献低于均值的玩家收益归零
                if c_i < avg_contribution:
                    reward = 0.0

            elif governance == "reward":
                # 奖励：高贡献者获得 30% 额外加成
                if c_i > avg_contribution:
                    reward *= 1.3

            reward = round(reward, 2)
            p.rewards.append(reward)

            records.append({
                "round": round_num,
                "player_id": p.player_id,
                "contribution": c_i,
                "total_pool": total_pool,
                "reward": reward,
            })

        return records

    # ───────────── 运行完整仿真 ─────────────
    def run(self, governance: str = "none") -> List[Dict]:
        """
        运行 n_rounds 轮仿真。

        参数
        ----
        governance : str
            治理模式 → "none" | "punishment" | "reward"

        返回
        ----
        所有轮次的记录列表
        """
        all_records: List[Dict] = []
        prev_avg = self.endowment / 2  # 初始假定平均贡献为禀赋一半

        for r in range(1, self.n_rounds + 1):
            round_records = self._simulate_round(r, governance, prev_avg)
            all_records.extend(round_records)
            # 更新上轮平均贡献
            prev_avg = sum(rec["contribution"] for rec in round_records) / self.n_players

        return all_records

    # ───────────── 导出 CSV ─────────────
    @staticmethod
    def to_csv(records: List[Dict], filepath: str) -> None:
        """将记录列表导出为 CSV 文件。"""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        fieldnames = ["round", "player_id", "contribution", "total_pool", "reward"]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rec in records:
                writer.writerow({k: rec[k] for k in fieldnames})

    # ───────────── 重置玩家状态 ─────────────
    def reset(self) -> None:
        """重置所有玩家的历史记录以便重新运行。"""
        for p in self.players:
            p.history.clear()
            p.rewards.clear()


# ──────────────────── 便捷运行函数 ────────────────────
def run_all_modes(seed: int = 42, n_rounds: int = 15, output_dir: str = "output"):
    """
    依次运行三种治理模式并导出 CSV。

    返回
    ----
    results : dict[str, List[Dict]]
        键为模式名称，值为记录列表。
    """
    modes = ["none", "punishment", "reward"]
    results = {}

    for mode in modes:
        game = PublicGoodsGame(seed=seed, n_rounds=n_rounds)
        records = game.run(governance=mode)
        csv_path = os.path.join(output_dir, f"data_exp3_{mode if mode != 'none' else 'no_governance'}.csv")
        PublicGoodsGame.to_csv(records, csv_path)
        results[mode] = records
        print(f"[✓] 模式 '{mode}' 仿真完成 → {csv_path}")

    # 合并汇总 CSV（带 governance_mode 列）
    all_records = []
    for mode, recs in results.items():
        for rec in recs:
            row = dict(rec)
            row["governance_mode"] = mode
            all_records.append(row)

    summary_path = os.path.join(output_dir, "data_exp3_public_goods.csv")
    fieldnames = ["governance_mode", "round", "player_id", "contribution", "total_pool", "reward"]
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_records:
            writer.writerow({k: row[k] for k in fieldnames})

    print(f"[✓] 汇总数据 → {summary_path}")
    return results
