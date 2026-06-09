"""
Module 4: Earned Value Analysis (EVA - Phân tích Giá trị Thu được)
====================================================================
Tính toán các chỉ số hiệu suất dự án tại một thời điểm kiểm tra (Time Now),
bao gồm PV, EV, AC, SV, CV, SPI, CPI, EAC, ETC, VAC.

Công thức toán học:
    - PV (Planned Value):   Tổng ngân sách kế hoạch đáng lẽ phải chi đến Time Now
    - EV (Earned Value):    Tổng giá trị công việc thực tế đã hoàn thành
    - AC (Actual Cost):     Tổng chi phí thực tế đã chi
    - SV = EV - PV          (< 0: trễ tiến độ)
    - CV = EV - AC          (< 0: vượt ngân sách)
    - SPI = EV / PV         (< 1: trễ tiến độ)
    - CPI = EV / AC         (< 1: vượt ngân sách)
    - BAC = Tổng ngân sách kế hoạch
    - EAC = BAC / CPI       (Dự báo tổng chi phí cuối cùng)
    - ETC = EAC - AC         (Chi phí cần thêm)
    - VAC = BAC - EAC        (Chênh lệch khi hoàn thành)
"""

from typing import Dict, List, Any, Optional
import networkx as nx


def calculate_task_budget(
    G: nx.DiGraph,
    resource_costs: Dict[str, float]
) -> Dict[str, float]:
    """
    Tính ngân sách (Budget at Completion) cho từng task dựa trên
    duration × tổng daily cost của resources.

    Args:
        G: Đồ thị dự án đã tính CPM
        resource_costs: Mapping resource_type -> daily_cost

    Returns:
        Dict mapping task_id -> budget
    """
    budgets = {}
    for node, data in G.nodes(data=True):
        resources = data.get('resources', [])
        daily_cost = sum(resource_costs.get(r, 0) for r in resources)
        duration = data.get('normal_duration', data['duration'])
        budgets[node] = daily_cost * duration
    return budgets


def calculate_pv_by_day(
    G: nx.DiGraph,
    budgets: Dict[str, float],
    time_now: int
) -> float:
    """
    Tính Planned Value (PV) tại thời điểm time_now.

    PV tính dựa trên lịch baseline (ES/EF ban đầu):
    - Task đã hoàn thành theo kế hoạch (EF <= time_now): PV += 100% budget
    - Task đang thực hiện theo kế hoạch (ES < time_now < EF): 
      PV += budget × (time_now - ES) / duration
    - Task chưa bắt đầu theo kế hoạch: PV += 0

    Args:
        G: Đồ thị dự án
        budgets: Ngân sách từng task
        time_now: Thời điểm kiểm tra (ngày)

    Returns:
        Tổng PV
    """
    pv = 0.0

    for node, data in G.nodes(data=True):
        budget = budgets.get(node, 0)
        es = data['es']
        ef = data['ef']
        duration = data['duration']

        if time_now >= ef:
            # Task đáng lẽ phải xong 100% theo kế hoạch
            pv += budget
        elif time_now > es:
            # Task đang thực hiện, tính tỷ lệ
            theoretical_percent = (time_now - es) / duration
            pv += budget * theoretical_percent
        # else: chưa bắt đầu → PV = 0

    return pv


