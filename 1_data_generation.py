import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

class PublicGoodsGame:
    def __init__(self, n_players=10, endowment=10, multiplier=2.0, rounds=20):
        self.n_players = n_players
        self.endowment = endowment
        self.multiplier = multiplier
        self.rounds = rounds
        self.history = []
        
        # Define player types for behavioral simulation
        # 0-1: Free Riders (Selfish) - contribute very low
        # 2-3: Altruists - contribute high
        # 4-9: Conditional Cooperators - contribute based on previous average
        self.player_types = ['free_rider'] * 2 + ['altruist'] * 2 + ['conditional'] * 6

    def calculate_payoff(self, contribution, total_pool, governance_type='none', contributions_list=None):
        # Basic Public Goods Game Payoff Formula
        # pi = (Endowment - contribution) + (Total Pool * Multiplier) / N
        share_from_pool = (total_pool * self.multiplier) / self.n_players
        base_payoff = (self.endowment - contribution) + share_from_pool
        
        final_payoff = base_payoff
        
        avg_contribution = np.mean(contributions_list) if contributions_list is not None else 0
        
        # Governance Mechanisms
        if governance_type == 'punishment':
            # Mechanism: Punish if contribution is significantly below average
            # Simulating the data point: contribution 6, reward 0. 
            # If avg is say 8, 6 is below. Let's say if c < avg * 0.8, penalty applied.
            # Penalty logic: confiscate all earnings (simulating strict platform ban/audit).
            if contribution < avg_contribution * 0.8:
                final_payoff = 0  # Severe punishment
            else:
                # Small cost of auditing spread among everyone? Or just specific penalty.
                # To keep it simple and match "reward=0", we just zero it out.
                pass
                
        elif governance_type == 'reward':
            # Mechanism: Reward if contribution is above average
            # Simulating traffic boost
            if contribution > avg_contribution:
                # Bonus: e.g., 20% extra yield equivalent
                final_payoff += 5 
        
        return max(0, round(final_payoff, 2))

    def get_decision(self, player_idx, current_round, prev_avg_contribution):
        p_type = self.player_types[player_idx]
        noise = np.random.randint(-1, 2) # Small randomness
        
        if current_round == 1:
            # Initial round
            if p_type == 'free_rider': return np.random.randint(0, 3)
            if p_type == 'altruist': return np.random.randint(8, 11)
            return np.random.randint(4, 7) # Conditional starts middle
            
        # Subsequent rounds
        if p_type == 'free_rider':
            return max(0, min(self.endowment, 0 + max(0, noise))) # Always low
        elif p_type == 'altruist':
            return max(0, min(self.endowment, 10 + min(0, noise))) # Always high
        elif p_type == 'conditional':
            # Match previous average, maybe slightly less (imperfect reciprocity)
            decision = int(prev_avg_contribution) + noise
            return max(0, min(self.endowment, decision))
            
    def run_simulation(self, governance_type='none'):
        self.history = []
        prev_avg = 0
        
        # Re-initialize for fresh run
        current_contributions = []
        
        for r in range(1, self.rounds + 1):
            round_data = []
            contributions = []
            
            # 1. Decisions Phase
            for i in range(self.n_players):
                # For governance simulation, strategies might adapt
                # But for this simple exp, we assume fixed types adapting to pool size
                # OR we can make them adapt to governance.
                # If punishment is on, Free Riders might be forced to contribute?
                # Let's add a "fear" factor for punishment
                
                base_c = self.get_decision(i, r, prev_avg)
                
                if governance_type == 'punishment' and self.player_types[i] == 'free_rider':
                    # Free riders adapt to avoid punishment
                    # They try to do just enough (e.g. 60-80% of perceived average)
                    # But sometimes fail.
                    base_c = max(base_c, int(prev_avg * 0.8) if r > 1 else 5)
                
                if governance_type == 'reward' and self.player_types[i] == 'conditional':
                    # Conditional cooperators contribute more to get reward
                    base_c += 1
                    
                c = max(0, min(self.endowment, base_c))
                contributions.append(c)
            
            total_pool = sum(contributions)
            current_avg = total_pool / self.n_players
            prev_avg = current_avg
            
            # 2. Payoff Phase
            for i in range(self.n_players):
                c = contributions[i]
                reward = self.calculate_payoff(c, total_pool, governance_type, contributions)
                
                # Record Data
                record = {
                    'round': r,
                    'player_id': i + 1, # 1-based ID
                    'contribution': c,
                    'total_pool': total_pool,
                    'reward': reward,
                    'governance': governance_type # Extra field for analysis
                }
                self.history.append(record)
                
        return pd.DataFrame(self.history)

# Main Execution Flow
if __name__ == "__main__":
    game = PublicGoodsGame(rounds=10)
    
    # 1. Run Scenarios
    df_none = game.run_simulation('none')
    df_punish = game.run_simulation('punishment')
    df_reward = game.run_simulation('reward')
    
    # Combine for analysis
    df_all = pd.concat([df_none, df_punish, df_reward])
    
    # 2. Save Data (Simulating the requirement to produce consistent data)
    df_none.to_csv('exp3_no_gov.csv', index=False)
    df_punish.to_csv('exp3_punish.csv', index=False)
    df_reward.to_csv('exp3_reward.csv', index=False)
    
    print("Simulation Complete. Data files generated: exp3_no_gov.csv, exp3_punish.csv, exp3_reward.csv")
    
    # 3. Visualization
    plt.figure(figsize=(12, 6))
    sns.set_style("whitegrid")
    
    # Calculate average contribution per round per governance
    avg_trends = df_all.groupby(['governance', 'round'])['contribution'].mean().reset_index()
    
    sns.lineplot(data=avg_trends, x='round', y='contribution', hue='governance', marker='o', linewidth=2.5)
    
    plt.title('Impact of Governance Mechanisms on Average Contribution', fontsize=16)
    plt.xlabel('Round', fontsize=12)
    plt.ylabel('Average Contribution', fontsize=12)
    plt.ylim(0, 11)
    plt.legend(title='Governance Type')
    
    plt.savefig('exp3_analysis_plot.png')
    print("Analysis plot saved as exp3_analysis_plot.png")
    
    # 4. Show sample data to console for verification
    print("\n--- Sample Data (No Governance, Round 1-2) ---")
    print(df_none.head(10))
    
    print("\n--- Sample Data (Punishment Logic Check) ---")
    # Show cases where reward is 0 in punishment mode
    punished_cases = df_punish[df_punish['reward'] == 0]
    if not punished_cases.empty:
        print(punished_cases.head())
    else:
        print("No severe punishments (reward=0) occurred in this run.")

