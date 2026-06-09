"""Verify CPM calculation step by step."""
import sys
sys.path.insert(0, '.')
from algorithms.cpm_engine import build_project_graph, calculate_cpm, get_critical_path
from tests.case_study_data import TASKS, DEPENDENCIES

G = build_project_graph(TASKS, DEPENDENCIES)
G, dur = calculate_cpm(G)

print("Critical Path:", get_critical_path(G))
print("Project Duration:", dur)
print()

# Verify path
path = ['A','C','G','I','J','N','R','T','U']
durations_sum = sum(G.nodes[p]['duration'] for p in path)
print(f"Sum of durations on critical path: {durations_sum}")
print(f"4+7+10+16+12+7+5+3+2 = {4+7+10+16+12+7+5+3+2}")
print()

# Full table
print(f"{'Task':<4} {'ES':>3} {'EF':>3} {'LS':>3} {'LF':>3} {'TS':>3} {'FS':>3}")
print("-" * 30)
for n in sorted(G.nodes()):
    d = G.nodes[n]
    print(f"{n:<4} {d['es']:>3} {d['ef']:>3} {d['ls']:>3} {d['lf']:>3} {d['total_slack']:>3} {d['free_slack']:>3}")
