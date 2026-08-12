import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

# Create figure and axes with ample dimensions
fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
ax.set_xlim(0, 18)
ax.set_ylim(0, 10.5)
ax.axis('off')

# Professional Academic Color Palette (IEEE Style)
COLOR_BG = '#FFFFFF'
COLOR_BORDER = '#334155'
COLOR_ENCODING = '#E0F2FE'        # Light Blue
COLOR_ENCODING_BORDER = '#0284C7'
COLOR_ATTN = '#FFE4E6'            # Light Rose
COLOR_ATTN_BORDER = '#E11D48'
COLOR_FFN = '#FEF3C7'             # Light Amber
COLOR_FFN_BORDER = '#D97706'
COLOR_OUTPUT = '#DCFCE7'          # Light Emerald
COLOR_OUTPUT_BORDER = '#059669'
COLOR_TEXT = '#0F172A'

fig.patch.set_facecolor('white')

# Title
ax.text(9, 9.8, "Kiến trúc Concept Cơ chế Chú ý Nâng cao (Graphormer Advanced Attention)",
        ha='center', va='center', fontsize=15, fontweight='bold', color=COLOR_TEXT)

# Helper function to draw rounded boxes
def draw_box(ax, x, y, w, h, bg_color, border_color, title, subtitle="", boxstyle="round,pad=0.3,rounding_size=0.15"):
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle=boxstyle,
                                facecolor=bg_color, edgecolor=border_color, linewidth=1.5, zorder=2)
    ax.add_patch(box)
    if subtitle:
        ax.text(x + w/2, y + h/2 + 0.22, title, ha='center', va='center', fontsize=10.5, fontweight='bold', color=COLOR_TEXT, zorder=3)
        ax.text(x + w/2, y + h/2 - 0.22, subtitle, ha='center', va='center', fontsize=9, color='#334155', zorder=3)
    else:
        ax.text(x + w/2, y + h/2, title, ha='center', va='center', fontsize=10.5, fontweight='bold', color=COLOR_TEXT, zorder=3)

# Helper function to draw arrows
def draw_arrow(ax, start, end, label=""):
    arrow = patches.FancyArrowPatch(start, end, arrowstyle='->,head_width=4,head_length=6',
                                    color='#475569', linewidth=1.5, zorder=4)
    ax.add_patch(arrow)
    if label:
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        ax.text(mid_x, mid_y + 0.15, label, ha='center', va='center', fontsize=8.5, color='#64748B', zorder=5)

# --- 1. INPUT LAYER ---
draw_box(ax, 0.5, 3.2, 2.7, 3.0, '#F1F5F9', COLOR_BORDER, "Input AON Graph", "Đồ thị Dị thể $G(V,E)$\nTasks + Resources + Shifts")

# --- 2. STRUCTURAL ENCODINGS LAYER ---
enc_group_box = patches.FancyBboxPatch((3.9, 0.8), 3.8, 7.3, boxstyle="round,pad=0.25",
                                       facecolor='#F0F9FF', edgecolor='#38BDF8', linestyle='--', linewidth=1.3, zorder=1)
ax.add_patch(enc_group_box)
ax.text(5.8, 8.5, "Mã hóa Cấu trúc (Structural Encodings)", ha='center', va='center', fontsize=11, fontweight='bold', color='#0369A1')

draw_box(ax, 4.3, 5.8, 3.0, 1.8, COLOR_ENCODING, COLOR_ENCODING_BORDER, "Spatial Encoding", "$b_{\\text{spatial}}(v_i, v_j) = \\text{SPD}(v_i, v_j)$")
draw_box(ax, 4.3, 3.6, 3.0, 1.8, COLOR_ENCODING, COLOR_ENCODING_BORDER, "Centrality Encoding", "$z_{d^-}(v_i) + z_{d^+}(v_i)$")
draw_box(ax, 4.3, 1.4, 3.0, 1.8, COLOR_ENCODING, COLOR_ENCODING_BORDER, "Edge Encoding", "$c_{ij} = \\text{Embed}(e_{ij}, \\text{PDM})$")

# Connect Input to Encodings
draw_arrow(ax, (3.2, 4.7), (4.3, 6.7))
draw_arrow(ax, (3.2, 4.7), (4.3, 4.5))
draw_arrow(ax, (3.2, 4.7), (4.3, 2.3))

# Summation Circle
sum_circle = patches.Circle((8.5, 4.7), radius=0.4, facecolor='#BAE6FD', edgecolor='#0284C7', linewidth=1.5, zorder=3)
ax.add_patch(sum_circle)
ax.text(8.5, 4.7, "$\\bigoplus$", ha='center', va='center', fontsize=15, fontweight='bold', color='#0369A1', zorder=4)

draw_arrow(ax, (7.3, 6.7), (8.15, 5.0))
draw_arrow(ax, (7.3, 4.5), (8.1, 4.7))
draw_arrow(ax, (7.3, 2.3), (8.15, 4.4))

# --- 3. ADVANCED MULTI-HEAD ATTENTION BLOCK ---
attn_group_box = patches.FancyBboxPatch((9.7, 1.5), 4.2, 6.6, boxstyle="round,pad=0.25",
                                        facecolor='#FFF1F2', edgecolor='#FDA4AF', linestyle='--', linewidth=1.3, zorder=1)
ax.add_patch(attn_group_box)
ax.text(11.8, 8.5, "Khối Attention Nâng cao (Graphormer)", ha='center', va='center', fontsize=11, fontweight='bold', color='#BE123C')

draw_box(ax, 10.1, 5.1, 3.4, 2.3, COLOR_ATTN, COLOR_ATTN_BORDER, "Biểu thức Bias Attention", "$A_{ij} = \\frac{(h_i W_Q)(h_j W_K)^T}{\\sqrt{d}} + b_{ij}$")
draw_box(ax, 10.1, 2.1, 3.4, 2.3, COLOR_ATTN, COLOR_ATTN_BORDER, "Multi-Head Aggregator", "Softmax $(A_{ij}) \\cdot (h_j W_V)$")

draw_arrow(ax, (8.9, 4.7), (10.1, 6.25))
draw_arrow(ax, (11.8, 5.1), (11.8, 4.4))

# --- 4. FFN & NORM LAYER ---
draw_arrow(ax, (13.5, 3.25), (14.6, 3.25))

draw_box(ax, 14.6, 1.9, 2.8, 2.7, COLOR_FFN, COLOR_FFN_BORDER, "FFN & Residual", "LayerNorm $(h + \\text{Attn})$\nFFN $(h_{\\text{out}})$")

# --- 5. OUTPUT PREDICTIONS ---
draw_arrow(ax, (16.0, 4.6), (16.0, 5.9))

draw_box(ax, 14.4, 5.9, 3.2, 2.2, COLOR_OUTPUT, COLOR_OUTPUT_BORDER, "Dự báo Đầu ra", "Thời gian $\\hat{y}_i$ & Risk $\\text{CI}_i$\nKhắc phục Over-squashing")

# Adjust margins and save
plt.tight_layout()
os.makedirs(r"c:\CNTT\KY8-2026\Logistics-Project-Progress-Cost-Management\docs\baocao2\image", exist_ok=True)
out_path = r"c:\CNTT\KY8-2026\Logistics-Project-Progress-Cost-Management\docs\baocao2\image\hinh4_1_advanced_attention.png"
plt.savefig(out_path, bbox_inches='tight', dpi=300)
plt.close()
print(f"Successfully generated clean {out_path}")