def calculate_eva(
    G: nx.DiGraph,
    time_now: int,
    actual_data: Dict[str, Dict[str, float]],
    resource_costs: Dict[str, float],
    budgets: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Thực hiện phân tích Earned Value đầy đủ.

    Args:
        G: Đồ thị dự án đã tính CPM (baseline schedule)
        time_now: Thời điểm kiểm tra (ngày)
        actual_data: Dữ liệu thực tế cho từng task, mỗi entry chứa:
            - 'percent_complete': % hoàn thành (0-100)
            - 'actual_cost': Chi phí thực tế đã chi
        resource_costs: Mapping resource_type -> daily_cost
        budgets: Ngân sách đã tính sẵn (optional, sẽ tự tính nếu không có)

    Returns:
        Dict chứa tất cả chỉ số EVA
    """
    # Tính budget nếu chưa có
    if budgets is None:
        budgets = calculate_task_budget(G, resource_costs)

    # BAC = Budget at Completion (tổng ngân sách toàn dự án)
    BAC = sum(budgets.values())

    # ============================================
    # 1. Tính PV (Planned Value)
    # ============================================
    PV = calculate_pv_by_day(G, budgets, time_now)

    # ============================================
    # 2. Tính EV (Earned Value)
    # ============================================
    EV = 0.0
    for node in G.nodes():
        budget = budgets.get(node, 0)
        task_actual = actual_data.get(node, {})
        percent_complete = task_actual.get('percent_complete', 0) / 100.0
        EV += budget * percent_complete

    # ============================================
    # 3. Tính AC (Actual Cost)
    # ============================================
    AC = sum(
        actual_data.get(node, {}).get('actual_cost', 0)
        for node in G.nodes()
    )

    # ============================================
    # 4. Tính các chỉ số phái sinh
    # ============================================
    # Schedule Variance
    SV = EV - PV
    # Cost Variance
    CV = EV - AC

    # Schedule Performance Index
    SPI = EV / PV if PV > 0 else 1.0
    # Cost Performance Index
    CPI = EV / AC if AC > 0 else 1.0

    # Estimate At Completion
    EAC = BAC / CPI if CPI > 0 else float('inf')
    # Estimate To Complete
    ETC = EAC - AC
    # Variance At Completion
    VAC = BAC - EAC

    # Dự báo ngày hoàn thành
    project_duration = max(G.nodes[n]['ef'] for n in G.nodes())
    estimated_completion = project_duration / SPI if SPI > 0 else float('inf')

    # ============================================
    # 5. Đánh giá sức khỏe dự án
    # ============================================
    health_status = []
    if SPI < 1.0:
        health_status.append("⚠️ TRỄ TIẾN ĐỘ (Behind Schedule)")
    elif SPI > 1.0:
        health_status.append("✅ NHANH HƠN KẾ HOẠCH (Ahead of Schedule)")
    else:
        health_status.append("✅ ĐÚNG TIẾN ĐỘ (On Schedule)")

    if CPI < 1.0:
        health_status.append("⚠️ VƯỢT NGÂN SÁCH (Over Budget)")
    elif CPI > 1.0:
        health_status.append("✅ TIẾT KIỆM NGÂN SÁCH (Under Budget)")
    else:
        health_status.append("✅ ĐÚNG NGÂN SÁCH (On Budget)")

    # ============================================
    # 6. Chi tiết EV từng task
    # ============================================
    task_details = []
    for node in sorted(G.nodes()):
        budget = budgets.get(node, 0)
        task_actual = actual_data.get(node, {})
        pct = task_actual.get('percent_complete', 0)
        ac = task_actual.get('actual_cost', 0)
        ev = budget * (pct / 100.0)

        task_details.append({
            'task': node,
            'budget': budget,
            'percent_complete': pct,
            'EV': ev,
            'AC': ac,
            'variance': ev - ac
        })

    return {
        # Chỉ số chính
        'BAC': round(BAC, 2),
        'PV': round(PV, 2),
        'EV': round(EV, 2),
        'AC': round(AC, 2),

        # Phương sai
        'SV': round(SV, 2),
        'CV': round(CV, 2),

        # Chỉ số hiệu suất
        'SPI': round(SPI, 3),
        'CPI': round(CPI, 3),

        # Dự báo
        'EAC': round(EAC, 2),
        'ETC': round(ETC, 2),
        'VAC': round(VAC, 2),
        'estimated_completion_days': round(estimated_completion, 1),

        # Đánh giá
        'health_status': health_status,
        'task_details': task_details,
        'time_now': time_now
    }


def print_eva_results(eva_results: Dict[str, Any]):
    """
    In kết quả EVA ra console dạng dashboard.
    """
    print("\n" + "=" * 70)
    print("PHÂN TÍCH GIÁ TRỊ THU ĐƯỢC (Earned Value Analysis)")
    print(f"Thời điểm kiểm tra: Ngày {eva_results['time_now']}")
    print("=" * 70)

    # Bảng chỉ số chính
    print("\n📊 CHỈ SỐ CHÍNH:")
    print(f"  {'BAC (Tổng ngân sách):':<35} ${eva_results['BAC']:>12,.2f}")
    print(f"  {'PV (Giá trị kế hoạch):':<35} ${eva_results['PV']:>12,.2f}")
    print(f"  {'EV (Giá trị thu được):':<35} ${eva_results['EV']:>12,.2f}")
    print(f"  {'AC (Chi phí thực tế):':<35} ${eva_results['AC']:>12,.2f}")

    print("\n📈 CHỈ SỐ HIỆU SUẤT:")
    print(f"  {'SV (Schedule Variance):':<35} ${eva_results['SV']:>12,.2f}")
    print(f"  {'CV (Cost Variance):':<35} ${eva_results['CV']:>12,.2f}")
    print(f"  {'SPI (Schedule Perf. Index):':<35} {eva_results['SPI']:>12.3f}")
    print(f"  {'CPI (Cost Perf. Index):':<35} {eva_results['CPI']:>12.3f}")

    print("\n🔮 DỰ BÁO:")
    print(f"  {'EAC (Dự báo tổng chi phí):':<35} ${eva_results['EAC']:>12,.2f}")
    print(f"  {'ETC (Chi phí cần thêm):':<35} ${eva_results['ETC']:>12,.2f}")
    print(f"  {'VAC (Chênh lệch cuối cùng):':<35} ${eva_results['VAC']:>12,.2f}")
    print(f"  {'Ngày hoàn thành dự kiến:':<35} {eva_results['estimated_completion_days']:>12.1f} ngày")

    print("\n🏥 ĐÁNH GIÁ SỨC KHỎE DỰ ÁN:")
    for status in eva_results['health_status']:
        print(f"  {status}")

    # Bảng chi tiết từng task
    print("\n📋 CHI TIẾT TỪNG TASK:")
    print(f"  {'Task':<6} {'Budget':>10} {'%Done':>8} {'EV':>10} {'AC':>10} {'Variance':>10}")
    print("  " + "-" * 60)

    for detail in eva_results['task_details']:
        if detail['percent_complete'] > 0 or detail['AC'] > 0:
            print(
                f"  {detail['task']:<6} "
                f"${detail['budget']:>9,.2f} "
                f"{detail['percent_complete']:>7.0f}% "
                f"${detail['EV']:>9,.2f} "
                f"${detail['AC']:>9,.2f} "
                f"${detail['variance']:>9,.2f}"
            )

    print("=" * 70)
