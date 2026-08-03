import sys
sys.path.append('/')
import pandas as pd
from ai_pipeline.models.moi.pipeline_runner import MOIPipelineRunner
from ai_pipeline.models.moi.cpsat_pareto_solver import CPSATParetoSolver

def patch_init(self, tasks, *args, **kwargs):
    print("PATCHED INIT!")
    t4 = next((t for t in tasks if t.get('task_id') == 'C2011-07_4'), None)
    if t4:
        print(f"C2011-07_4 inside solver tasks: duration_hours={t4.get('duration_hours')}, duration_factor={t4.get('duration_factor')}")
    else:
        print("C2011-07_4 not found!")
    import sys
    sys.exit(0)

original_init = CPSATParetoSolver.__init__
CPSATParetoSolver.__init__ = patch_init

runner = MOIPipelineRunner('/ai_pipeline/data/processed/C2011-07')
runner.run(mc_iterations=5, pareto_count=1)
