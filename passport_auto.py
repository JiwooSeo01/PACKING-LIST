from PIL import Image, ImageDraw, ImageFont
import random
import string
import os
from pathlib import Path

# ===== 설정 =====
TEMPLATE_PATH = "passport_template.jpg"
OUTPUT_DIR = "output"
NUM_IMAGES = 10

# MRZ 영역 좌표 (기존 좌표 유지)
MRZ_BOX = (300, 1091, 1001, 1158)

# 폰트 설정 (OCR-B.ttf 파일이 같은 폴더에 있어야 함)
FONT_PATH = "OCR-B.ttf"
FONT_SIZE = 25  # 인식률을 위해 크기를 살짝 키움

# ===== MRZ 체크섬 계산 함수 (필수) =====
def get_check_digit(data):
    weight = [7, 3, 1]
    total = 0
    for i, char in enumerate(data):
        if '0' <= char <= '9':
            val = int(char)
        elif 'A' <= char <= 'Z':
            val = ord(char) - 55
        else:
            val = 0
        total += val * weight[i % 3]
    return str(total % 10)

def pad(text, length=44):
    return text[:length].ljust(length, "<")

# ===== MRZ 데이터 생성 (체크섬 포함) =====
def generate_mrz_with_check():
    countries = ["KAZ", "KGZ", "UZB", "KOR", "USA"]
    country = random.choice(countries)
    surname = random.choice(["IVANOV", "KIM", "LEE", "SMITH", "SAIDOV"])
    name = random.choice(["SERGEI", "ALTYN", "MINJUN", "JOHN", "BAKHTIYOR"])

    # Line 1
    line1 = pad(f"P<{country}{surname}<<{name}")

    # Line 2: 여권번호 + 체크섬 + 국적 + 생일 + 체크섬 + 성별 + 만료일 + 체크섬
    pno = random.choice(string.ascii_uppercase) + ''.join(random.choices(string.digits, k=8))
    pno_check = get_check_digit(pno)
    
    birth = f"{random.randint(70, 99):02}{random.randint(1, 12):02}{random.randint(1, 28):02}"
    birth_check = get_check_digit(birth)
    
    expiry = f"{random.randint(25, 35):02}{random.randint(1, 12):02}{random.randint(1, 28):02}"
    expiry_check = get_check_digit(expiry)
    
    sex = random.choice(["M", "F"])

    line2 = pad(f"{pno}{pno_check}{country}{birth}{birth_check}{sex}{expiry}{expiry_check}")

    return line1, line2

# ===== 이미지에 MRZ 그리기 (에러 수정됨) =====
def draw_mrz(image, mrz_box, mrz_lines, font_path, font_size):
    draw = ImageDraw.Draw(image)
    x1, y1, x2, y2 = mrz_box

    # 배경 지우기
    draw.rectangle(mrz_box, fill="white")

    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    # --- 핵심: 자간 강제 조절 ---
    # MRZ 표준은 한 줄에 정확히 44글자입니다.
    # 전체 너비를 44로 나누어 한 글자가 차지할 '칸'을 계산합니다.
    char_width = (x2 - x1) / 44 
    line_height = (y2 - y1) / 2

    for row_idx, line in enumerate(mrz_lines):
        for col_idx, char in enumerate(line):
            # 각 글자의 시작 X 좌표를 수동으로 계산 (이게 '고정 폭'을 만듭니다)
            char_x = x1 + (col_idx * char_width)
            char_y = y1 + (row_idx * line_height)
            
            # 한 글자씩 그리기
            draw.text((char_x, char_y), char, font=font, fill="black")

    return image

# ===== 메인 실행부 =====
def main():
    if not os.path.exists(TEMPLATE_PATH):
        print(f"❌ 템플릿 파일({TEMPLATE_PATH})이 없습니다!")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i in range(NUM_IMAGES):
        # 이미지 열기
        img = Image.open(TEMPLATE_PATH).convert("RGB")

        # MRZ 데이터 생성 (체크섬 포함)
        mrz_lines = generate_mrz_with_check()

        # MRZ 그리기 (인자 5개 정확히 전달)
        img = draw_mrz(img, MRZ_BOX, mrz_lines, FONT_PATH, FONT_SIZE)

        # 저장
        output_path = os.path.join(OUTPUT_DIR, f"passport_{i}.jpg")
        img.save(output_path, quality=95) # 화질 유지

        print(f"✅ 생성 완료: {output_path}")

if __name__ == "__main__":
    main()