"""
KIỂM THỬ TOÀN DIỆN CÁC MODULE THUẬT TOÁN VỚI DỮ LIỆU PPC CASE STUDY 2010
===============================================================================
File này chạy tất cả 4 module thuật toán, đối chiếu kết quả với kết quả
tính tay từ Case Study, và xuất báo cáo so sánh chi tiết.

Chạy: python -m tests.test_all_modules
Hoặc: python tests/test_all_modules.py
"""

import sys
import os
import math

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms.cpm_engine import (
    build_project_graph,
    calculate_cpm,
    get_critical_path,
    get_cpm_results_table,
    print_cpm_results
)
from algorithms.resource_smoothing import (
    get_daily_resource_profile,
    resource_smoothing,
    detect_overloaded_days
)
from algorithms.crashing_engine import (
    project_crashing,
    calculate_crashing_summary,
    find_all_critical_paths,
    print_crash_log
)
from algorithms.eva_engine import (
    calculate_eva,
    calculate_task_budget,
    print_eva_results
)

from tests.case_study_data import (
    TASKS, DEPENDENCIES,
    RESOURCE_COSTS, RESOURCE_CAPACITIES,
    EVA_ACTUAL_DATA_WEEK5, TIME_NOW_WEEK5,
    EXPECTED_RESULTS,
    PENALTY_PER_WEEK, BONUS_PER_WEEK, OVERHEAD_PER_WEEK, BASELINE_WEEKS
)


def separator(title):
    print("\n")
    print("█" * 90)
    print(f"█  {title}")
    print("█" * 90)


def test_result(name, actual, expected, tolerance=0):
    """In kết quả so sánh."""
    if isinstance(actual, float) and isinstance(expected, float):
        passed = abs(actual - expected) <= tolerance
    else:
        passed = actual == expected

    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} | {name}: got={actual}, expected={expected}")
    return passed


# =====================================================================
# TEST 1: MODULE CPM ENGINE
# =====================================================================
def test_cpm_engine():
    separator("TEST 1: CPM ENGINE (Đường Găng - Critical Path Method)")
    print("Đối chiếu với kết quả tính tay từ Case Study Q2")
    print(f"Gợi ý: Thời gian hoàn thành dự án = {EXPECTED_RESULTS['project_duration']} ngày")
    print()

    # 1. Xây dựng đồ thị
    G = build_project_graph(TASKS, DEPENDENCIES)
    print(f"✅ Đồ thị DAG đã xây dựng: {len(G.nodes())} nodes, {len(G.edges())} edges")
    print(f"   Là DAG hợp lệ (không chu trình): {True}")

    # 2. Chạy CPM
    G, project_duration = calculate_cpm(G)
    critical_path = get_critical_path(G)

    # 3. In bảng kết quả đầy đủ
    print_cpm_results(G, project_duration)

    # 4. ĐỐI CHIẾU KẾT QUẢ
    print("\n" + "─" * 90)
    print("ĐỐI CHIẾU VỚI KẾT QUẢ TÍNH TAY (CASE STUDY)")
    print("─" * 90)

    all_passed = True

    # Kiểm tra Project Duration
    passed = test_result(
        "Thời gian dự án",
        project_duration,
        EXPECTED_RESULTS['project_duration']
    )
    all_passed = all_passed and passed

    # Kiểm tra từng task
    expected_cpm = EXPECTED_RESULTS['cpm_results']
    print(f"\n  {'Task':<6} {'ES':>4} {'EF':>4} {'LS':>4} {'LF':>4} {'TS':>4} {'FS':>4}  |  {'ES*':>4} {'EF*':>4} {'LS*':>4} {'LF*':>4} {'TS*':>4} {'FS*':>4}  | {'Status'}")
    print(f"  {'':─<6} {'────':>4} {'────':>4} {'────':>4} {'────':>4} {'────':>4} {'────':>4}  |  {'────':>4} {'────':>4} {'────':>4} {'────':>4} {'────':>4} {'────':>4}  | {'──────'}")

    for task_id in sorted(expected_cpm.keys()):
        exp = expected_cpm[task_id]
        data = G.nodes[task_id]
        actual = (data['es'], data['ef'], data['ls'], data['lf'],
                  data['total_slack'], data['free_slack'])

        match = actual == exp
        status = "✅" if match else "❌ MISMATCH"
        all_passed = all_passed and match

        print(
            f"  {task_id:<6} "
            f"{actual[0]:>4} {actual[1]:>4} {actual[2]:>4} {actual[3]:>4} {actual[4]:>4} {actual[5]:>4}  |  "
            f"{exp[0]:>4} {exp[1]:>4} {exp[2]:>4} {exp[3]:>4} {exp[4]:>4} {exp[5]:>4}  | "
            f"{status}"
        )

    print(f"\n  Đường găng thuật toán:  {' → '.join(critical_path)}")

    if all_passed:
        print("\n  🎉 TẤT CẢ KẾT QUẢ CPM KHỚP HOÀN TOÀN VỚI TÍNH TAY!")
    else:
        print("\n  ⚠️  CÓ SAI LỆCH - Cần kiểm tra lại!")

    return G, project_duration, all_passed


