# DeepECG Docker

Анализ ЭКГ сигналов с использованием deep learning моделей. Поддерживает классификацию по 77 диагнозам, а также бинарную классификацию риска мерцательной аритмии (AFIB) и сниженной фракции выброса левого желудочка (LVEF).

## Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)
- HuggingFace API key

---

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/JKurdina/DeepLerning_ECGProject.git
cd DeepLerning_ECGProject
```

### 2. Настройка HuggingFace API ключа

Зарегистрироваться на HuggingFace

Вставить ключ в файл `api_key.json`:

```json
{
  "HUGGING_FACE_API_KEY": "hf_xxxxxxxxxxxxxxxxx"
}
```

### 3. Сборка Docker образа

```bash
docker build -t deepecg-docker .
```

> **Как проверить сборку локально без другого компьютера:** после сборки запустите тест внутри образа без каких-либо volume-монтирований. Если тест проходит — образ самодостаточен:
>
> ```bash
> docker run --rm deepecg-docker python tests/test_error_collector.py
> ```

### 4. Запуск контейнера

**Git Bash / macOS / Linux:**

```bash
MSYS_NO_PATHCONV=1 docker run -d --name deepecg \
  -v $(pwd)/inputs:/app/inputs \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/ecg_signals:/app/ecg_signals:ro \
  -v $(pwd)/preprocessing:/app/preprocessing \
  -v $(pwd)/thresholds:/app/thresholds \
  -v $(pwd)/weights:/app/weights \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/tests:/app/tests \
  deepecg-docker
```

**Windows CMD:**

```cmd
docker run -d --name deepecg -v %cd%/inputs:/app/inputs -v %cd%/outputs:/app/outputs -v %cd%/ecg_signals:/app/ecg_signals:ro -v %cd%/preprocessing:/app/preprocessing -v %cd%/thresholds:/app/thresholds -v %cd%/weights:/app/weights -v %cd%/results:/app/results -v %cd%/tests:/app/tests deepecg-docker
```

### 5. Подключение к контейнеру

```bash
docker exec -it deepecg bash
```

### 6. Запуск пайплайна

```bash
bash run_pipeline.bash --mode full_run --csv_file_name data_rows_template_npy.csv
```

---

## 7. Проверка результатов

В репозитории есть эталонные результаты в папке `results/` и скрипт сравнения `tests/compare_results.py`.

### Запуск проверки

```bash
python tests/compare_results.py
```

### Ожидаемый вывод

```
============================================================
DeepECG — сравнение результатов с эталоном
============================================================

[1/3] Проверка препроцессинга...
  OK  ecg_processing_detailed_report

[2/3] Проверка вероятностей wcr_77_classes...
  OK  wcr_77_classes_ecg_machine_diagnosis_probabilities

[3/3] Проверка вероятностей wcr_lvef_equal_under_40...
  OK  wcr_lvef_equal_under_40_lvef_40_probabilities

============================================================
РЕЗУЛЬТАТ: все проверки прошли успешно (158 проверок)
```

> Допустимое отклонение вероятностей между запусками: ±0.01

---

## Результаты

После завершения пайплайна результаты появятся в папке `outputs/`.

| Файл | Описание |
|---|---|
| `batch_1/ecg_processing_detailed_report.csv` | Статус обработки каждого ECG файла |
| `batch_1/ecg_processing_summary_report.csv` | Общая статистика препроцессинга |
| `{model}_probabilities.csv` | Вероятности предсказаний для каждого ECG |
| `{model}.csv` / `{model}.json` | Метрики качества (AUC, F1) |

### Модели и задачи

| Модель | Задача |
|---|---|
| `wcr_77_classes`, `efficientnetv2_77_classes` | 77 диагнозов ЭКГ |
| `wcr_afib_5y`, `efficientnetv2_afib_5y` | Риск мерцательной аритмии за 5 лет |
| `wcr_lvef_under_50`, `efficientnetv2_lvef_under_50` | Фракция выброса < 50% |
| `wcr_lvef_equal_under_40`, `efficientnetv2_lvef_equal_under_40` | Фракция выброса ≤ 40% |

### Как не скачивать все модели

Модели загружаются с HuggingFace при первом запуске пайплайна, а не при сборке образа. Чтобы ограничить набор загружаемых моделей, отредактируйте `heartwise.config` перед запуском:

```
use_wcr: True          # WCR-семейство (трансформер)
use_efficientnet: False # EfficientNetV2-семейство — отключить
```

Установите `False` для семейства, которое не нужно, — соответствующие модели не будут загружаться.

**Запуск только юнит-тестов (модели не нужны):**

```bash
# Прямо в образе, без volume-монтирований, без API-ключа
docker run --rm deepecg-docker python tests/test_error_collector.py
```

---

## Остановка контейнера

```bash
docker stop deepecg
docker rm deepecg
```

---
