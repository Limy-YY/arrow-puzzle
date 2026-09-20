# tests/test_level_generator.py
"""
对 level_generator 生成的关卡做「可行性」测试。

关键点：本文件用一套「自带的判定逻辑」独立模拟真实游戏，不调用生成器内部的 solver，
从而交叉验证「生成的关卡确实可玩」。模拟规则与 src/scenes/game.py 完全一致：

    点击箭头 -> 沿其指向逐格扫描直至棋盘边界：
        - 路径上有其它箭头  => 碰撞，扣 1 次失误，该箭头不消除（留在原地）
        - 路径上没有任何箭头  => 飞出棋盘，消除该格
    目标：失误耗尽/超时前消除所有箭头。

运行方式（任选其一）：
    python tests/test_level_generator.py
    python -m unittest discover -s tests -v
    pytest tests/ (若已安装 pytest，本文件兼容)
"""
import os
import sys
import unittest

# Windows 控制台默认 GBK，统一转 UTF-8，避免中文用例名/输出乱码
# 注意：unittest 的 verbose 输出默认写到 stderr，故 stdout/stderr 都要转换
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 让测试能直接 import src 下的 level_generator（src 不是包，手动加路径）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from level_generator import (  # noqa: E402
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIRECTIONS,
    generate_level, generate_normal_level, generate_hard_level,
    find_solution, is_solvable, is_solvable_dag, verify_solution, analyze_board,
)

# 独立的方向向量映射（与 settings.py 的 DIRECTION_DELTAS 一致，但刻意不 import，
# 以保证这是与生成器/游戏代码相互独立的一份规则定义，用于交叉验证）
_DELTA = {
    DIR_UP: (-1, 0),
    DIR_DOWN: (1, 0),
    DIR_LEFT: (0, -1),
    DIR_RIGHT: (0, 1),
}


def simulate_play(board, click_order):
    """独立模拟真实游戏：按 click_order 逐个点击箭头。

    返回 (是否全部消除, 碰撞失误次数, 有效点击次数)。
    这里刻意不 import level_generator 内部的 _ray_clear / find_solution，
    而是重新实现一遍游戏规则，从而独立检验。
    """
    rows = len(board)
    cols = len(board[0]) if rows else 0
    grid = [row[:] for row in board]
    mistakes = 0
    clicks = 0

    for (r, c) in click_order:
        if not (0 <= r < rows and 0 <= c < cols):
            return False, mistakes, clicks  # 越界坐标 => 非法顺序
        d = grid[r][c]
        if d == 0:
            return False, mistakes, clicks  # 点了已空的格子 => 非法顺序

        dr, dc = _DELTA[d]
        rr, cc = r + dr, c + dc
        blocked = False
        while 0 <= rr < rows and 0 <= cc < cols:
            if grid[rr][cc] != 0:
                blocked = True
                break
            rr += dr
            cc += dc

        if blocked:
            mistakes += 1      # 碰撞：扣失误，箭头留在原地
        else:
            grid[r][c] = 0     # 飞出消除
        clicks += 1

    cleared = all(v == 0 for row in grid for v in row)
    return cleared, mistakes, clicks


def count_arrows(board):
    return sum(1 for row in board for v in row if v != 0)


