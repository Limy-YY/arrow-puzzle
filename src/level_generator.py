# src/level_generator.py
"""
自动生成「可通关」箭头消消乐关卡的模块。

游戏规则（判定逻辑的核心）：
- 棋盘为 rows × cols 的网格，每个格子为空(0)或一个方向箭头（1 上 / 2 下 / 3 左 / 4 右）。
- 点击一个箭头后，它会沿自身指向飞出；若「指向方向直至棋盘边界」的路径上没有任何
  其他箭头阻挡，则该箭头飞出棋盘并被消除；否则视为碰撞、扣除一次失误。
- 关卡目标：在限时内、失误耗尽前消除所有箭头。

由此可导出「可解」的充要条件：
  对每个箭头 X，把「X 前进路径上的每一个箭头 Y」连一条有向边 X→Y（表示 Y 必须先于 X
  被消除）。这些边构成一张有向依赖图；当且仅当该图无环（DAG）时，存在合法消除顺序
  （沿该图的拓扑序，从外向内逐个消除）。注意：不能只连「离 X 最近的箭头」——那会漏掉
  路径上更远处、被先消除的中间箭头暴露出来的依赖（见 is_solvable_dag 的说明）。

生成策略（构造上保证可解）：
  采用「逆序构造」——从空棋盘出发，按「逆消除顺序」逐个放置箭头。放置每个箭头时，
  要求其「前进路径」上不存在任何「已放置」的箭头。可以证明：只要每步都满足该约束，
  最终棋盘按「放置顺序的逆序」消除就一定合法（因此放置顺序反过来即为一个可行解）。

  实现：回溯搜索 + 最少可选方向启发(MRV)，随机打散方向以获得多样性。若某空格已无
  可选方向则立即回溯；由于「全右 / 全下」这类棋盘必然可解，搜索总能找到解。

  本模块不依赖 pygame（方向编码与 src/settings.py 保持一致），可单独运行测试。
"""
from __future__ import annotations

import json
import random
import sys
from collections import deque

# 方向编码，与 src/settings.py 保持一致
DIR_UP = 1
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4
DIRECTIONS = (DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT)

_DIRECTION_DELTAS = {
    DIR_UP: (-1, 0),
    DIR_DOWN: (1, 0),
    DIR_LEFT: (0, -1),
    DIR_RIGHT: (0, 1),
}

_DIRECTION_SYMBOL = {
    DIR_UP: '↑',
    DIR_DOWN: '↓',
    DIR_LEFT: '←',
    DIR_RIGHT: '→',
}


# === 规则基础 ===

def _cells_ahead(rows, cols, r, c, direction):
    """生成 (r, c) 沿 direction 前进、直到棋盘边界之前的所有格子坐标。"""
    dr, dc = _DIRECTION_DELTAS[direction]
    r += dr
    c += dc
    while 0 <= r < rows and 0 <= c < cols:
        yield r, c
        r += dr
        c += dc


def _ray_clear(grid, rows, cols, r, c, direction):
    """判断 (r, c) 沿 direction 的前进路径上是否存在任何非空格子（False 表示被阻挡）。"""
    for rr, cc in _cells_ahead(rows, cols, r, c, direction):
        if grid[rr][cc] != 0:
            return False
    return True


# === 可解性判定（两个相互独立的实现，用于交叉验证）===

def find_solution(board):
    """贪心模拟：反复消除「当前可飞出」的箭头，返回一个合法的消除顺序 [(r,c), ...]。

    若无法消除所有箭头（死锁）则返回 None。正确性：只要棋盘可解，就至少存在一个
    「前进路径为空」的箭头（合法消除顺序的第一个箭头必满足）；且消除任意一个当前
    可飞出的箭头都不会破坏剩余棋盘的可解性（消除只会让别的箭头路径更空）。故贪心
    必能清空。
    """
    rows = len(board)
    cols = len(board[0]) if rows else 0
    grid = [row[:] for row in board]
    solution = []

    while True:
        free = None
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 0:
                    continue
                if _ray_clear(grid, rows, cols, r, c, grid[r][c]):
                    free = (r, c)
                    break
            if free is not None:
                break

        if free is None:
            # 仍有剩余箭头却无可消除者 => 死锁
            remaining = sum(1 for row in grid for v in row if v != 0)
            return None if remaining > 0 else solution

        r, c = free
        solution.append((r, c))
        grid[r][c] = 0