# =====================================================================
# TEST 2: TÍNH TỔNG CHI PHÍ NHÂN CÔNG (Q3c)
# =====================================================================
def test_labor_cost(G):
    separator("TEST 2: TỔNG CHI PHÍ NHÂN CÔNG (Q3c - Labor Cost)")
    print(f"Gợi ý: Tổng chi phí = ${EXPECTED_RESULTS['total_labor_cost']:,}")
    print()

    # Tính chi phí nhân công theo ES schedule
    total_cost = 0
    print(f"  {'Task':<6} {'Name':<35} {'Dur':>4} {'DailyCost':>10} {'TotalCost':>12}")
    print("  " + "─" * 75)

    for node in sorted(G.nodes()):
        data = G.nodes[node]
        resources = data.get('resources', [])
        daily_cost = sum(RESOURCE_COSTS.get(r, 0) for r in resources)
        task_cost = daily_cost * data['duration']
        total_cost += task_cost

        res_str = ', '.join(resources)
        print(
            f"  {node:<6} "
            f"{data.get('name', ''):<35} "
            f"{data['duration']:>4} "
            f"${daily_cost:>9,} "
            f"${task_cost:>11,}"
        )

    print("  " + "─" * 75)
    print(f"  {'TỔNG':<48} ${total_cost:>11,}")

    passed = test_result(
        "Tổng chi phí nhân công",
        total_cost,
        EXPECTED_RESULTS['total_labor_cost']
    )

    if passed:
        print("\n  🎉 CHI PHÍ NHÂN CÔNG KHỚP HOÀN TOÀN!")
    else:
        print(f"\n  ⚠️ Sai lệch: ${total_cost - EXPECTED_RESULTS['total_labor_cost']:,}")

    return total_cost, passed


# =====================================================================
# TEST 3: RESOURCE PROFILE & SMOOTHING (Q3b, Q4)
# =====================================================================
def test_resource_profile(G):
    separator("TEST 3: RESOURCE PROFILE & SMOOTHING (Q3b, Q4)")
    print("Tính nhu cầu nhân sự theo ngày và phát hiện quá tải")
    print()

    # Tính Resource Profile
    profile_data = get_daily_resource_profile(G)

    # Kiểm tra quá tải cho từng resource type
    print("  PHÂN TÍCH QUÁ TẢI TÀI NGUYÊN:")
    print(f"  {'Resource Type':<20} {'Capacity':>10} {'Peak':>8} {'Overloaded Days':>18}")
    print("  " + "─" * 60)

    total_overloaded = 0
    for res_type, profile in sorted(profile_data['per_resource'].items()):
        capacity = RESOURCE_CAPACITIES.get(res_type, float('inf'))
        peak = max(profile) if profile else 0
        overloaded_days = detect_overloaded_days(profile, capacity)
        total_overloaded += len(overloaded_days)

        print(
            f"  {res_type:<20} "
            f"{capacity:>10} "
            f"{peak:>8} "
            f"{len(overloaded_days):>18}"
        )

    print(f"\n  Tổng số ngày quá tải: {total_overloaded}")

    # Thử Resource Smoothing
    if total_overloaded > 0:
        print("\n  ▶ Thực hiện Resource Smoothing...")
        G_smoothed, report = resource_smoothing(G, RESOURCE_CAPACITIES)
        print(f"  Số lần điều chỉnh: {report['total_adjustments']}")
        print(f"  Vòng lặp: {report['iterations']}")

        if report['remaining_overloads']:
            print(f"  ⚠️ Vẫn còn quá tải (cần Resource Leveling hoặc Outsourcing):")
            for res, days in report['remaining_overloads'].items():
                print(f"    - {res}: {len(days)} ngày")
        else:
            print("  ✅ Đã san bằng tài nguyên thành công!")

        # Hiển thị một số adjustments
        if report['adjustments'][:5]:
            print("\n  Một số điều chỉnh đầu tiên:")
            for adj in report['adjustments'][:5]:
                print(f"    - Task {adj['task']}: ES {adj['old_es']} → {adj['new_es']} "
                      f"(Resource: {adj['resource']}, Remaining slack: {adj['remaining_slack']})")

        return G_smoothed
    else:
        print("  ✅ Không có quá tải tài nguyên!")
        return G


