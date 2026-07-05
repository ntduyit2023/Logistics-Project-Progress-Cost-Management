import sys
import os
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

# Dynamic path resolution to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.data_loader import GlPoDataset
from ai_pipeline.envs.logistics_gym_env import create_env_from_project_graph

processed_dir = os.path.abspath(os.path.join(project_root, 'ai_pipeline', 'data', 'processed'))
dataset = GlPoDataset(processed_dir)

for pg in dataset.graphs:
    if pg.project_id == 'C2012-04':
        features = pg.data.x.numpy()
        rms = np.sqrt(np.mean(features**2, axis=0, keepdims=True))
        rms = np.maximum(rms, 1.0)
        print(f"\nProject: {pg.project_id}")
        print(f"Features shape: {features.shape}")
        print(f"RMS of direct costs (7-14): {rms[0, 7:15]}")
        print(f"Max direct costs: {features[:, 7:15].max(axis=0)}")
        print(f"Mean direct costs: {features[:, 7:15].mean(axis=0)}")
        
        env = create_env_from_project_graph(pg)
        print(f"Env penalty_weight: {env.penalty_weight}")
        print(f"Env reward_scale: {env.reward_scale}")
        print(f"Env global_constraints: {env._global_constraints}")
        
        obs, info = env.reset()
        print(f"Reset info: {info}")
        
        # Step normal until end of episode to see violations
        done = False
        step = 0
        total_r = 0.0
        while not done:
            obs, r, term, trunc, info = env.step(0) # Step normal
            done = term or trunc
            step += 1
            total_r += r
            if len(info.get('reward_breakdown', {}).get('violations', [])) > 0:
                print(f"Step {step} Violations: {info['reward_breakdown']['violations']}")
                print(f"Step {step} Reward breakdown: {info['reward_breakdown']}")
        print(f"Episode finished in {step} steps. Total reward: {total_r}")