def _forward_arrows(rows, cols, board, r, c):
    """返回 (r, c) 前进路径上的**所有**箭头坐标（自近及远）。"""
    result = []
    for rr, cc in _cells_ahead(rows, cols, r, c, board[r][c]):
        if board[rr][cc] != 0:
            result.append((rr, cc))
    return result


def is_solvable_dag(board):
    """独立实现：构建「完整依赖图」并用 Kahn 拓扑排序判断是否无环。

    对每个箭头 X，把 X 前进路径上的**每一个**箭头 Y 都连一条有向边 X→Y（Y 必须先于 X
    消除）。注意必须是「所有箭头」而非仅「离 X 最近的箭头」：若只连最近者，当最近的
    中间箭头被先消除后，路径上更远处的箭头会暴露出新的依赖，静态图会漏判（必要而不
    充分）。当且仅当该完整依赖图无环时，存在合法消除顺序。
    """
    rows = len(board)
    cols = len(board[0]) if rows else 0
    nodes = [(r, c) for r in range(rows) for c in range(cols) if board[r][c] != 0]

    outgoing = {n: _forward_arrows(rows, cols, board, *n) for n in nodes}
    indegree = {n: 0 for n in nodes}
    for n in nodes:
        for m in outgoing[n]:
            indegree[m] += 1

    # Kahn 拓扑排序
    queue = deque(n for n in nodes if indegree[n] == 0)
    seen = 0
    while queue:
        n = queue.popleft()
        seen += 1
        for m in outgoing[n]:
            indegree[m] -= 1
            if indegree[m] == 0:
                queue.append(m)
    return seen == len(nodes)


def is_solvable(board):
    """主判定入口：等价于存在合法消除顺序。"""
    return find_solution(board) is not None


def verify_solution(board, solution):
    """严格重放一个消除顺序，校验每一步都符合「路径无阻挡」规则，且最终全部清空。"""
    rows = len(board)
    cols = len(board[0]) if rows else 0
    grid = [row[:] for row in board]
    for (r, c) in solution:
        d = grid[r][c]
        if d == 0:
            return False  # 该格已空或本为空，顺序非法
        if not _ray_clear(grid, rows, cols, r, c, d):
            return False  # 前进路径上仍有箭头 => 按此顺序点击会发生碰撞
        grid[r][c] = 0
    return all(v == 0 for row in grid for v in row)


# === 难度分析 ===

def _neighbors(rows, cols, r, c):
    """四邻域坐标生成器。"""
    for dr, dc in _DIRECTION_DELTAS.values():
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            yield nr, nc


def compute_depths(board):
    """计算每个箭头的「依赖深度」= 消除它之前，最多需要先消除多少个箭头。

    深度 0 表示开局即可飞出（前进路径为空）；深度越大，越需要前瞻推理。
    这里使用「前进路径上的所有箭头」构建完整依赖图，取其中最长路径作为深度
    （保证深度准确反映最长依赖链，而非仅按最近箭头计）。
    """
    rows = len(board)
    cols = len(board[0]) if rows else 0

    outgoing = {}
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                continue
            outgoing[(r, c)] = _forward_arrows(rows, cols, board, r, c)

    depth = {}
    visiting = set()

    def calc(node):
        if node in depth:
            return depth[node]
        if node in visiting:
            # 环（无解棋盘）——本指标只用于可解棋盘，这里给 0 防死循环
            return 0
        visiting.add(node)
        nxts = outgoing[node]
        depth[node] = 0 if not nxts else 1 + max(calc(m) for m in nxts)
        visiting.remove(node)
        return depth[node]

    for node in outgoing:
        calc(node)
    return depth


