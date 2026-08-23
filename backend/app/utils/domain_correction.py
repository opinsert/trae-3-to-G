"""
领域数据纠错模块

基于拼音相似度的领域数据校正器，解决OCR识别错误和用户输入不规范问题。

核心功能：
1. 长度索引过滤 - 快速筛选候选词
2. 拼音相似度计算 - 解决同音词错误
3. 编辑距离匹配 - 综合字符和拼音相似度

参考论文：《一种基于智能体的G代码生成问答系统设计与实现》（郜宇博）
"""

from typing import List, Dict, Tuple, Optional
from pypinyin import lazy_pinyin
from difflib import SequenceMatcher


class DomainCorrector:
    """领域数据校正器"""

    # 数控加工领域标准术语表
    DEFAULT_STANDARD_TERMS = [
        # 加工类型
        "粗车", "精车", "半精车", "仿形", "切槽", "切断",
        "钻孔", "扩孔", "铰孔", "镗孔", "攻丝", "铣削",
        # 表面类型
        "外圆", "内圆", "端面", "圆弧", "锥面", "螺纹",
        "内螺纹", "外螺纹", "槽", "台阶", "倒角",
        # 刀具类型
        "车刀", "钻头", "铰刀", "镗刀", "丝锥", "铣刀",
        "外圆车刀", "内孔车刀", "切槽刀", "螺纹车刀",
        # 材料
        "钢", "铝", "铜", "铸铁", "不锈钢", "合金钢",
        # 其他常用术语
        "进给", "速度", "转速", "切削", "冷却", "润滑",
        "直径", "半径", "长度", "深度", "宽度", "角度"
    ]

    def __init__(self, standard_terms: Optional[List[str]] = None):
        """
        初始化校正器

        Args:
            standard_terms: 标准术语列表，为None时使用默认术语表
        """
        self.standard_terms = standard_terms or self.DEFAULT_STANDARD_TERMS
        self.length_index = self._build_length_index()

    def _build_length_index(self) -> Dict[int, List[str]]:
        """
        构建长度索引

        Returns:
            字典，key为词语长度，value为该长度的所有标准术语
        """
        index = {}
        for term in self.standard_terms:
            length = len(term)
            if length not in index:
                index[length] = []
            index[length].append(term)
        return index

    def correct(self, input_term: str, threshold: float = 0.50) -> str:
        """
        校正输入词语

        Args:
            input_term: 待校正的输入词语
            threshold: 相似度阈值（0-1），低于此值不进行校正

        Returns:
            校正后的词语（如果无匹配则返回原词）
        """
        if not input_term or not input_term.strip():
            return input_term

        input_term = input_term.strip()

        # 完全匹配直接返回
        if input_term in self.standard_terms:
            return input_term

        # 步骤1: 长度过滤
        candidates = self._length_filter(input_term)
        if not candidates:
            return input_term

        # 步骤2: 拼音相似度过滤
        pinyin_filtered = self._pinyin_filter(input_term, candidates)
        if not pinyin_filtered:
            return input_term

        # 步骤3: 综合评分匹配
        best_match, best_score = self._final_match(input_term, pinyin_filtered)

        return best_match if best_score >= threshold else input_term

    def correct_batch(self, input_terms: List[str], threshold: float = 0.50) -> List[str]:
        """
        批量校正

        Args:
            input_terms: 待校正的词语列表
            threshold: 相似度阈值

        Returns:
            校正后的词语列表
        """
        return [self.correct(term, threshold) for term in input_terms]

    def _length_filter(self, input_term: str, k: int = 2) -> List[str]:
        """
        长度索引过滤

        论文公式：k/m ≤ (m-α)/m ≤ 1 ≤ (m+α)/m
        其中 m 是输入词长度，k 是编辑距离阈值，α = k/m

        Args:
            input_term: 输入词语
            k: 编辑距离阈值

        Returns:
            候选词列表
        """
        m = len(input_term)
        if m == 0:
            return []

        alpha = k / m
        min_length = int(m * (1 - alpha))
        max_length = int(m * (1 + alpha)) + 1

        candidates = []
        for length in range(min_length, max_length):
            if length in self.length_index:
                candidates.extend(self.length_index[length])

        return candidates

    def _pinyin_filter(self,
                      input_term: str,
                      candidates: List[str],
                      min_similarity: float = 0.4) -> List[Tuple[str, float]]:
        """
        拼音相似度过滤

        Args:
            input_term: 输入词语
            candidates: 候选词列表
            min_similarity: 最小拼音相似度

        Returns:
            (候选词, 拼音相似度) 元组列表
        """
        input_pinyin = lazy_pinyin(input_term)
        filtered = []

        for candidate in candidates:
            candidate_pinyin = lazy_pinyin(candidate)
            pinyin_sim = self._pinyin_similarity(input_pinyin, candidate_pinyin)

            if pinyin_sim >= min_similarity:
                filtered.append((candidate, pinyin_sim))

        return filtered

    def _final_match(self,
                    input_term: str,
                    pinyin_filtered: List[Tuple[str, float]],
                    w1: float = 0.6,
                    w2: float = 0.4) -> Tuple[str, float]:
        """
        综合字符和拼音相似度进行最终匹配

        论文公式：Sim_final = w1·Sim_char + w2·Sim_pinyin

        Args:
            input_term: 输入词语
            pinyin_filtered: (候选词, 拼音相似度) 列表
            w1: 字符相似度权重
            w2: 拼音相似度权重

        Returns:
            (最佳匹配词, 综合相似度分数)
        """
        best_match = input_term
        best_score = 0.0

        for candidate, pinyin_sim in pinyin_filtered:
            # 字符相似度（使用SequenceMatcher快速计算）
            char_sim = SequenceMatcher(None, input_term, candidate).ratio()

            # 综合相似度
            final_score = w1 * char_sim + w2 * pinyin_sim

            if final_score > best_score:
                best_score = final_score
                best_match = candidate

        return best_match, best_score

    def _pinyin_similarity(self, pinyin1: List[str], pinyin2: List[str]) -> float:
        """
        计算拼音相似度

        论文公式：Sim_pinyin = 1 - ED_pinyin(P1,P2) / max(|P1|, |P2|)

        Args:
            pinyin1: 第一个词的拼音列表
            pinyin2: 第二个词的拼音列表

        Returns:
            拼音相似度（0-1）
        """
        if not pinyin1 or not pinyin2:
            return 0.0

        ed = self._edit_distance(pinyin1, pinyin2)
        max_len = max(len(pinyin1), len(pinyin2))

        return 1 - ed / max_len

    @staticmethod
    def _edit_distance(s1: List[str], s2: List[str]) -> int:
        """
        计算编辑距离（动态规划）

        Args:
            s1: 第一个序列
            s2: 第二个序列

        Returns:
            编辑距离
        """
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # 初始化边界
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        # 动态规划填表
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],      # 删除
                        dp[i][j-1],      # 插入
                        dp[i-1][j-1]     # 替换
                    )

        return dp[m][n]

    def add_terms(self, new_terms: List[str]) -> None:
        """
        添加新的标准术语

        Args:
            new_terms: 新术语列表
        """
        self.standard_terms.extend(new_terms)
        self.length_index = self._build_length_index()

    def get_statistics(self) -> Dict[str, int]:
        """
        获取统计信息

        Returns:
            统计字典
        """
        return {
            "total_terms": len(self.standard_terms),
            "unique_lengths": len(self.length_index),
            "max_length": max(self.length_index.keys()) if self.length_index else 0,
            "min_length": min(self.length_index.keys()) if self.length_index else 0
        }


# 预定义的校正器实例
default_corrector = DomainCorrector()


def quick_correct(input_term: str, threshold: float = 0.50) -> str:
    """
    快速校正单个词语（使用默认校正器）

    Args:
        input_term: 待校正的词语
        threshold: 相似度阈值

    Returns:
        校正后的词语
    """
    return default_corrector.correct(input_term, threshold)


def quick_correct_batch(input_terms: List[str], threshold: float = 0.50) -> List[str]:
    """
    快速批量校正（使用默认校正器）

    Args:
        input_terms: 待校正的词语列表
        threshold: 相似度阈值

    Returns:
        校正后的词语列表
    """
    return default_corrector.correct_batch(input_terms, threshold)
