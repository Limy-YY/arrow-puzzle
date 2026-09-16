# Arrow Puzzle - 箭头消消乐

一个基于 Python + Pygame 开发的益智消除游戏。

## 玩法说明

点击无遮挡的箭头进行消除，遇到阻挡则产生碰撞反馈并扣除失误次数。清空所有箭头即可通关，失误次数耗尽则游戏失败。

## 环境要求

- Python 3.10+
- Pygame

## 安装与运行

```bash
# 创建虚拟环境
conda create -n arrow_env python=3.10
conda activate arrow_env

# 安装依赖
pip install -r requirements.txt

# 运行游戏
python src/main.py