def analyze_board(board):
    """返回关卡的难度指标（用于量化对比不同难度）。

    返回 dict：
        arrows         箭头总数
        depth0         开局即可消除的箭头数（越少越需要思考）
        max_depth      最长依赖链（越大越难）
        avg_depth      平均依赖深度
        same_dir_ratio 相邻同向箭头占比（越低方向越多样）
    """
    rows = len(board)
    cols = len(board[0]) if rows else 0
    depths = compute_depths(board)
    arrows = len(depths)
    max_depth = max(depths.values()) if depths else 0
    avg_depth = sum(depths.values()) / arrows if arrows else 0.0
    depth0 = sum(1 for v in depths.values() if v == 0)

    same = 0
    total_pairs = 0
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                continue
            for nr, nc in _neighbors(rows, cols, r, c):
                if board[nr][nc] != 0:
                    total_pairs += 1
                    if board[nr][nc] == board[r][c]:
                        same += 1
    same_dir_ratio = (same / total_pairs) if total_pairs else 0.0

    return {
        "arrows": arrows,
        "depth0": depth0,
        "max_depth": max_depth,
        "avg_depth": round(avg_depth, 2),
        "same_dir_ratio": round(same_dir_ratio, 2),
    }


# === 关卡生成 ===

def _generate_board(rows, cols, rng, weighted=False):
    """逆序构造一个「保证可解」的满棋盘，返回二维方向数组。

    weighted=False（简单基盘）：均匀随机选择可选方向。
    weighted=True（深底盘）：按「前方空位越多越优先、相邻同向越少越优先」加权选择方向，
              从而拉长依赖链、压低开局即消的箭头数、增加方向多样性。
    """
    board = [[0] * cols for _ in range(rows)]
    total = rows * cols

    def free_directions(r, c):
        return [d for d in DIRECTIONS if _ray_clear(board, rows, cols, r, c, d)]

    def direction_weight(r, c, d):
        """加权启发式：前方空位越多、相邻同向越少，权重越高。"""
        empty_ahead = sum(1 for _ in _cells_ahead(rows, cols, r, c, d))
        same_as_neighbor = sum(
            1 for nr, nc in _neighbors(rows, cols, r, c) if board[nr][nc] == d
        )
        return (empty_ahead + 1) * 3.0 - same_as_neighbor * 6.0

    def fill(count):
        if count == total:
            return True

        # 选择「可选方向最少」的空格（MRV 启发式），显著减少回溯
        best = None
        for r in range(rows):
            for c in range(cols):
                if board[r][c] != 0:
                    continue
                dirs = free_directions(r, c)
                if not dirs:
                    # 该空格已无可选方向，随着后续填充约束只会更紧，必然死局 => 回溯
                    return False
                if best is None or len(dirs) < best[0]:
                    best = (len(dirs), r, c)

        _, r, c = best
        dirs = free_directions(r, c)
        if weighted:
            # 加权随机排序：权重越高越靠前，同时保留随机性，让不同种子生成不同棋盘
            dirs = sorted(dirs, key=lambda d: direction_weight(r, c, d) * rng.random(),
                          reverse=True)
        else:
            rng.shuffle(dirs)

        for d in dirs:
            board[r][c] = d
            if fill(count + 1):
                return True
            board[r][c] = 0
        return False

    if not fill(0):
        # 理论不可达：全右/全下棋盘必然可解
        raise RuntimeError("棋盘生成失败（理论上不应发生）")
    return board


def _difficulty_score(m):
    """把难度指标合成一个标量，越大越难（综合依赖链、平均深度、开局即消、方向多样性）。"""
    return (m["max_depth"] * 3 + m["avg_depth"] * 12
            - m["depth0"] * 2 - m["same_dir_ratio"] * 60)


