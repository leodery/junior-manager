"""
蒙特卡洛模拟定价欧式看涨期权 + 希腊字母
=======================================
对比 Black-Scholes 解析解，测试模拟精度随样本量的收敛性

负载特征:
  - 5000 万条模拟路径（numpy 矢量化）
  - 多进程并行（multiprocessing Pool）
  - 内存峰值 ~2 GB
  - 单机 8 核满载约 30-60 秒

经济学背景:
  欧式看涨期权 = 到期日 T 以执行价 K 买入标的的权利（非义务）
  Black-Scholes 公式给出解析解:
      C = S0 * N(d1) - K * e^{-rT} * N(d2)
  其中 d1 = (ln(S0/K) + (r + σ²/2)T) / (σ√T)
       d2 = d1 - σ√T
  蒙特卡洛模拟用 GBM (几何布朗运动) 生成到期股价:
      S_T = S0 * exp((r - 0.5σ²)T + σ√T * Z),  Z ~ N(0,1)
  期权价格 = e^{-rT} * E[max(S_T - K, 0)]
"""
import time
import os
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
from multiprocessing import Pool, cpu_count
from functools import partial

# ---------- 1. 参数 ----------
S0 = 100.0        # 标的现价
K = 100.0         # 执行价
T = 1.0           # 到期时间（年）
r = 0.05          # 无风险利率
sigma = 0.20      # 波动率
N_PATHS = 50_000_000  # 5000 万条路径
CHUNK_SIZE = 2_000_000  # 每块 200 万
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------- 2. Black-Scholes 解析解（基准） ----------
def black_scholes_call(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


def black_scholes_greeks(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    delta = norm.cdf(d1)
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T)
    return delta, gamma, vega


# ---------- 3. 蒙特卡洛模拟（单块，矢量化） ----------
def mc_chunk(n_paths, S0, K, T, r, sigma, seed_offset):
    """单块模拟：n_paths 条路径，返回期权现值"""
    rng = np.random.default_rng(seed_offset)
    z = rng.standard_normal(n_paths)
    s_t = S0 * np.exp((r - 0.5 * sigma ** 2) * T + sigma * np.sqrt(T) * z)
    payoff = np.maximum(s_t - K, 0.0)
    return np.sum(payoff)  # 返回总和，外层汇总（节省内存）


def mc_call_price(n_paths, S0, K, T, r, sigma, n_workers=None):
    """多进程并行蒙特卡洛定价"""
    n_workers = n_workers or cpu_count()
    n_chunks = (n_paths + CHUNK_SIZE - 1) // CHUNK_SIZE
    # 每块用不同 seed，避免重复
    seeds = [1000 * i + 7 for i in range(n_chunks)]
    sizes = [CHUNK_SIZE if i < n_chunks - 1
             else n_paths - CHUNK_SIZE * (n_chunks - 1)
             for i in range(n_chunks)]

    fn = partial(mc_chunk, S0=S0, K=K, T=T, r=r, sigma=sigma)
    # multiprocessing 需要可 pickle 的参数
    args = [(sizes[i], S0, K, T, r, sigma, seeds[i]) for i in range(n_chunks)]
    with Pool(n_workers) as pool:
        sums = pool.starmap(mc_chunk, args)

    total_payoff = sum(sums)
    total_n = sum(sizes)
    price = np.exp(-r * T) * (total_payoff / total_n)
    return price


# ---------- 4. 希腊字母（有限差分 bump-and-recompute） ----------
def mc_delta_gamma(n_paths, S0, K, T, r, sigma, h=0.01):
    """用有限差分计算 Delta 和 Gamma"""
    price_up = mc_call_price(n_paths, S0 + h, K, T, r, sigma)
    price_dn = mc_call_price(n_paths, S0 - h, K, T, r, sigma)
    price_mid = mc_call_price(n_paths, S0, K, T, r, sigma)
    delta = (price_up - price_dn) / (2 * h)
    gamma = (price_up - 2 * price_mid + price_dn) / (h ** 2)
    return delta, gamma, price_mid


# ---------- 5. 收敛性测试 ----------
def convergence_test(S0, K, T, r, sigma, sizes):
    """测试不同样本量下的蒙特卡洛误差"""
    bs_price = black_scholes_call(S0, K, T, r, sigma)
    print(f"  Black-Scholes 基准价: {bs_price:.6f}")
    errors = []
    times = []
    for n in sizes:
        t0 = time.time()
        mc_price = mc_call_price(n, S0, K, T, r, sigma)
        dt = time.time() - t0
        err = abs(mc_price - bs_price)
        errors.append(err)
        times.append(dt)
        print(f"  N={n:>12,d}  MC={mc_price:.6f}  err={err:.6f}  t={dt:.2f}s")
    return bs_price, errors, times


# ---------- 6. 画图 ----------
def plot_convergence(sizes, errors, times, bs_price, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # 左图：误差收敛（对数-对数）
    ax = axes[0]
    ax.loglog(sizes, errors, 'o-', color='#534AB7', linewidth=2, markersize=8, label='MC 误差')
    # 理论收敛速率 O(1/√N)
    ref = errors[0] * np.sqrt(sizes[0]) / np.sqrt(sizes)
    ax.loglog(sizes, ref, '--', color='#D85A30', alpha=0.7, label=r'$O(1/\sqrt{N})$ 理论')
    ax.set_xlabel('模拟路径数 N', fontsize=12)
    ax.set_ylabel('|MC - BS| 绝对误差', fontsize=12)
    ax.set_title(f'蒙特卡洛误差收敛  (BS 基准 = {bs_price:.4f})', fontsize=13)
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(fontsize=11)

    # 右图：计算时间 vs 样本量
    ax = axes[1]
    ax.plot(sizes, times, 's-', color='#0F6E56', linewidth=2, markersize=8)
    ax.set_xlabel('模拟路径数 N', fontsize=12)
    ax.set_ylabel('计算时间（秒）', fontsize=12)
    ax.set_title(f'计算耗时  (CPU 核心数 = {cpu_count()})', fontsize=13)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  图表已保存: {out_path}")


# ---------- 7. 主流程 ----------
def main():
    print("=" * 70)
    print("蒙特卡洛模拟定价欧式看涨期权")
    print("=" * 70)
    print(f"参数: S0={S0}, K={K}, T={T}, r={r}, σ={sigma}")
    print(f"总路径数: {N_PATHS:,}")
    print(f"CPU 核心数: {cpu_count()}")
    print()

    # 1. Black-Scholes 解析解
    print("[1/4] Black-Scholes 解析解")
    bs_price = black_scholes_call(S0, K, T, r, sigma)
    bs_delta, bs_gamma, bs_vega = black_scholes_greeks(S0, K, T, r, sigma)
    print(f"  价格 = {bs_price:.6f}")
    print(f"  Delta = {bs_delta:.6f}")
    print(f"  Gamma = {bs_gamma:.6f}")
    print(f"  Vega  = {bs_vega:.6f}")
    print()

    # 2. 大规模蒙特卡洛定价
    print(f"[2/4] 蒙特卡洛模拟 ({N_PATHS:,} 条路径)")
    t0 = time.time()
    mc_price = mc_call_price(N_PATHS, S0, K, T, r, sigma)
    dt = time.time() - t0
    print(f"  MC 价格 = {mc_price:.6f}")
    print(f"  误差   = {abs(mc_price - bs_price):.6f}")
    print(f"  耗时   = {dt:.2f}s")
    print(f"  速率   = {N_PATHS / dt / 1e6:.2f} 百万路径/秒")
    print()

    # 3. 希腊字母（用较小样本量，bump 3 次）
    print("[3/4] 蒙特卡洛希腊字母（5 百万路径 × 3 次 bump）")
    t0 = time.time()
    mc_delta, mc_gamma, mc_price_small = mc_delta_gamma(5_000_000, S0, K, T, r, sigma)
    dt = time.time() - t0
    print(f"  MC Delta = {mc_delta:.6f}  (误差 {abs(mc_delta - bs_delta):.6f})")
    print(f"  MC Gamma = {mc_gamma:.6f}  (误差 {abs(mc_gamma - bs_gamma):.6f})")
    print(f"  耗时 = {dt:.2f}s")
    print()

    # 4. 收敛性测试
    print("[4/4] 收敛性测试（不同样本量）")
    sizes = [10_000, 100_000, 1_000_000, 10_000_000, 50_000_000]
    bs_p, errors, times = convergence_test(S0, K, T, r, sigma, sizes)
    print()

    # 5. 输出对比表
    print("=" * 70)
    print("最终对比表")
    print("=" * 70)
    print(f"{'指标':<10}{'Black-Scholes':>18}{'蒙特卡洛':>18}{'误差':>14}")
    print("-" * 60)
    print(f"{'价格':<10}{bs_price:>18.6f}{mc_price:>18.6f}{abs(mc_price-bs_price):>14.6f}")
    print(f"{'Delta':<10}{bs_delta:>18.6f}{mc_delta:>18.6f}{abs(mc_delta-bs_delta):>14.6f}")
    print(f"{'Gamma':<10}{bs_gamma:>18.6f}{mc_gamma:>18.6f}{abs(mc_gamma-bs_gamma):>14.6f}")

    # 6. 画收敛图
    out_path = os.path.join(OUTPUT_DIR, 'convergence.png')
    plot_convergence(sizes, errors, times, bs_p, out_path)

    print()
    print("=" * 70)
    print(f"完成！图表: {out_path}")
    print("=" * 70)


if __name__ == '__main__':
    main()
