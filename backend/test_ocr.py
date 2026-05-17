import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.ocr_processor import ocr_recognize
import base64

def test_ocr_on_image(image_path):
    print("\n" + "="*80)
    print("百度OCR识别测试")
    print("="*80)
    
    if not os.path.exists(image_path):
        print("ERROR: 图片文件不存在:", image_path)
        print("请将测试图片放在 backend 目录下，或指定正确的图片路径")
        return
    
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        print("图片路径:", image_path)
        print("图片数据长度:", len(image_data), "字符")
        
        result = ocr_recognize(image_data)
        
        print("\n" + "="*80)
        print("OCR识别结果")
        print("="*80)
        
        print("\n【基本信息】")
        print("  产品名称:", result.get('product_name') or "(未识别)")
        print("  工序名称:", result.get('process_name') or "(未识别)")
        print("  工序编号:", result.get('process_number') or "(未识别)")
        print("  版本号:", result.get('version') or "(未识别)")
        print("  设备名称:", result.get('equipment') or "(未识别)")
        print("  数控系统:", result.get('control_system') or "(未识别)")
        print("  夹具名称:", result.get('fixture') or "(未识别)")
        print("  材料名称:", result.get('material') or "(未识别)")
        
        print("\n【刀具信息】")
        print("  刀具名称:", result.get('tool_name') or "(未识别)")
        print("  刀具长度:", result.get('tool_length') or 0)
        print("  刀具直径:", result.get('tool_diameter') or 0)
        
        print("\n【工步列表】")
        steps = result.get('steps', [])
        if steps and len(steps) > 0:
            for step in steps:
                print("  [工步", step.get('sequence'), "]", step.get('content', ''))
        else:
            print("  (未识别到工步)")
        
        if result.get('raw_text'):
            print("\n【原始识别文本】")
            print("-"*60)
            lines = result['raw_text'].split('\n')[:15]
            for line in lines:
                print(line)
            lines_count = len(result['raw_text'].split('\n'))
            if lines_count > 15:
                print("... (还有", lines_count - 15, "行)")
            print("-"*60)
        
        if result.get('error'):
            print("\nWARN:", result['error'])
        
        print("\n" + "="*80)
        print("OCR识别测试完成")
        print("="*80)
        
    except Exception as e:
        print("\nERROR: OCR识别失败:", str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("="*80)
        print("使用说明")
        print("="*80)
        print("方法1: python test_ocr.py test.jpg")
        print("方法2: python test_ocr.py \"图片完整路径.jpg\"")
        print("\n请将测试图片放在 backend 目录下，或指定图片路径")
        image_path = "test.jpg"
    
    test_ocr_on_image(image_path)