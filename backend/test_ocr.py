import asyncio
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.ocr_processor import ocr_recognize


def run_ocr_on_image(image_path):
    print("\n" + "=" * 80)
    print("视觉 GPT 识别测试")
    print("=" * 80)

    if not os.path.exists(image_path):
        print("ERROR: 图片文件不存在:", image_path)
        return

    try:
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        result = asyncio.run(ocr_recognize(image_data))
        print("OCR识别结果:", result)
    except Exception as error:
        print("ERROR: OCR识别失败:", str(error))


if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else "test.jpg"
    run_ocr_on_image(image_path)
