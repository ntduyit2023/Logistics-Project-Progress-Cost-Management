import sys
import os

# Đảm bảo đường dẫn tới DA3 được nhận diện
project_root = r"E:\University\Year 3 - 3\DA3"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.moi.pipeline_runner import run_new_pipeline

def test_pipeline():
    print("Testing Pipeline with Project C2011-07...")
    try:
        results = run_new_pipeline(
            project_id="C2011-07",
            mc_iterations=100,  # Keep it small for quick testing
            pareto_count=3,
            overtime_multiplier=1.5
        )
        print(f"\nSUCCESS: Pipeline finished successfully with {len(results)} pareto options.")
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
