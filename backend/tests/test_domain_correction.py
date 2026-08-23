"""
领域数据纠错模块单元测试
"""

import pytest
from app.utils.domain_correction import (
    DomainCorrector,
    quick_correct,
    quick_correct_batch
)


class TestDomainCorrector:
    """领域数据校正器测试类"""

    @pytest.fixture
    def corrector(self):
        """创建测试用校正器"""
        return DomainCorrector()

    def test_exact_match(self, corrector):
        """测试完全匹配的情况"""
        assert corrector.correct("粗车") == "粗车"
        assert corrector.correct("外圆") == "外圆"
        assert corrector.correct("精车") == "精车"

    def test_ocr_errors(self, corrector):
        """测试OCR常见错误"""
        # 形近字错误（字形相似导致的OCR错误）
        assert corrector.correct("组车") == "粗车"  # 组 -> 粗（形近）
        assert corrector.correct("外园") == "外圆"  # 园 -> 圆（形近）
        assert corrector.correct("精东") == "精车"  # 东 -> 车（形近，较远）

        # 同音或近音词错误
        assert corrector.correct("钻空") == "钻孔"  # kong -> kong
        assert corrector.correct("切曹") == "切槽"  # cao -> cao

    def test_user_input_variations(self, corrector):
        """测试用户输入变体"""
        # 多字（长度差异较大，可能保持原样）
        result = corrector.correct("粗车加工")
        # 由于长度差异，通常会保持原样
        assert result in ["粗车加工", "粗车"]

        # 近似匹配
        assert corrector.correct("车刃") == "车刀"  # 刃 接近 刀

    def test_pinyin_similarity(self, corrector):
        """测试拼音相似度计算"""
        # 同音不同字
        assert corrector.correct("钻空") == "钻孔"  # kong -> kong
        assert corrector.correct("刀角") == "倒角"  # dao jiao
        assert corrector.correct("切曹") == "切槽"  # cao -> cao

    def test_no_match_returns_original(self, corrector):
        """测试无匹配时返回原词"""
        result = corrector.correct("完全不相关的词汇xyz")
        assert result == "完全不相关的词汇xyz"

    def test_empty_input(self, corrector):
        """测试空输入"""
        assert corrector.correct("") == ""
        assert corrector.correct("   ") == "   "

    def test_batch_correction(self, corrector):
        """测试批量校正"""
        inputs = ["组车", "外园", "精车"]
        expected = ["粗车", "外圆", "精车"]
        results = corrector.correct_batch(inputs)
        assert results == expected

    def test_custom_terms(self):
        """测试自定义术语表"""
        custom_terms = ["自定义术语1", "自定义术语2"]
        custom_corrector = DomainCorrector(standard_terms=custom_terms)

        assert custom_corrector.correct("自定义术语1") == "自定义术语1"
        assert custom_corrector.correct("自订义术语1") == "自定义术语1"

    def test_add_terms(self, corrector):
        """测试动态添加术语"""
        new_term = "新加工类型"
        corrector.add_terms([new_term])

        assert new_term in corrector.standard_terms
        assert corrector.correct(new_term) == new_term
        assert corrector.correct("新加エ类型") == new_term  # 错别字

    def test_threshold_effect(self, corrector):
        """测试阈值对结果的影响"""
        # 低阈值：更容易匹配
        result_low = corrector.correct("粗削", threshold=0.5)
        # 高阈值：更严格
        result_high = corrector.correct("粗削", threshold=0.9)

        # 低阈值应该能匹配到"粗车"
        assert result_low == "粗车"
        # 高阈值可能保持原样
        assert result_high in ["粗削", "粗车"]

    def test_statistics(self, corrector):
        """测试统计信息"""
        stats = corrector.get_statistics()

        assert "total_terms" in stats
        assert stats["total_terms"] > 0
        assert "unique_lengths" in stats
        assert "max_length" in stats
        assert "min_length" in stats

    def test_length_filter(self, corrector):
        """测试长度过滤逻辑"""
        # 长度相近的词应该被过滤进候选集
        candidates = corrector._length_filter("粗车")
        assert len(candidates) > 0
        assert "精车" in candidates  # 同样2字
        assert "半精车" in candidates  # 3字（在容差范围内）

    def test_pinyin_filter(self, corrector):
        """测试拼音过滤逻辑"""
        candidates = ["粗车", "出车", "精车", "外圆"]
        filtered = corrector._pinyin_filter("出车", candidates)

        # 应该包含"粗车"（拼音相近）
        filtered_terms = [term for term, _ in filtered]
        assert "粗车" in filtered_terms
        assert "出车" in filtered_terms  # 完全相同

    def test_edit_distance(self, corrector):
        """测试编辑距离计算"""
        # 相同序列
        assert corrector._edit_distance(["a"], ["a"]) == 0

        # 一个替换
        assert corrector._edit_distance(["a"], ["b"]) == 1

        # 一个插入
        assert corrector._edit_distance(["a"], ["a", "b"]) == 1

        # 一个删除
        assert corrector._edit_distance(["a", "b"], ["b"]) == 1

        # 复杂情况
        assert corrector._edit_distance(["cu", "che"], ["chu", "che"]) == 1