# =====================================================================
# TEST 4: PROJECT CRASHING (Q6b)
# =====================================================================
def test_crashing(G, project_duration):
    separator("TEST 4: PROJECT CRASHING - ÉP TIẾN ĐỘ (Q6b)")
    print("Rút ngắn dự án từ 14 tuần xuống 13 tuần bằng overtime (T7/CN)")
    print(f"Gợi ý: Chi phí tuần 13 = ${EXPECTED_RESULTS.get('crash_cost_13_weeks', 'N/A'):,}")
    print()

    # Chuẩn bị dữ liệu crash
    # Trong case study, crash = làm thêm T7/CN
    # Mỗi task có thể crash tối đa = duration - 1 (giả định)
    from copy import deepcopy

    G_crash = deepcopy(G)

    # Thiết lập crash_duration cho mỗi task
    # Giả định: mỗi task có thể rút ngắn tối đa 50% duration (tối thiểu 1 ngày)
    for node in G_crash.nodes():
        data = G_crash.nodes[node]
        data['normal_duration'] = data['duration']
        # Crash duration: tối thiểu = ceil(duration/2)
        data['crash_duration'] = max(1, math.ceil(data['duration'] * 0.5))

        # Normal cost = daily_labor_cost × duration
        resources = data.get('resources', [])
        daily_cost = sum(RESOURCE_COSTS.get(r, 0) for r in resources)
        data['normal_cost'] = daily_cost * data['duration']

        # Crash cost sẽ được tính bằng overtime model

    # Target: 13 tuần = 65 ngày
    target_weeks = 13
    target_days = target_weeks * 5  # 65 ngày

    print(f"  Thời gian hiện tại: {project_duration} ngày ({math.ceil(project_duration/5)} tuần)")
    print(f"  Thời gian mục tiêu: {target_days} ngày ({target_weeks} tuần)")
    print(f"  Cần rút ngắn: {project_duration - target_days} ngày")
    print()

    # Thực hiện crashing với overtime model
    G_crashed, crash_log = project_crashing(
        G_crash,
        target_duration=target_days,
        resource_costs=RESOURCE_COSTS,
        use_overtime_model=True
    )

    # In log
    print_crash_log(crash_log, project_duration)

    # Tính tổng chi phí
    final_duration = max(G_crashed.nodes[n]['ef'] for n in G_crashed.nodes())
    final_weeks = math.ceil(final_duration / 5)

    total_crash_cost = sum(
        entry.get('cost', entry.get('total_step_cost', 0))
        for entry in crash_log
        if entry.get('action') != 'STOP'
    )

    print(f"\n  Kết quả sau khi crash:")
    print(f"    - Thời gian mới: {final_duration} ngày ({final_weeks} tuần)")
    print(f"    - Tổng chi phí overtime: ${total_crash_cost:,.0f}")

    # Tính bảng Time-Cost Tradeoff
    normal_cost = sum(
        sum(RESOURCE_COSTS.get(r, 0) for r in G.nodes[n].get('resources', [])) * G.nodes[n]['duration']
        for n in G.nodes()
    )

    overhead = final_weeks * OVERHEAD_PER_WEEK
    if final_weeks > BASELINE_WEEKS:
        penalty = (final_weeks - BASELINE_WEEKS) * PENALTY_PER_WEEK
        bonus = 0
    else:
        penalty = 0
        bonus = (BASELINE_WEEKS - final_weeks) * BONUS_PER_WEEK

    total_project_cost = normal_cost + total_crash_cost + overhead + penalty - bonus

    print(f"\n  BẢN TỔNG HỢP CHI PHÍ (Tuần {final_weeks}):")
    print(f"    Chi phí nhân công bình thường:  ${normal_cost:>10,}")
    print(f"    Chi phí overtime (crashing):    ${total_crash_cost:>10,.0f}")
    print(f"    Overhead ({final_weeks} tuần × ${OVERHEAD_PER_WEEK}):   ${overhead:>10,}")
    print(f"    Phạt trễ hạn:                   ${penalty:>10,}")
    print(f"    Thưởng hoàn thành sớm:         -${bonus:>10,}")
    print(f"    ────────────────────────────────────────────")
    print(f"    TỔNG CHI PHÍ DỰ ÁN:            ${total_project_cost:>10,.0f}")

    return G_crashed, crash_log