def _best_base_board(rows, cols, rng, attempts):
    """从若干「逆序构造」的深底盘里挑难度得分最高的一个，作为爬山优化的起点。"""
    best_board = None
    best_score = None
    for _ in range(attempts):
        board = _generate_board(rows, cols, rng, weighted=True)
        score = _difficulty_score(analyze_board(board))
        if best_score is None or score > best_score:
            best_board, best_score = board, score
    return best_board


def _hillclimb_balance(board, rng, iters, bal, spread_w, cap_avg, w_avg, w_d0, w_sr):
    """在保证可解的前提下，通过「翻转单个箭头」爬山，优化方向均衡与依赖深度。

    每步随机翻转一个箭头的方向；若翻转后棋盘仍可解（用完整依赖图的 DAG 判定），且综合
    得分不下降，则接受，否则回退。得分 = 方向均衡度（最少方向次数 + 极差惩罚）+ 依赖
    深度 + 开局即消 + 相邻同向的加权和（权重由调用方给定，据此区分「普通」与「困难」
    两档）。返回方向均衡、且可解性仍被保证的棋盘。
    """
    rows = len(board)
    cols = len(board[0]) if rows else 0
    cur = [row[:] for row in board]

    def score():
        depths = compute_depths(cur)
        arrows = len(depths)
        avg = sum(depths.values()) / arrows if arrows else 0.0
        depth0 = sum(1 for v in depths.values() if v == 0)
        cnt = {}
        for row in cur:
            for v in row:
                cnt[v] = cnt.get(v, 0) + 1
        minc = min(cnt.get(d, 0) for d in DIRECTIONS)
        spread = max(cnt.get(d, 0) for d in DIRECTIONS) - minc
        same = 0
        total_pairs = 0
        for r in range(rows):
            for c in range(cols):
                if cur[r][c] == 0:
                    continue
                for nr, nc in _neighbors(rows, cols, r, c):
                    if cur[nr][nc] != 0:
                        total_pairs += 1
                        if cur[nr][nc] == cur[r][c]:
                            same += 1
        sr = (same / total_pairs) if total_pairs else 0.0
        return (bal * minc
                - spread_w * spread
                + w_avg * min(avg, cap_avg)
                + w_d0 * depth0
                + w_sr * sr)

    cur_score = score()
    for _ in range(iters):
        r = rng.randrange(rows)
        c = rng.randrange(cols)
        old = cur[r][c]
        nd = rng.choice([d for d in DIRECTIONS if d != old])
        cur[r][c] = nd
        if is_solvable_dag(cur):
            s = score()
            if s >= cur_score:
                cur_score = s
            else:
                cur[r][c] = old
        else:
            cur[r][c] = old
    return cur


def _generate_board_normal(rows, cols, rng, attempts=3):
    """普通版：方向均衡（四方向大致各 1/4）+ 中等依赖深度。

    先逆序构造一个深底盘，再用爬山把方向翻均衡，同时保留中等深度（平均深度约 7）。
    逆序构造保证可解；爬山的每一步都只接受仍可解的翻转，故最终棋盘依然可解。

    迭代次数取经验下界（8x8 实测 800 轮即可四方向各 ≥12 个、平均深度 >6），
    线性随棋盘规模增长即可，避免在无谓的翻牌上浪费时间。
    """
    base = _best_base_board(rows, cols, rng, attempts)
    return _hillclimb_balance(
        base, rng, iters=max(600, rows * cols * 15),
        bal=6, spread_w=3, cap_avg=6, w_avg=7, w_d0=-1, w_sr=-20,
    )