class TestGeneratedLevels(unittest.TestCase):
    """核心：验证生成的关卡确实可行（存在 0 失误的通关顺序）。"""

    def test_level_structure_matches_game_loader(self):
        """生成的 dict 必须能被 game.py 的 load 逻辑正确读取。"""
        level = generate_level(6, 3, 45, seed=1)
        # 对应 game.py：self.level_data['grid_size'] / ['map'] / .get(...)
        rows, cols = level['grid_size']
        self.assertEqual((rows, cols), (6, 6))
        self.assertEqual(len(level['map']), rows)
        self.assertTrue(all(len(r) == cols for r in level['map']))
        self.assertEqual(level['max_failures'], 3)          # game.py: .get('max_failures')
        self.assertEqual(level['arrows_left'], 6 * 6)       # game.py: .get('arrows_left')
        self.assertEqual(level['time_limit'], 45)           # game.py: .get('time_limit')

    def test_generated_levels_are_solvable(self):
        """多种尺寸、多种种子下，生成的关卡都必须可解。"""
        for rows in (2, 3, 4, 5, 6, 8, 10):
            for seed in range(4):
                with self.subTest(rows=rows, seed=seed):
                    level = generate_level(rows, max_mistakes=3, time_limit=60, seed=seed)
                    board = level['map']
                    self.assertTrue(
                        is_solvable_dag(board),
                        f"{rows}x{rows} seed={seed} 未通过 DAG 判定",
                    )
                    solution = find_solution(board)
                    self.assertIsNotNone(solution, f"{rows}x{rows} seed={seed} 贪心求不到解")
                    self.assertEqual(len(solution), count_arrows(board),
                                     "消除顺序步数应恰等于箭头数")

    def test_solution_replays_cleanly_in_game_simulation(self):
        """用独立的 game 模拟器重放解：应 0 失误、一次点击一个箭头全部清空。"""
        for rows in (3, 5, 8):
            for seed in range(3):
                with self.subTest(rows=rows, seed=seed):
                    level = generate_level(rows, max_mistakes=3, time_limit=60, seed=seed)
                    board = level['map']
                    solution = find_solution(board)
                    cleared, mistakes, clicks = simulate_play(board, solution)
                    self.assertTrue(cleared, "按解点击后应全部消除")
                    self.assertEqual(mistakes, 0, "完美解应 0 失误")
                    self.assertEqual(clicks, count_arrows(board),
                                     "每个箭头只需一次点击")

    def test_zero_mistakes_always_sufficient(self):
        """即使 max_mistakes=0，关卡也必须在 0 失误下可通关。"""
        for rows in (4, 7):
            level = generate_level(rows, max_mistakes=0, time_limit=60, seed=rows)
            board = level['map']
            solution = find_solution(board)
            cleared, mistakes, _ = simulate_play(board, solution)
            self.assertTrue(cleared and mistakes == 0,
                            "max_mistakes=0 时仍应存在 0 失误解")

    def test_solvers_agree(self):
        """两个独立判定器（贪心模拟 / DAG 拓扑）结论必须一致。

        除了生成的可解棋盘，还加入大量随机满盘（其中很多不可解），
        确保 DAG 判定器不会在无解棋盘上误判为可解。
        """
        import random
        boards = [
            [[DIR_RIGHT, DIR_RIGHT], [DIR_RIGHT, DIR_RIGHT]],   # 全右：可解
            [[DIR_DOWN, DIR_DOWN], [DIR_DOWN, DIR_DOWN]],        # 全下：可解
            [[DIR_RIGHT, DIR_LEFT], [DIR_RIGHT, DIR_LEFT]],      # 互指：不可解
        ]
        for _ in range(20):
            level = generate_level(6, 3, 60, seed=hash(os.urandom(4)) % 10_000)
            boards.append(level['map'])
        # 随机满盘：大概率不可解，能有效暴露 DAG 判定器的漏判
        rng = random.Random(0)
        for n in (3, 4, 5):
            for _ in range(40):
                boards.append([[rng.choice(DIRECTIONS) for _ in range(n)]
                               for _ in range(n)])

        for board in boards:
            with self.subTest(board=str(board)[:40]):
                self.assertEqual(is_solvable(board), is_solvable_dag(board),
                                 "两个判定器结论不一致")

    def test_dag_uses_full_ray_not_nearest(self):
        """回归：只按「最近箭头」建图会把可解/无解判反（静态图漏掉远处依赖）。

        该棋盘贪心判定为不可解；若 DAG 判定器只连最近箭头，会漏掉
        (0,0)↓ 与 (2,0)↑ 之间的死锁环而误判为可解。
        """
        board = [
            [DIR_DOWN, DIR_DOWN, DIR_DOWN],
            [DIR_RIGHT, DIR_RIGHT, DIR_DOWN],
            [DIR_UP, DIR_LEFT, DIR_DOWN],
        ]
        self.assertFalse(is_solvable(board))
        self.assertFalse(is_solvable_dag(board))
        self.assertIsNone(find_solution(board))

    def test_detects_unsolvable_deadlock(self):
        """两个箭头互指形成死锁：必须被判定为不可解（保证判定器不是恒 True）。"""
        deadlock = [[DIR_RIGHT, DIR_LEFT], [DIR_RIGHT, DIR_LEFT]]
        self.assertFalse(is_solvable(deadlock))
        self.assertFalse(is_solvable_dag(deadlock))
        self.assertIsNone(find_solution(deadlock))

    def test_verify_solution_rejects_bad_order(self):
        """一个错误的消除顺序应被 verify_solution 拒绝（保证校验不是恒 True）。"""
        board = [[DIR_RIGHT, DIR_RIGHT], [DIR_RIGHT, DIR_RIGHT]]
        bad_order = [(0, 0), (0, 1), (1, 0), (1, 1)]  # 先点最左列：路径被挡，非法
        self.assertFalse(verify_solution(board, bad_order))

    def test_reproducible_with_seed(self):
        a = generate_level(6, 3, 45, seed=42)['map']
        b = generate_level(6, 3, 45, seed=42)['map']
        self.assertEqual(a, b, "相同 seed 应生成相同关卡")

    def test_raises_on_invalid_params(self):
        for kwargs in (
            dict(rows=0, max_mistakes=3, time_limit=30),
            dict(rows=4, max_mistakes=-1, time_limit=30),
            dict(rows=4, max_mistakes=3, time_limit=0),
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    generate_level(**kwargs)

    def test_edge_sizes(self):
        # 1x1 单箭头：必可解
        level = generate_level(1, 0, 10)
        self.assertTrue(is_solvable(level['map']))
        # 非正方形（矩形）棋盘
        level = generate_level(3, 2, 30, cols=5, seed=7)
        self.assertEqual(level['grid_size'], [3, 5])
        self.assertTrue(is_solvable(level['map']))
        self.assertEqual(level['arrows_left'], 3 * 5)


class TestNormalLevels(unittest.TestCase):
    """普通版：既要可解，也要确实比简单版更难（可量化对比）。"""

    def test_normal_levels_are_solvable(self):
        """普通版生成的关卡必须可解，且消除顺序能 0 失误重放。"""
        for rows in (5, 6, 8):
            for seed in range(3):
                with self.subTest(rows=rows, seed=seed):
                    level = generate_normal_level(rows, 3, 60, seed=seed)
                    board = level["map"]
                    self.assertTrue(is_solvable_dag(board))
                    solution = find_solution(board)
                    self.assertIsNotNone(solution)
                    self.assertTrue(verify_solution(board, solution))
                    cleared, mistakes, _ = simulate_play(board, solution)
                    self.assertTrue(cleared and mistakes == 0)

    def test_normal_is_harder_than_easy(self):
        """普通版平均而言：平均依赖深度更高、相邻同向更少（方向更均衡）。"""
        rows = 8
        easy_avg = easy_same = normal_avg = normal_same = 0
        for seed in range(6):
            em = analyze_board(generate_level(rows, 3, 60, seed=seed)["map"])
            nm = analyze_board(generate_level(rows, 3, 60, seed=seed, difficulty="normal")["map"])
            easy_avg += em["avg_depth"]
            easy_same += em["same_dir_ratio"]
            normal_avg += nm["avg_depth"]
            normal_same += nm["same_dir_ratio"]
        self.assertGreater(normal_avg, easy_avg,
                           "普通版平均依赖深度应更高")
        self.assertLess(normal_same, easy_same,
                        "普通版相邻同向应更少")

    def test_normal_uses_all_four_directions(self):
        """普通版应四个方向都均衡出现（每个方向占比不低于约 1/8）。"""
        for rows in (6, 8):
            for seed in range(4):
                with self.subTest(rows=rows, seed=seed):
                    board = generate_normal_level(rows, 3, 60, seed=seed)["map"]
                    counts = {d: 0 for d in DIRECTIONS}
                    for row in board:
                        for v in row:
                            counts[v] += 1
                    self.assertGreaterEqual(
                        min(counts.values()), max(1, rows * rows // 10),
                        f"方向分布 {counts} 不够均衡",
                    )

    def test_normal_level_structure_matches_game_loader(self):
        level = generate_normal_level(8, 3, 60, seed=1, level=9)
        rows, cols = level["grid_size"]
        self.assertEqual((rows, cols), (8, 8))
        self.assertEqual(len(level["map"]), rows)
        self.assertTrue(all(len(r) == cols for r in level["map"]))
        self.assertEqual(level["max_failures"], 3)
        self.assertEqual(level["arrows_left"], 64)
        self.assertEqual(level["level"], 9)

    def test_generate_level_rejects_bad_difficulty(self):
        with self.assertRaises(ValueError):
            generate_level(4, 3, 30, difficulty="impossible")


class TestHardLevels(unittest.TestCase):
    """困难版：方向均衡、依赖链更深、开局即消更少，且可解。"""

    def test_hard_levels_are_solvable(self):
        """困难版生成的关卡必须可解，且消除顺序能 0 失误重放。"""
        for rows in (5, 6, 8):
            for seed in range(3):
                with self.subTest(rows=rows, seed=seed):
                    level = generate_hard_level(rows, 3, 60, seed=seed)
                    board = level["map"]
                    self.assertTrue(is_solvable_dag(board))
                    solution = find_solution(board)
                    self.assertIsNotNone(solution)
                    self.assertTrue(verify_solution(board, solution))
                    cleared, mistakes, _ = simulate_play(board, solution)
                    self.assertTrue(cleared and mistakes == 0)

    def test_hard_is_harder_than_normal(self):
        """困难版平均而言：平均依赖深度更高、开局即可消除的箭头更少。"""
        rows = 8
        normal_avg = normal_d0 = hard_avg = hard_d0 = 0
        for seed in range(6):
            nm = analyze_board(generate_level(rows, 3, 60, seed=seed, difficulty="normal")["map"])
            hm = analyze_board(generate_level(rows, 3, 60, seed=seed, difficulty="hard")["map"])
            normal_avg += nm["avg_depth"]
            normal_d0 += nm["depth0"]
            hard_avg += hm["avg_depth"]
            hard_d0 += hm["depth0"]
        self.assertGreater(hard_avg, normal_avg,
                           "困难版平均依赖深度应更高")
        self.assertLess(hard_d0, normal_d0,
                        "困难版开局即可消除的箭头应更少")

    def test_all_four_dimensions_monotonic(self):
        """三档难度在四个指标上严格单调：平均深度↑、最长链↑、开局即消↓、相邻同向↓。"""
        rows = 8
        agg = {"easy": {}, "normal": {}, "hard": {}}
        for diff in ("easy", "normal", "hard"):
            total = {"avg_depth": 0, "max_depth": 0, "depth0": 0, "same_dir_ratio": 0}
            for seed in range(6):
                m = analyze_board(generate_level(rows, 3, 60, seed=seed, difficulty=diff)["map"])
                for k in total:
                    total[k] += m[k]
            agg[diff] = {k: v / 6 for k, v in total.items()}

        e, n, h = agg["easy"], agg["normal"], agg["hard"]
        self.assertGreater(n["avg_depth"], e["avg_depth"], "平均深度应 easy<normal")
        self.assertGreater(h["avg_depth"], n["avg_depth"], "平均深度应 normal<hard")
        self.assertGreater(n["max_depth"], e["max_depth"], "最长链应 easy<normal")
        self.assertGreater(h["max_depth"], n["max_depth"], "最长链应 normal<hard")
        self.assertLess(n["depth0"], e["depth0"], "开局即消应 easy>normal")
        self.assertLess(h["depth0"], n["depth0"], "开局即消应 normal>hard")
        self.assertLess(n["same_dir_ratio"], e["same_dir_ratio"], "相邻同向应 easy>normal")
        self.assertLess(h["same_dir_ratio"], n["same_dir_ratio"], "相邻同向应 normal>hard")

    def test_hard_uses_all_four_directions(self):
        """困难版也应四个方向都均衡出现。"""
        for rows in (6, 8):
            for seed in range(4):
                with self.subTest(rows=rows, seed=seed):
                    board = generate_hard_level(rows, 3, 60, seed=seed)["map"]
                    counts = {d: 0 for d in DIRECTIONS}
                    for row in board:
                        for v in row:
                            counts[v] += 1
                    self.assertGreaterEqual(
                        min(counts.values()), max(1, rows * rows // 12),
                        f"方向分布 {counts} 不够均衡",
                    )

    def test_hard_level_structure_matches_game_loader(self):
        level = generate_hard_level(8, 3, 60, seed=1, level=10)
        rows, cols = level["grid_size"]
        self.assertEqual((rows, cols), (8, 8))
        self.assertEqual(len(level["map"]), rows)
        self.assertTrue(all(len(r) == cols for r in level["map"]))
        self.assertEqual(level["max_failures"], 3)
        self.assertEqual(level["arrows_left"], 64)
        self.assertEqual(level["level"], 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
