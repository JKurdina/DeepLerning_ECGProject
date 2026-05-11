"""
Сравнивает результаты пайплайна с эталонными значениями из results/.

"""

import glob
import json
import sys
import os

ETALON_DIR = "results"
OUTPUTS_DIR = "outputs"
TOLERANCE = 0.1


def load_json(path):
    with open(path) as f:
        return json.load(f)


def find_output_csv(model_prefix, task):
    """Ищет CSV файл в outputs/, игнорируя дату в имени."""
    pattern = os.path.join(OUTPUTS_DIR, f"{model_prefix}_*_{task}_probabilities.csv")
    files = glob.glob(pattern)
    return files[0] if files else None


def csv_to_records(filepath):
    """Читает CSV и возвращает список словарей."""
    import csv
    with open(filepath) as f:
        return list(csv.DictReader(f))


def compare_preprocessing(etalon):
    """Сравнивает ecg_processing_detailed_report."""
    errors = []
    passed = 0

    current_file = os.path.join(OUTPUTS_DIR, "batch_1", "ecg_processing_detailed_report.csv")
    if not os.path.exists(current_file):
        return [f"FAIL  Файл не найден: {current_file}"], 0

    current = csv_to_records(current_file)

    if len(etalon) != len(current):
        errors.append(f"FAIL  preprocessing: строк было {len(etalon)}, стало {len(current)}")
        return errors, passed

    for i, (e, c) in enumerate(zip(etalon, current)):
        for col in ["file_id", "status", "message"]:
            e_val = e.get(col, "")
            c_val = c.get(col, "")
            if e_val != c_val:
                errors.append(
                    f"FAIL  preprocessing | строка {i} | '{col}': "
                    f"ожидалось '{e_val}', получено '{c_val}'"
                )
            else:
                passed += 1

    return errors, passed


def compare_probabilities(etalon, model_prefix, task):
    """Сравнивает probabilities CSV с эталонным JSON."""
    errors = []
    passed = 0

    current_file = find_output_csv(model_prefix, task)
    if current_file is None:
        return [f"FAIL  Файл не найден для модели '{model_prefix}' (задача: {task})"], 0

    current = csv_to_records(current_file)

    if len(etalon) != len(current):
        errors.append(
            f"FAIL  {model_prefix}: строк было {len(etalon)}, стало {len(current)}"
        )
        return errors, passed

    for i, (e_row, c_row) in enumerate(zip(etalon, current)):
        for col, e_val in e_row.items():
            if col not in c_row:
                errors.append(f"FAIL  {model_prefix} | колонка '{col}' отсутствует")
                continue

            c_val = c_row[col]

            try:
                e_num = float(e_val)
                c_num = float(c_val)
                diff = abs(e_num - c_num)
                if diff > TOLERANCE:
                    errors.append(
                        f"FAIL  {model_prefix} | строка {i} | '{col}': "
                        f"ожидалось {e_num:.6f}, получено {c_num:.6f} "
                        f"(отклонение {diff:.6f} > {TOLERANCE})"
                    )
                else:
                    passed += 1
            except (ValueError, TypeError):
                if str(e_val) != str(c_val):
                    errors.append(
                        f"FAIL  {model_prefix} | строка {i} | '{col}': "
                        f"ожидалось '{e_val}', получено '{c_val}'"
                    )
                else:
                    passed += 1

    return errors, passed


def main():
    print("=" * 60)
    print("DeepECG — сравнение результатов с эталоном")
    print("=" * 60)

    all_errors = []
    total_passed = 0

    # 1. Препроцессинг
    print("\n[1/3] Проверка препроцессинга...")
    etalon_preprocessing = load_json(
        os.path.join(ETALON_DIR, "ecg_processing_detailed_report.json")
    )
    errors, passed = compare_preprocessing(etalon_preprocessing)
    total_passed += passed
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(" ", e)
    else:
        print("  OK  ecg_processing_detailed_report")

    # 2. Вероятности wcr_77_classes
    print("\n[2/3] Проверка вероятностей wcr_77_classes...")
    etalon_probs = load_json(
        os.path.join(ETALON_DIR, "wcr_77_classes_ecg_machine_diagnosis_probabilities.json")
    )
    errors, passed = compare_probabilities(
        etalon_probs, "wcr_77_classes", "ecg_machine_diagnosis"
    )
    total_passed += passed
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(" ", e)
    else:
        print("  OK  wcr_77_classes_ecg_machine_diagnosis_probabilities")

    # 3. Вероятности wcr_lvef_equal_under_40
    print("\n[3/3] Проверка вероятностей wcr_lvef_equal_under_40...")
    etalon_lvef = load_json(
        os.path.join(ETALON_DIR, "wcr_lvef_equal_under_40_lvef_40_probabilities.json")
    )
    errors, passed = compare_probabilities(
        etalon_lvef, "wcr_lvef_equal_under_40", "lvef_40"
    )
    total_passed += passed
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(" ", e)
    else:
        print("  OK  wcr_lvef_equal_under_40_lvef_40_probabilities")

    # Итог
    print()
    print("=" * 60)
    if all_errors:
        print(f"РЕЗУЛЬТАТ: {len(all_errors)} ошибок, {total_passed} проверок прошло")
        sys.exit(1)
    else:
        print(f"РЕЗУЛЬТАТ: все проверки прошли успешно ({total_passed} проверок)")
        sys.exit(0)


if __name__ == "__main__":
    main()