def _generate_board_hard(rows, cols, rng, attempts=3):
    """困难版：方向均衡 + 更深的依赖链 + 更少的开局即消箭头（平均深度约 11）。

    相比普通版，困难版把「平均深度上限」抬高到 11、把「开局即消」与「相邻同向」的
    惩罚压得更重，从而在四档难度指标上都严格难过普通版（平均深度↑、最长链↑、
    开局即消↓、相邻同向↓）。
    """
    base = _best_base_board(rows, cols, rng, attempts)
    return _hillclimb_balance(
        base, rng, iters=max(1200, rows * cols * 30),
        bal=6, spread_w=3, cap_avg=11, w_avg=7, w_d0=-5, w_sr=-250,
    )


def generate_level(rows, max_mistakes, time_limit, cols=None, seed=None, level=0,
                   difficulty="easy"):
    """生成一个「可通关」关卡，返回与 data/levels.json 相同结构的 dict。

    参数：
        rows         棋盘行数（≥1 的整数；默认生成正方形棋盘）
        max_mistakes 最大失误次数（≥0 的整数）
        time_limit   时间限制（>0，秒）
        cols         棋盘列数（可选，默认等于 rows）
        seed         随机种子（可选，用于复现）
        level        关卡编号（写入 levels.json 时使用；0 表示未分配，默认 0）
        difficulty   难度："easy"（简单）、"normal"（普通：方向均衡 + 中等深度）或
                     "hard"（困难：方向均衡 + 深依赖链 + 更少开局即消）

    返回字段：level / grid_size / max_failures / arrows_left / time_limit / map。
    生成的 map 为满棋盘（每个格子都有箭头），与现有关卡一致。
    """
    if not isinstance(rows, int) or isinstance(rows, bool) or rows < 1:
        raise ValueError("rows 必须为 ≥1 的整数")
    if cols is None:
        cols = rows
    if not isinstance(cols, int) or isinstance(cols, bool) or cols < 1:
        raise ValueError("cols 必须为 ≥1 的整数")
    if not isinstance(max_mistakes, int) or isinstance(max_mistakes, bool) or max_mistakes < 0:
        raise ValueError("max_mistakes 必须为 ≥0 的整数")
    if not isinstance(time_limit, (int, float)) or time_limit <= 0:
        raise ValueError("time_limit 必须为 >0 的数值")
    if difficulty not in ("easy", "normal", "hard"):
        raise ValueError("difficulty 必须为 'easy'、'normal' 或 'hard'")

    rng = random.Random(seed)
    if difficulty == "normal":
        board = _generate_board_normal(rows, cols, rng)
    elif difficulty == "hard":
        board = _generate_board_hard(rows, cols, rng)
    else:
        board = _generate_board(rows, cols, rng, weighted=False)

    return {
        "level": level,  # 关卡编号；由调用方在写入 levels.json 时指定
        "grid_size": [rows, cols],
        "max_failures": max_mistakes,
        "arrows_left": rows * cols,
        "time_limit": time_limit,
        "map": board,
    }


def generate_normal_level(rows, max_mistakes, time_limit, cols=None, seed=None, level=0):
    """生成一个普通版关卡（方向均衡 + 中等依赖深度）。"""
    return generate_level(rows, max_mistakes, time_limit, cols=cols, seed=seed,
                          level=level, difficulty="normal")


def generate_hard_level(rows, max_mistakes, time_limit, cols=None, seed=None, level=0):
    """生成一个困难版关卡（方向均衡 + 深依赖链 + 更少开局即消）。"""
    return generate_level(rows, max_mistakes, time_limit, cols=cols, seed=seed,
                          level=level, difficulty="hard")


def board_to_str(board):
    """用箭头符号把棋盘打印成可读的多行文本。"""
    return "\n".join(
        " ".join(_DIRECTION_SYMBOL.get(v, '·') for v in row)
        for row in board
    )


def _json_scalar(value):
    """序列化标量：整数化的 float 输出为 int（避免出现 45.0 这类字样）。"""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return json.dumps(value)


