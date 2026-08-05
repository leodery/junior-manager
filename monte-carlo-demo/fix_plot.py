"""修复版画图 - 用之前蒙特卡洛模拟的硬编码结果，不重新跑模拟"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# 之前模拟跑出来的硬编码结果
BS_PRICE = 10.450584
SIZES = [10_000, 100_000, 1_000_000, 10_000_000, 50_000_000]
ERRORS = [0.222553, 0.043920, 0.005379, 0.002491, 0.000155]
TIMES = [3.36, 3.31, 3.22, 3.80, 4.13]
CPU_COUNT = 20


def plot_convergence_fixed():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # 左图：误差收敛（对数-对数）
    ax = axes[0]
    ax.loglog(SIZES, ERRORS, 'o-', color='#534AB7', linewidth=2.2, markersize=10,
              label='MC 模拟误差', zorder=3)
    # 理论收敛速率 O(1/√N)
    ref = ERRORS[0] * np.sqrt(SIZES[0]) / np.sqrt(SIZES)
    ax.loglog(SIZES, ref, '--', color='#D85A30', alpha=0.75, linewidth=1.8,
              label=r'$O(1/\sqrt{N})$ 理论收敛速率', zorder=2)
    ax.set_xlabel('模拟路径数 N', fontsize=12)
    ax.set_ylabel('|MC − BS| 绝对误差', fontsize=12)
    ax.set_title(f'蒙特卡洛误差收敛性  (Black-Scholes 基准 = {BS_PRICE:.4f})',
                 fontsize=13, fontweight='medium')
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(fontsize=11, loc='upper right')

    # 标注关键点
    for n, err in zip(SIZES, ERRORS):
        ax.annotate(f'{err:.4f}', xy=(n, err), xytext=(8, 8),
                    textcoords='offset points', fontsize=9,
                    color='#26215C', alpha=0.85)

    # 右图：计算时间 vs 样本量
    ax = axes[1]
    ax.plot(SIZES, TIMES, 's-', color='#0F6E56', linewidth=2.2, markersize=10, zorder=3)
    ax.set_xlabel('模拟路径数 N', fontsize=12)
    ax.set_ylabel('计算时间（秒）', fontsize=12)
    ax.set_title(f'计算耗时  (CPU 核心数 = {CPU_COUNT})',
                 fontsize=13, fontweight='medium')
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    for n, t in zip(SIZES, TIMES):
        ax.annotate(f'{t:.2f}s', xy=(n, t), xytext=(8, -14),
                    textcoords='offset points', fontsize=9,
                    color='#085041', alpha=0.85)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'convergence.png')
    plt.savefig(out_path, dpi=130, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"图表已保存: {out_path}")
    return out_path


if __name__ == '__main__':
    plot_convergence_fixed()