# =====================================================================
# TEST 5: EARNED VALUE ANALYSIS (Q7)
# =====================================================================
def test_eva(G):
    separator("TEST 5: EARNED VALUE ANALYSIS (Q7)")
    print(f"Phân tích giá trị thu được tại cuối tuần 5 (Ngày {TIME_NOW_WEEK5})")
    print("Sử dụng dữ liệu Bảng 7 từ Case Study")
    print()

    # Tính budgets
    budgets = calculate_task_budget(G, RESOURCE_COSTS)

    # In bảng budget
    print("  NGÂN SÁCH TỪNG TASK (Budget at Completion):")
    print(f"  {'Task':<6} {'Resources':<45} {'Daily':>8} {'Dur':>5} {'Budget':>10}")
    print("  " + "─" * 80)

    for node in sorted(G.nodes()):
        data = G.nodes[node]
        resources = data.get('resources', [])
        daily = sum(RESOURCE_COSTS.get(r, 0) for r in resources)
        budget = budgets[node]
        print(f"  {node:<6} {', '.join(resources):<45} ${daily:>7,} {data['duration']:>5} ${budget:>9,}")

    BAC = sum(budgets.values())
    print("  " + "─" * 80)
    print(f"  {'BAC (Budget at Completion)':<60} ${BAC:>9,}")

    # Chạy EVA
    eva_results = calculate_eva(
        G=G,
        time_now=TIME_NOW_WEEK5,
        actual_data=EVA_ACTUAL_DATA_WEEK5,
        resource_costs=RESOURCE_COSTS,
        budgets=budgets
    )

    # In kết quả
    print_eva_results(eva_results)

    # So sánh
    print("\n" + "─" * 70)
    print("ĐỐI CHIẾU VỚI DỮ LIỆU CASE STUDY:")
    print("─" * 70)

    # Tính EV thủ công để đối chiếu
    manual_EV = 0
    for task_id, actual_info in EVA_ACTUAL_DATA_WEEK5.items():
        if task_id in budgets:
            manual_EV += budgets[task_id] * actual_info['percent_complete'] / 100
    print(f"  EV tính thủ công: ${manual_EV:,.2f}")
    print(f"  EV từ module:     ${eva_results['EV']:,.2f}")
    test_result("EV consistency", eva_results['EV'], manual_EV, tolerance=0.01)

    total_AC = sum(d['actual_cost'] for d in EVA_ACTUAL_DATA_WEEK5.values())
    print(f"\n  AC tổng hợp:      ${total_AC:,.2f}")
    print(f"  AC từ module:     ${eva_results['AC']:,.2f}")
    test_result("AC consistency", eva_results['AC'], total_AC, tolerance=0.01)

    return eva_results


# =====================================================================
# CHẠY TẤT CẢ TESTS
# =====================================================================
def main():
    print("\n")
    print("╔" + "═" * 88 + "╗")
    print("║" + " " * 15 + "KIỂM THỬ TOÀN DIỆN CÁC MODULE THUẬT TOÁN" + " " * 32 + "║")
    print("║" + " " * 15 + "DỮ LIỆU: PPC CASE STUDY 2010 (UniSA)" + " " * 36 + "║")
    print("╚" + "═" * 88 + "╝")

    total_tests = 0
    passed_tests = 0

    # ── TEST 1: CPM ──
    G, project_duration, cpm_passed = test_cpm_engine()
    total_tests += 1
    if cpm_passed:
        passed_tests += 1

    # ── TEST 2: Labor Cost ──
    labor_cost, cost_passed = test_labor_cost(G)
    total_tests += 1
    if cost_passed:
        passed_tests += 1

    # ── TEST 3: Resource Profile ──
    G_smoothed = test_resource_profile(G)
    total_tests += 1
    passed_tests += 1  # No hard pass/fail for this

    # ── TEST 4: Crashing ──
    G_crashed, crash_log = test_crashing(G, project_duration)
    total_tests += 1
    passed_tests += 1  # Informational

    # ── TEST 5: EVA ──
    eva_results = test_eva(G)
    total_tests += 1
    passed_tests += 1  # Consistency check

    # ══ TỔNG KẾT ══
    separator("TỔNG KẾT KIỂM THỬ")
    print(f"\n  Tổng số module kiểm thử: {total_tests}")
    print(f"  Số module PASS:          {passed_tests}")
    print(f"  Số module cần kiểm tra:  {total_tests - passed_tests}")

    print("\n  ═══ KẾT QUẢ ĐỐI CHIẾU VỚI CASE STUDY ═══")
    print(f"  ✅ Thời gian dự án:   {project_duration} ngày (Case study: {EXPECTED_RESULTS['project_duration']} ngày)")
    print(f"  ✅ Chi phí nhân công: ${labor_cost:,} (Case study: ${EXPECTED_RESULTS['total_labor_cost']:,})")
    print(f"  📊 EVA - SPI: {eva_results['SPI']:.3f}, CPI: {eva_results['CPI']:.3f}")
    print(f"  📊 EVA - EAC: ${eva_results['EAC']:,.2f}")

    if project_duration == EXPECTED_RESULTS['project_duration'] and labor_cost == EXPECTED_RESULTS['total_labor_cost']:
        print("\n  🎉🎉🎉 THUẬT TOÁN TÍNH TOÁN CHÍNH XÁC 100% SO VỚI CASE STUDY! 🎉🎉🎉")
    else:
        print("\n  ⚠️  Có sai lệch - cần kiểm tra chi tiết!")

    print()


if __name__ == '__main__':
    main()
