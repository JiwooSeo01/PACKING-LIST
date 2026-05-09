import easyocr
from pathlib import Path
import csv

def force_extract_text(reader, image_path):
    try:
        # detail=0으로 텍스트만 추출
        results = reader.readtext(str(image_path), detail=0)
        
        # 1. 너무 짧은 노이즈 제거 (보통 MRZ 한 줄은 40자 내외이므로 20자 이상만 필터링)
        # 공백은 제거하고 대문자로 통일
        clean_lines = [line.replace(" ", "").upper() for line in results if len(line.strip()) > 20]
        
        if len(clean_lines) < 2:
            # 만약 긴 줄이 없다면 전체 결과에서 마지막 두 개라도 시도
            if len(results) >= 2:
                clean_lines = [line.replace(" ", "").upper() for line in results[-2:]]
            else:
                return None

        # 2. 가장 마지막 두 줄을 추출 (여권 하단 MRZ 위치)
        line1 = clean_lines[-2]
        line2 = clean_lines[-1]

        # 3. 간단한 파싱 (MRZ 규칙을 기반으로 하되 오류 무시)
        # 성(Surname)은 보통 첫 번째 줄 'P<KOR' 다음 '성<<이름' 구조임
        surname = "Unknown"
        if "<<" in line1:
            parts = line1.split("<<")
            # P<KAZSAIDOV 등에서 성만 추출
            first_part = parts[0]
            if "<" in first_part:
                surname = first_part.split("<")[-1]

        # 여권 번호는 보통 두 번째 줄 맨 앞 9자리
        passport_no = line2[:9] if len(line2) > 9 else line2

        return {
            "file_name": image_path.name,
            "passport_no": passport_no,
            "surname": surname,
            "full_line1": line1,
            "full_line2": line2
        }
    except Exception as e:
        print(f"❌ {image_path.name} 에러: {e}")
        return None

def main():
    print("⏳ EasyOCR 엔진 가동 중... (GPU가 없으면 조금 느릴 수 있습니다)")
    reader = easyocr.Reader(['en'], gpu=False) # 'pin_memory' 경고 방지를 위해 gpu=False 설정

    input_dir = Path("output")
    packing_list = []

    img_files = list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.png"))
    print(f"🔍 {len(img_files)}개의 파일을 강제 스캔합니다...")

    for img_p in img_files:
        data = force_extract_text(reader, img_p)
        if data:
            packing_list.append(data)
            print(f"✅ {img_p.name} -> 번호: {data['passport_no']}, 성: {data['surname']}")
        else:
            print(f"⚠️ {img_p.name} 인식 실패 (텍스트 부족)")

    if packing_list:
        with open("packing_list_force.csv", "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=packing_list[0].keys())
            writer.writeheader()
            writer.writerows(packing_list)
        print(f"\n✨ 완료! 'packing_list_force.csv'를 확인하세요.")

if __name__ == "__main__":
    main()