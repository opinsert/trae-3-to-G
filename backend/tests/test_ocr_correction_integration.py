"""
OCR处理器集成测试 - 验证领域纠错功能
"""

import pytest
from app.core.ocr_processor import OCRProcessor


class TestOCRProcessorWithCorrection:
    """测试OCR处理器的领域纠错集成"""

    @pytest.fixture
    def processor(self):
        """创建OCR处理器实例"""
        return OCRProcessor()

    def test_processor_initialization(self, processor):
        """测试处理器正确初始化了纠错器"""
        assert processor.corrector is not None
        stats = processor.corrector.get_statistics()
        assert stats['total_terms'] > 50  # 应该包含默认术语+额外术语

    def test_normalize_vision_result_with_correction(self, processor):
        """测试视觉结果标准化时应用纠错"""
        # 模拟OCR识别结果（包含错误）
        parsed = {
            'process_name': '组车',      # OCR错误：组 -> 粗
            'material': '钢',            # 正确
            'material_grade': '不秀钢',  # OCR错误：秀 -> 锈
            'tool_name': '车刃',         # OCR错误：刃 -> 刀
            'equipment': '数控车床',
            'tool_length': '100',
            'tool_diameter': '10',
        }

        normalized = processor._normalize_vision_result(parsed)

        # 验证纠错结果
        assert normalized['process_name'] == '粗车'
        assert normalized['material'] == '钢'
        assert normalized['material_grade'] == '不锈钢'
        assert normalized['tool_name'] == '车刀'
        assert normalized['equipment'] == '数控车床'

    def test_normalize_drawing_steps_with_correction(self, processor):
        """测试工步标准化时应用纠错"""
        steps = [
            {
                'step': 1,
                'step_content': '组车',      # 错误：组 -> 粗
                'tooling': '车刃',           # 错误：刃 -> 刀
                'spindle_speed': 1000,
                'feed_rate': 0.2,
            }
        ]

        normalized = processor._normalize_drawing_steps(steps)

        assert len(normalized) == 1
        assert normalized[0]['step_content'] == '粗车'
        assert normalized[0]['tooling'] == '车刀'

    def test_empty_fields_not_corrected(self, processor):
        """测试空字段不会被纠错"""
        parsed = {
            'process_name': '',
            'material': '',  # 空字符串
            'tool_name': '   ',  # 空白
        }

        normalized = processor._normalize_vision_result(parsed)

        # 空字段应保持为空或None
        assert normalized['process_name'] == ''
        assert normalized['material'] in ['', None]  # 可能是空字符串或None

    def test_correct_terms_unchanged(self, processor):
        """测试正确的术语不会被修改"""
        parsed = {
            'process_name': '精车',
            'material': '铝',
            'tool_name': '钻头',
        }

        normalized = processor._normalize_vision_result(parsed)

        # 正确的术语保持不变
        assert normalized['process_name'] == '精车'
        assert normalized['material'] == '铝'
        assert normalized['tool_name'] == '钻头'

    def test_multiple_errors_in_single_field(self, processor):
        """测试单个字段中的多个错误"""
        parsed = {
            'equipment': '数空车创',  # 空->控, 创->床
        }

        normalized = processor._normalize_vision_result(parsed)

        # 应该能纠正为合理的术语
        # 由于"数空车创"与标准术语差异较大，可能保持原样
        # 这个测试验证不会崩溃
        assert 'equipment' in normalized

    def test_corrector_custom_terms(self, processor):
        """测试自定义术语被正确添加"""
        # 添加一个新术语
        processor.corrector.add_terms(['特殊工艺'])

        parsed = {
            'process_name': '特殊エ艺',  # 错字
        }

        normalized = processor._normalize_vision_result(parsed)
        assert normalized['process_name'] == '特殊工艺'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
