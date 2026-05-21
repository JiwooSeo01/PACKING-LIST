import easyocr
from pathlib import Path
import csv


def force_extract_text(reader, image_path):
    try:
        # OCR 결과 (텍스트만)
        results = reader.readtext(str(image_path), detail=0)

        # MRZ 후보 정리 (너무 짧은 노이즈 제거)
        clean_lines = [
            line.replace(" ", "").upper()
            for line in results
            if len(line.strip()) > 20
        ]

        # MRZ가 제대로 안 잡히면 fallback
        if len(clean_lines) < 2:
            if len(results) >= 2:
                clean_lines = [line.replace(" ", "").upper() for line in results[-2:]]
            else:
                return None

        # MRZ는 보통 마지막 2줄
        line1 = clean_lines[-2]
        line2 = clean_lines[-1]

        # -----------------------------
        # MRZ 파싱 (성 + 이름)
        # -----------------------------
        surname = "Unknown"
        given_names = "Unknown"

        if "<<" in line1:
            parts = line1.split("<<")

            left_part = parts[0]   # P<KORSMITH
            right_part = parts[1] if len(parts) > 1 else ""

            # 성 추출
            if "<" in left_part:
                surname = left_part.split("<")[-1]

            # 이름 추출 (<< 이후)
            given_names = right_part.replace("<", " ").strip()

        # -----------------------------
        # 여권번호 (보통 MRZ 2번째 줄 앞부분)
        # -----------------------------
        passport_no = line2[:9] if len(line2) >= 9 else line2

        return {
            "file_name": image_path.name,
            "passport_no": passport_no,
            "surname": surname,
            "given_names": given_names,
            "full_line1": line1,
            "full_line2": line2
        }

    except Exception as e:
        print(f"❌ {image_path.name} 에러: {e}")
        return None


def main():
    print("⏳ EasyOCR 엔진 가동 중...")

    reader = easyocr.Reader(['en'], gpu=False)

    input_dir = Path("output")
    packing_list = []

    img_files = list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.png"))

    print(f"🔍 {len(img_files)}개의 파일을 스캔합니다...")

    for img_p in img_files:
        data = force_extract_text(reader, img_p)

        if data:
            packing_list.append(data)
            print(
                f"✅ {img_p.name} -> "
                f"번호: {data['passport_no']}, "
                f"성: {data['surname']}, "
                f"이름: {data['given_names']}"
            )
        else:
            print(f"⚠️ {img_p.name} 인식 실패")

    if packing_list:
        with open("packing_list_force.csv", "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=packing_list[0].keys())
            writer.writeheader()
            writer.writerows(packing_list)

        print("\n✨ 완료! packing_list_force.csv 생성됨")


if __name__ == "__main__":
    main()