from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, ImageEnhance, ImageFilter

DYNAMSOFT_LICENSE = "t0161pgQAAEFKWsS7IqQP6ieXvOn2SyN6FFx4I25qvuTdN0c54kYSWf+QghDhs4K9jwE7NAoaBUEtSuETaibcolM557i0SIGAshIQ0uwTcXdD8vw29bjXGWWZ62J8BemaeoBpf5q0Zqlp3NT3ll+eN33qukk7XVMPMG1/s+1zzLRQRXp9Tt9x2NQDTNvf7Pb5k8mynUqL0aofQojeOy72APwP9r0=;t0159pgQAAISN9wbASt0mDQZpZA7pMrFxPeplJ6/Wd8b7K3UPXJKmmEUsIVdIxURsnASjeGgtbHcRSLx5lfhOiSLhLPodj0AgQCybDw/zVjBsX1OOWc9Im7Fk4yeIpikDTL1oojZTTf2m2XfZ/L7qU45N1NM0ZYCp95t1n32muiLS6jPeY7cpA0y932z2+ZeZ05hTi16LH4Lz1hpM+gEpOfbO"


def _default_vin_result() -> Dict[str, Any]:
    return {
        "vin_string": "",
        "wmi": "",
        "region": "",
        "vds": "",
        "vis": "",
        "model_year": "",
        "plant_code": "",
        "status": "OK",
        "error": "",
    }


def normalize_vin(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def is_valid_vin(value: str) -> bool:
    value = normalize_vin(value)
    if len(value) != 17:
        return False
    if any(ch in value for ch in ["I", "O", "Q"]):
        return False
    return True


def build_variants(image_path: Path) -> List[Path]:
    img = Image.open(image_path).convert("RGB")
    out_paths = [image_path]

    work_dir = image_path.parent

    # grayscale + contrast
    gray = img.convert("L")
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    p1 = work_dir / f"{image_path.stem}_gray.jpg"
    gray.save(p1, quality=95)
    out_paths.append(p1)

    # sharpen
    sharp = img.filter(ImageFilter.SHARPEN)
    sharp = ImageEnhance.Contrast(sharp).enhance(1.8)
    p2 = work_dir / f"{image_path.stem}_sharp.jpg"
    sharp.save(p2, quality=95)
    out_paths.append(p2)

    # upscale
    big = img.resize((img.width * 2, img.height * 2))
    p3 = work_dir / f"{image_path.stem}_big.jpg"
    big.save(p3, quality=95)
    out_paths.append(p3)

    # rotate
    for angle in [-10, -5, 5, 10]:
        rot = img.rotate(angle, expand=True)
        p = work_dir / f"{image_path.stem}_rot_{angle}.jpg"
        rot.save(p, quality=95)
        out_paths.append(p)

    return out_paths


def extract_vin_info(image_path: Path) -> Dict[str, Any]:
    result = _default_vin_result()

    try:
        from dynamsoft_capture_vision_bundle import (
            CaptureVisionRouter,
            EnumErrorCode,
            EnumValidationStatus,
            LicenseManager,
        )

        error_code, error_message = LicenseManager.init_license(DYNAMSOFT_LICENSE)
        if error_code not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_WARNING):
            result["status"] = "ERROR"
            result["error"] = f"License init failed: {error_message}"
            return result

        cvr = CaptureVisionRouter()
        templates = ["ReadVINText", "ReadVINBarcode"]

        image_variants = build_variants(image_path)
        last_error = "VIN not found"

        for variant_path in image_variants:
            for template_name in templates:
                result_array = cvr.capture_multi_pages(str(variant_path), template_name)
                results = result_array.get_results()

                if not results:
                    continue

                for capture_result in results:
                    parsed_result = capture_result.get_parsed_result()
                    if parsed_result is None:
                        continue

                    items = parsed_result.get_items()
                    if not items:
                        continue

                    for item in items:
                        if item.get_code_type() != "VIN":
                            continue

                        raw_vin = item.get_field_value("vinString")
                        if raw_vin:
                            candidate = normalize_vin(raw_vin)
                            if is_valid_vin(candidate):
                                result["vin_string"] = candidate

                        if item.get_field_value("WMI") and item.get_field_validation_status("WMI") != EnumValidationStatus.VS_FAILED:
                            result["wmi"] = item.get_field_value("WMI")
                        if item.get_field_value("region") and item.get_field_validation_status("region") != EnumValidationStatus.VS_FAILED:
                            result["region"] = item.get_field_value("region")
                        if item.get_field_value("VDS") and item.get_field_validation_status("VDS") != EnumValidationStatus.VS_FAILED:
                            result["vds"] = item.get_field_value("VDS")
                        if item.get_field_value("VIS") and item.get_field_validation_status("VIS") != EnumValidationStatus.VS_FAILED:
                            result["vis"] = item.get_field_value("VIS")
                        if item.get_field_value("modelYear") and item.get_field_validation_status("modelYear") != EnumValidationStatus.VS_FAILED:
                            result["model_year"] = item.get_field_value("modelYear")
                        if item.get_field_value("plantCode") and item.get_field_validation_status("plantCode") != EnumValidationStatus.VS_FAILED:
                            result["plant_code"] = item.get_field_value("plantCode")

                        if result["vin_string"]:
                            return result

                last_error = f"VIN not found using {template_name} on {variant_path.name}"

        result["status"] = "ERROR"
        result["error"] = last_error
        return result

    except Exception as exc:
        result["status"] = "ERROR"
        result["error"] = f"VIN parser error: {exc}"
        return result