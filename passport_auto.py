from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random
import string
import os
import numpy as np
import cv2

# ======================
# 설정
# ======================
TEMPLATE_PATH = "passport_template.jpg"
OUTPUT_DIR = "passports"
NUM_IMAGES = 10

MRZ_BOX = (300, 1091, 1001, 1158)

FONT_PATH = "OCR-B.ttf"
FONT_SIZE = 21


# ======================
# MRZ 체크섬
# ======================
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


# ======================
# MRZ 생성
# ======================
def generate_mrz_with_check():
    countries = ["KAZ", "KGZ", "UZB", "KOR", "USA"]

    country = random.choice(countries)
    surname = random.choice(["IVANOV", "KIM", "LEE", "SMITH", "SAIDOV"])
    name = random.choice(["SERGEI", "ALTYN", "MINJUN", "JOHN", "BAKHTIYOR"])

    line1 = pad(f"P<{country}{surname}<<{name}")

    pno = random.choice(string.ascii_uppercase) + ''.join(random.choices(string.digits, k=8))
    pno_check = get_check_digit(pno)

    birth = f"{random.randint(70, 99):02}{random.randint(1, 12):02}{random.randint(1, 28):02}"
    birth_check = get_check_digit(birth)

    expiry = f"{random.randint(25, 35):02}{random.randint(1, 12):02}{random.randint(1, 28):02}"
    expiry_check = get_check_digit(expiry)

    sex = random.choice(["M", "F"])

    line2 = pad(f"{pno}{pno_check}{country}{birth}{birth_check}{sex}{expiry}{expiry_check}")

    return line1, line2


# ======================
# MRZ 렌더링
# ======================
def draw_mrz(image, mrz_box, mrz_lines, font_path, font_size):
    draw = ImageDraw.Draw(image)

    x1, y1, x2, y2 = mrz_box

    draw.rectangle(mrz_box, fill="white")

    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    total_width = x2 - x1
    char_width = total_width / 44
    line_height = (y2 - y1) / 2

    for r, line in enumerate(mrz_lines):
        for c, ch in enumerate(line):
            draw.text(
                (x1 + c * char_width, y1 + r * line_height - 2),
                ch,
                font=font,
                fill="black"
            )

    return image


# ======================
# 🔥 AUGMENTATION (강화 버전)
# ======================

def random_perspective(image, strength=0.1):
    img = np.array(image)
    h, w = img.shape[:2]

    src = np.float32([[0,0],[w,0],[w,h],[0,h]])

    dx, dy = w * strength, h * strength

    dst = np.float32([
        [random.uniform(0, dx), random.uniform(0, dy)],
        [w - random.uniform(0, dx), random.uniform(0, dy)],
        [w - random.uniform(0, dx), h - random.uniform(0, dy)],
        [random.uniform(0, dx), h - random.uniform(0, dy)]
    ])

    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, matrix, (w, h), borderValue=(255,255,255))

    return Image.fromarray(warped)


def random_warp(image, intensity=4):
    img = np.array(image)
    h, w = img.shape[:2]

    map_x, map_y = np.meshgrid(np.arange(w), np.arange(h))

    dx = np.sin(map_y / 30.0) * random.uniform(-intensity, intensity)
    dy = np.cos(map_x / 40.0) * random.uniform(-intensity, intensity)

    map_x = (map_x + dx).astype(np.float32)
    map_y = (map_y + dy).astype(np.float32)

    warped = cv2.remap(
        img,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255,255,255)
    )

    return Image.fromarray(warped)


def uneven_light(image):
    img = np.array(image).astype(np.float32)
    h, w = img.shape[:2]

    x_grad = np.tile(np.linspace(0.7, 1.3, w), (h, 1))
    y_grad = np.tile(np.linspace(1.2, 0.8, h), (w, 1)).T

    mask = (x_grad * y_grad)[:, :, None]

    img *= mask
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def motion_blur(image, size=7):
    img = np.array(image)

    kernel = np.zeros((size, size))
    kernel[size // 2, :] = 1
    kernel = kernel / size

    blurred = cv2.filter2D(img, -1, kernel)
    return Image.fromarray(blurred)


def random_blur(image, p=0.6):
    if random.random() < p:
        return image.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 1.2)))
    return image


def random_light(image):
    image = ImageEnhance.Brightness(image).enhance(random.uniform(0.85, 1.15))
    image = ImageEnhance.Contrast(image).enhance(random.uniform(0.85, 1.2))
    return image


def random_noise(image):
    img = np.array(image)
    noise = np.random.normal(0, random.randint(5, 25), img.shape)
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(img)


# ======================
# MAIN
# ======================
def main():
    if not os.path.exists(TEMPLATE_PATH):
        print("❌ template 없음")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i in range(NUM_IMAGES):
        img = Image.open(TEMPLATE_PATH).convert("RGB")

        mrz_lines = generate_mrz_with_check()
        img = draw_mrz(img, MRZ_BOX, mrz_lines, FONT_PATH, FONT_SIZE)

        # ===== 🔥 강한 현실 환경 =====
        img = random_perspective(img, 0.1)
        # img = random_warp(img, 4)
        img = uneven_light(img)
        img = motion_blur(img, 5)

        # ===== 기본 노이즈 =====
        img = random_blur(img, 0.6)
        img = random_light(img)
        img = random_noise(img)

        output_path = os.path.join(OUTPUT_DIR, f"passport_{i}.jpg")
        img.save(output_path, quality=95)

        print(f"✅ 생성: {output_path}")


if __name__ == "__main__":
    main()