def level_to_json(level, indent=4):
    """把单个关卡 dict 序列化为与 data/levels.json 相同风格的 JSON 字符串。

    输出形如（可直接粘贴进 levels.json 的 "levels" 数组里）：
        {
            "level": 1,
            "grid_size": [6, 6],
            "max_failures": 3,
            "arrows_left": 36,
            "time_limit": 45,
            "map": [
                [1, 4, 1, 4, 4, 1],
                ...
            ]
        }
    """
    pad1 = " " * indent
    pad2 = " " * (indent * 2)
    map_body = ",\n".join(pad2 + json.dumps(row) for row in level["map"])
    return (
        "{\n"
        f'{pad1}"level": {_json_scalar(level["level"])},\n'
        f'{pad1}"grid_size": {json.dumps(level["grid_size"])},\n'
        f'{pad1}"max_failures": {_json_scalar(level["max_failures"])},\n'
        f'{pad1}"arrows_left": {_json_scalar(level["arrows_left"])},\n'
        f'{pad1}"time_limit": {_json_scalar(level["time_limit"])},\n'
        f'{pad1}"map": [\n'
        f"{map_body}\n"
        f"{pad1}]\n"
        "}"
    )


def generate_level_json(rows, max_mistakes, time_limit, cols=None, seed=None, level=1,
                        difficulty="easy"):
    """生成一个关卡，并直接返回可直接粘贴进 data/levels.json 的 JSON 字符串。"""
    level_dict = generate_level(
        rows, max_mistakes, time_limit, cols=cols, seed=seed, level=level,
        difficulty=difficulty,
    )
    return level_to_json(level_dict)


if __name__ == "__main__":
    import argparse

    # Windows 控制台默认 GBK，统一转 UTF-8 避免中文/箭头符号乱码或编码报错
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    def _time(v):
        f = float(v)
        return int(f) if f.is_integer() else f

    parser = argparse.ArgumentParser(
        description="生成可通关的箭头消消乐关卡，输出可直接粘贴进 data/levels.json 的 JSON。",
    )
    parser.add_argument("rows", nargs="?", type=int, default=6,
                        help="棋盘行数（正方形棋盘，默认 6）")
    parser.add_argument("max_mistakes", nargs="?", type=int, default=3,
                        help="最大失误次数（默认 3）")
    parser.add_argument("time_limit", nargs="?", type=_time, default=45,
                        help="时间限制秒数（默认 45）")
    parser.add_argument("--level", type=int, default=1,
                        help="关卡编号；追加到 levels.json 时设为当前最大编号 + 1（默认 1）")
    parser.add_argument("--cols", type=int, default=None,
                        help="列数（默认等于行数，可生成矩形棋盘）")
    parser.add_argument("--seed", type=int, default=None,
                        help="随机种子（可选，用于复现同一关卡）")
    parser.add_argument("--difficulty", choices=("easy", "normal", "hard"), default="easy",
                        help="关卡难度：easy 简单 / normal 普通 / hard 困难（默认 easy）")
    parser.add_argument("--metrics", action="store_true",
                        help="在 stderr 打印难度指标（依赖链/平均深度/开局即消/同向比）")
    args = parser.parse_args()

    level = generate_level(
        args.rows, args.max_mistakes, args.time_limit,
        cols=args.cols, seed=args.seed, level=args.level, difficulty=args.difficulty,
    )
    print(level_to_json(level))  # stdout 保持纯净 JSON，方便复制
    if args.metrics:
        m = analyze_board(level["map"])
        print(f"难度指标：最长依赖链={m['max_depth']} 平均深度={m['avg_depth']} "
              f"开局即消={m['depth0']}/{m['arrows']} 相邻同向={m['same_dir_ratio']}",
              file=sys.stderr)
    print(f"提示：level 编号为 {args.level}，把上面内容粘贴到 data/levels.json 的 levels 数组中即可。",
          file=sys.stderr)
