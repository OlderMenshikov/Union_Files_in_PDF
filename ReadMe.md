# Merge PDF & Images / Объединение PDF и Изображений

[English](#english) | [Русский](#русский)

---

<a name="english"></a>
## English

**Merge PDF** is a Python-based desktop application (GUI built with Tkinter) designed to effortlessly merge multiple PDF documents and images into a single PDF file. It includes features like automatic proportional image scaling to A4 size and the generation of an interactive Table of Contents.

### Features
* **Merge Files**: Combine PDF documents and images (PNG, JPG, JPEG, BMP) into one file.
* **Interactive Table of Contents**: Automatically generates a clickable table of contents with dot leaders. You can also turn this feature off if you prefer a direct merge.
* **Image Scaling**: Images are proportionally scaled to fit perfectly onto A4-sized PDF pages without distortion.
* **Multilingual UI**: The application interface supports 6 languages: Russian, Ukrainian, German, Italian, French, and Polish.
* **Easy Management**: Add, remove, and reorder files directly within the application's listbox.
* **Automatic Open**: The application remembers your last successfully merged PDF and will automatically open it in your default PDF viewer once you close the program.

### Latest Changes
* **Auto-Open Feature**: The final generated PDF file will now automatically open in your default system viewer after the application is closed.
* **UI Clean-up**: Removed the "Contact developer" section from the App Information window for a cleaner look.
* **Info Window Restructure**: Section "Features" was re-numbered correctly across all available translations.

### Requirements
* Python 3.x
* `PyPDF2`
* `reportlab`
* `Pillow`

### How to Run
Use the provided `Merge_PDF.bat` to launch the application on Windows, or simply run:
```bash
python Merge_PDF.py
```

---

<a name="русский"></a>
## Русский

**Объединение PDF и Изображений** — это десктопное приложение на Python (с графическим интерфейсом на Tkinter), предназначенное для удобного объединения нескольких PDF-документов и изображений в один PDF-файл. Приложение поддерживает автоматическое пропорциональное масштабирование изображений под формат А4 и создание интерактивного оглавления.

### Возможности
* **Объединение файлов**: Комбинируйте PDF-документы и картинки (PNG, JPG, JPEG, BMP) в один файл.
* **Интерактивное оглавление**: Автоматически генерирует кликабельное оглавление с точками-заполнителями. Оглавление можно отключить при необходимости.
* **Масштабирование картинок**: Изображения пропорционально вписываются в PDF-страницы формата A4 без искажений.
* **Мультиязычность**: Интерфейс приложения поддерживает 6 языков: русский, украинский, немецкий, итальянский, французский и польский.
* **Удобное управление**: Добавляйте, удаляйте и меняйте порядок файлов прямо в списке приложения.
* **Автоматическое открытие**: Программа запоминает последний успешно объединённый PDF-файл и автоматически открывает его в программе по умолчанию при закрытии приложения.

### Последние изменения
* **Функция авто-открытия**: Теперь итоговый созданный PDF-файл автоматически открывается в вашей программе для просмотра по умолчанию после закрытия приложения.
* **Очистка интерфейса**: Из окна информации о приложении был удален раздел "Написать разработчику" для более лаконичного вида.
* **Обновление окна "Инфо"**: Раздел "Возможности" был корректно перенумерован во всех доступных переводах.

### Требования
* Python 3.x
* `PyPDF2`
* `reportlab`
* `Pillow`

### Как запустить
Используйте прилагаемый файл `Merge_PDF.bat` для запуска в Windows, или просто выполните команду:
```bash
python Merge_PDF.py
```