class TestQuickFunctions:
    """测试快速调用函数"""

    def test_quick_correct(self):
        """测试快速校正"""
        assert quick_correct("组车") == "粗车"
        assert quick_correct("外园") == "外圆"

    def test_quick_correct_batch(self):
        """测试快速批量校正"""
        inputs = ["组车", "外园", "精车"]
        expected = ["粗车", "外圆", "精车"]
        results = quick_correct_batch(inputs)
        assert results == expected


class TestRealWorldScenarios:
    """真实场景测试"""

    @pytest.fixture
    def corrector(self):
        return DomainCorrector()

    def test_ocr_process_workflow(self, corrector):
        """模拟OCR工序图识别工作流"""
        ocr_results = {
            "加工类型": "组车",      # OCR错误（形近字）
            "表面": "外园",          # OCR错误
            "刀具": "车刃",          # OCR错误（形近字）
            "材料": "钢"            # 正确
        }

        corrected = {
            key: corrector.correct(value)
            for key, value in ocr_results.items()
        }

        assert corrected["加工类型"] == "粗车"
        assert corrected["表面"] == "外圆"
        assert corrected["刀具"] == "车刀"
        assert corrected["材料"] == "钢"

    def test_multi_character_terms(self, corrector):
        """测试多字术语"""
        # 3-4字术语
        assert corrector.correct("外圆车到") == "外圆车刀"
        assert corrector.correct("不秀钢") == "不锈钢"
        assert corrector.correct("内螺纹") == "内螺纹"  # 正确的保持

    def test_partial_match(self, corrector):
        """测试部分匹配"""
        # 用户可能只输入部分
        result = corrector.correct("外")
        # 应该不会错误匹配
        assert len(result) >= 1

    def test_case_sensitivity(self, corrector):
        """测试大小写（中文无大小写，但测试混合输入）"""
        # 如果有英文混合
        custom = DomainCorrector(standard_terms=["CNC", "G代码", "M代码"])
        assert custom.correct("CNC") == "CNC"
        # 小写可能无法匹配（拼音转换对英文支持有限）
        result = custom.correct("cnc")
        assert result in ["cnc", "CNC"]  # 可能保持原样

    def test_performance_batch(self, corrector):
        """测试批量性能"""
        # 100个词的批量校正应该很快
        inputs = ["组车", "外园", "精车"] * 34  # 102个

        import time
        start = time.time()
        results = corrector.correct_batch(inputs)
        duration = time.time() - start

        assert len(results) == len(inputs)
        assert duration < 1.0  # 应该在1秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
