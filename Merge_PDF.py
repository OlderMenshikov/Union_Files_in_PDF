import sys
import os
import webbrowser
from PyPDF2 import PdfWriter, PdfReader
from PyPDF2.generic import AnnotationBuilder
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image


def setup_fonts():
    """
    Настройка шрифтов с поддержкой кириллицы (русских букв).
    Использует системный Arial на Windows, либо fallback на Helvetica.
    """
    font_name = "Helvetica"
    font_bold = "Helvetica-Bold"

    windows_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    arial_path = os.path.join(windows_fonts, "arial.ttf")
    arial_bold_path = os.path.join(windows_fonts, "arialbd.ttf")

    if os.path.exists(arial_path):
        try:
            pdfmetrics.registerFont(TTFont("Arial", arial_path))
            font_name = "Arial"
            if os.path.exists(arial_bold_path):
                pdfmetrics.registerFont(TTFont("Arial-Bold", arial_bold_path))
                font_bold = "Arial-Bold"
            else:
                font_bold = "Arial"
        except Exception:
            pass

    return font_name, font_bold


FONT_REGULAR, FONT_BOLD = setup_fonts()


def convert_images_to_pdf(image_files):
    """
    Конвертирует изображения в валидные PDF страницы формата A4 с пропорциональным масштабированием.
    Гарантирует полноценную запись файла без пустых или битых страниц.
    """
    temp_pdfs = []
    for img_file in image_files:
        if not os.path.exists(img_file):
            print(f"Предупреждение: Файл {img_file} не найден!")
            continue
        try:
            pdf_name = f"{os.path.splitext(img_file)[0]}_temp.pdf"
            
            # Получаем размеры исходного изображения и закрываем хэндл
            with Image.open(img_file) as img_obj:
                img_w, img_h = img_obj.size

            # Рендерим страницу A4 через ReportLab
            c = canvas.Canvas(pdf_name, pagesize=A4)
            a4_w, a4_h = A4
            
            # Масштабируем изображение так, чтобы оно помещалось на страницу A4 без искажений
            ratio = min(a4_w / img_w, a4_h / img_h)
            draw_w = img_w * ratio
            draw_h = img_h * ratio
            x = (a4_w - draw_w) / 2
            y = (a4_h - draw_h) / 2

            c.drawImage(img_file, x, y, width=draw_w, height=draw_h)
            c.showPage()
            c.save()
            
            temp_pdfs.append(pdf_name)
        except Exception as e:
            print(f"Ошибка конвертации изображения {img_file}: {e}")
    return temp_pdfs


def calculate_page_counts(pdf_files):
    """
    Возвращает список кортежей (имя_файла, количество_страниц).
    """
    file_info = []
    for file in pdf_files:
        try:
            reader = PdfReader(file)
            pages = len(reader.pages)
            if pages > 0:
                file_info.append((os.path.basename(file), pages))
        except Exception as e:
            print(f"Ошибка при чтении {file}: {e}")
    return file_info


def build_toc_pdf(entries, output_toc="toc.pdf", toc_title="Оглавление"):
    """
    Рендерит страницу(ы) оглавления с точками-заполнителями между названием и номером страницы.
    Возвращает список кортежей с координатами интерактивных ссылок: (toc_page_index, rect, target_page_index)
    """
    c = canvas.Canvas(output_toc, pagesize=A4)

    # Заголовок оглавления стильного сине-фиолетового цвета
    c.setFillColorRGB(0.3, 0.4, 0.7)
    c.setFont(FONT_BOLD, 20)
    c.drawString(50, 800, toc_title)

    c.setFillColorRGB(0, 0, 0)
    c.setFont(FONT_REGULAR, 11)

    y = 760
    margin_left = 50
    margin_right = 545
    toc_page_idx = 0
    link_rects = []

    for title, display_page, target_idx in entries:
        page_str = str(display_page)
        page_w = c.stringWidth(page_str, FONT_REGULAR, 11)
        x_page = margin_right - page_w

        title_w = c.stringWidth(title, FONT_REGULAR, 11)
        x_title_end = margin_left + title_w

        x_dots_start = x_title_end + 4
        x_dots_end = x_page - 4
        gap = x_dots_end - x_dots_start
        dot_w = c.stringWidth(".", FONT_REGULAR, 11)

        # Рисуем точки-заполнители между текстом и номером страницы
        if gap > dot_w:
            num_dots = int(gap // dot_w)
            dots_text = "." * num_dots
            c.drawString(x_dots_start, y, dots_text)

        c.drawString(margin_left, y, title)
        c.drawString(x_page, y, page_str)

        # Прямоугольная область для клика (вся строка оглавления)
        rect = (margin_left - 2, y - 2, margin_right + 2, y + 12)
        link_rects.append((toc_page_idx, rect, target_idx))

        y -= 20
        if y < 50:
            c.showPage()
            y = 760
            toc_page_idx += 1
            c.setFillColorRGB(0, 0, 0)
            c.setFont(FONT_REGULAR, 11)

    c.save()
    return link_rects


def create_toc(pdf_files, output_toc="toc.pdf", toc_title="Оглавление"):
    """
    Создаёт оглавление с точным расчётом страниц и координатами кликабельных ссылок.
    """
    file_info = calculate_page_counts(pdf_files)

    # Проход 1: предварительный рендеринг для определения числа страниц оглавления
    dummy_entries = [(title, 1, 0) for title, _ in file_info]
    build_toc_pdf(dummy_entries, output_toc, toc_title=toc_title)
    toc_pages_count = len(PdfReader(output_toc).pages)

    # Проход 2: точный расчёт отображаемых номеров страниц и целевых индексов
    entries = []
    current_display_page = toc_pages_count + 1
    current_target_index = toc_pages_count
    for title, pages in file_info:
        entries.append((title, current_display_page, current_target_index))
        current_display_page += pages
        current_target_index += pages

    # Проход 3: рендеринг финального оглавления и получение прямоугольников ссылок
    link_rects = build_toc_pdf(entries, output_toc, toc_title=toc_title)
    return output_toc, entries, link_rects


def merge_pdfs(pdf_files, output_filename="final_project.pdf", make_toc=True, cleanup_temp=True, toc_title="Оглавление"):
    """
    Объединяет PDF и изображения в один файл.
    Если make_toc=True (по умолчанию), формирует страницу(ы) интерактивного оглавления с ссылками.
    Если make_toc=False, объединяет документы напрямую без добавления страницы оглавления.
    """
    if not pdf_files:
        raise ValueError("Нет PDF-файлов для объединения!")

    writer = PdfWriter()

    if make_toc:
        # 1. Создаём оглавление и получаем координаты кликабельных областей
        toc_file, entries, link_rects = create_toc(pdf_files, toc_title=toc_title)

        # 2. Добавляем страницы оглавления
        toc_reader = PdfReader(toc_file)
        for page in toc_reader.pages:
            writer.add_page(page)

        # 3. Добавляем страницы остальных документов
        for pdf in pdf_files:
            reader = PdfReader(pdf)
            for page in reader.pages:
                writer.add_page(page)

        # 4. Добавляем боковые закладки (outline)
        for title, _, target_idx in entries:
            writer.add_outline_item(title, target_idx)

        # 5. Добавляем интерактивные ссылки прямо на страницы оглавления
        for toc_page_idx, rect, target_idx in link_rects:
            link_annot = AnnotationBuilder.link(rect=rect, target_page_index=target_idx)
            writer.add_annotation(page_number=toc_page_idx, annotation=link_annot)

        if cleanup_temp and os.path.exists(toc_file):
            try:
                os.remove(toc_file)
            except Exception:
                pass
    else:
        # Режим БЕЗ оглавления
        outline_page_index = 0
        for pdf in pdf_files:
            reader = PdfReader(pdf)
            num_pages = len(reader.pages)
            for page in reader.pages:
                writer.add_page(page)
            writer.add_outline_item(os.path.basename(pdf), outline_page_index)
            outline_page_index += num_pages

    with open(output_filename, "wb") as out_f:
        writer.write(out_f)

    print(f"Готово! Итоговый файл: {output_filename}")


def process_files(files, output_name, make_toc=True, toc_title="Оглавление"):
    """
    Вспомогательная функция обработки списка файлов и сохранения итогового PDF.
    """
    if not output_name.lower().endswith(".pdf"):
        output_name += ".pdf"

    image_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))]
    pdf_files = [f for f in files if f.lower().endswith(".pdf")]

    temp_pdfs = convert_images_to_pdf(image_files)
    all_pdfs = pdf_files + temp_pdfs

    try:
        merge_pdfs(all_pdfs, output_name, make_toc=make_toc, cleanup_temp=True, toc_title=toc_title)
    finally:
        for temp_pdf in temp_pdfs:
            if os.path.exists(temp_pdf):
                try:
                    os.remove(temp_pdf)
                except Exception:
                    pass


TRANSLATIONS = {
    "ru": {
        "lang_name": "🌐 Русский",
        "app_title": "Объединение PDF и Изображений",
        "btn_add": "➕ Добавить файлы",
        "btn_up": "⬆ Выше",
        "btn_down": "⬇ Ниже",
        "btn_remove": "❌ Удалить",
        "btn_clear": "🗑 Очистить",
        "btn_info": "ℹ️ Информация о приложении",
        "btn_merge": "🚀 Объединить файлы в PDF",
        "toc_checkbox": "Создавать интерактивное оглавление (по умолчанию включено)",
        "listbox_header": "Выбранные файлы (порядок объединения):",
        "file_dialog_title": "Выберите PDF файлы и изображения",
        "file_type_all": "Все поддерживаемые",
        "file_type_pdf": "PDF документы",
        "file_type_img": "Изображения",
        "save_dialog_title": "Сохранить итоговый PDF как...",
        "warn_title": "Внимание",
        "warn_no_files": "Пожалуйста, добавьте файлы для объединения!",
        "success_title": "Успех",
        "success_toc": "Интерактивный PDF с оглавлением успешно создан:",
        "success_no_toc": "PDF без оглавления успешно создан:",
        "error_title": "Ошибка",
        "error_merge": "Не удалось объединить файлы:\n",
        "toc_title": "Оглавление",
        "info_title": "Информация о приложении",
        "info_header": "ℹ️ Информация о приложении",
        "info_sec1": " 1. Написать разработчику ",
        "info_contact": "Связаться в Telegram: ",
        "info_sec2": " 2. Возможности ",
        "info_features": (
            "• Объединение PDF документов и картинок (PNG, JPG, BMP)\n"
            "• Включение и выключение оглавления\n"
            "• Пропорциональное масштабирование картинок под формат A4\n"
            "• Автоматическая генерация интерактивного оглавления с точками\n"
            "• Кликабельные ссылки на страницы и боковые закладки (outline)\n"
            "• Удобное изменение порядка и удаление выбранных файлов"
        ),
        "btn_close": "Закрыть",
    },
    "uk": {
        "lang_name": "🌐 Українська",
        "app_title": "Об'єднання PDF та Зображень",
        "btn_add": "➕ Додати файли",
        "btn_up": "⬆ Вище",
        "btn_down": "⬇ Нижче",
        "btn_remove": "❌ Видалити",
        "btn_clear": "🗑 Очистити",
        "btn_info": "ℹ️ Інформація про програму",
        "btn_merge": "🚀 Об'єднати файли в PDF",
        "toc_checkbox": "Створювати інтерактивний зміст (за замовчуванням увімкнено)",
        "listbox_header": "Обрані файли (порядок об'єднання):",
        "file_dialog_title": "Оберіть PDF файли та зображення",
        "file_type_all": "Усі підтримувані",
        "file_type_pdf": "PDF документи",
        "file_type_img": "Зображення",
        "save_dialog_title": "Зберегти підсумковий PDF як...",
        "warn_title": "Увага",
        "warn_no_files": "Будь ласка, додайте файли для об'єднання!",
        "success_title": "Успіх",
        "success_toc": "Інтерактивний PDF зі змістом успішно створено:",
        "success_no_toc": "PDF без змісту успішно створено:",
        "error_title": "Помилка",
        "error_merge": "Не вдалося об'єднати файли:\n",
        "toc_title": "Зміст",
        "info_title": "Інформація про програму",
        "info_header": "ℹ️ Інформація про програму",
        "info_sec1": " 1. Написати розробнику ",
        "info_contact": "Зв'язатися в Telegram: ",
        "info_sec2": " 2. Можливості ",
        "info_features": (
            "• Об'єднання PDF документів та зображень (PNG, JPG, BMP)\n"
            "• Увімкнення та вимкнення змісту\n"
            "• Пропорційне масштабування зображень під формат A4\n"
            "• Автоматична генерація інтерактивного змісту з крапками\n"
            "• Кликабельні посилання на сторінки та бічні закладки (outline)\n"
            "• Зручне змінення порядку та видалення обраних файлів"
        ),
        "btn_close": "Закрити",
    },
    "de": {
        "lang_name": "🌐 Deutsch",
        "app_title": "PDF und Bilder zusammenfügen",
        "btn_add": "➕ Dateien hinzufügen",
        "btn_up": "⬆ Nach oben",
        "btn_down": "⬇ Nach unten",
        "btn_remove": "❌ Entfernen",
        "btn_clear": "🗑 Leeren",
        "btn_info": "ℹ️ App-Informationen",
        "btn_merge": "🚀 Dateien zu PDF zusammenfügen",
        "toc_checkbox": "Interaktives Inhaltsverzeichnis erstellen (Standard: aktiv)",
        "listbox_header": "Ausgewählte Dateien (Zusammenfügungsreihenfolge):",
        "file_dialog_title": "PDF-Dateien und Bilder auswählen",
        "file_type_all": "Alle unterstützten",
        "file_type_pdf": "PDF-Dokumente",
        "file_type_img": "Bilder",
        "save_dialog_title": "Ergebnis-PDF speichern unter...",
        "warn_title": "Warnung",
        "warn_no_files": "Bitte fügen Sie Dateien zum Zusammenfügen hinzu!",
        "success_title": "Erfolg",
        "success_toc": "Interaktives PDF mit Inhaltsverzeichnis erfolgreich erstellt:",
        "success_no_toc": "PDF ohne Inhaltsverzeichnis erfolgreich erstellt:",
        "error_title": "Fehler",
        "error_merge": "Dateien konnten nicht zusammengefügt werden:\n",
        "toc_title": "Inhaltsverzeichnis",
        "info_title": "App-Informationen",
        "info_header": "ℹ️ App-Informationen",
        "info_sec1": " 1. Entwickler kontaktieren ",
        "info_contact": "Kontakt über Telegram: ",
        "info_sec2": " 2. Funktionen ",
        "info_features": (
            "• Zusammenfügen von PDF-Dokumenten und Bildern (PNG, JPG, BMP)\n"
            "• Inhaltsverzeichnis ein- und ausschalten\n"
            "• Proportionale Bildskalierung auf das A4-Format\n"
            "• Automatische Erstellung eines interaktiven Inhaltsverzeichnisses mit Punkten\n"
            "• Klickbare Seitenlinks und Seiten-Lesezeichen (Outline)\n"
            "• Bequemes Ändern der Reihenfolge und Löschen ausgewählter Dateien"
        ),
        "btn_close": "Schließen",
    },
    "it": {
        "lang_name": "🌐 Italiano",
        "app_title": "Unisci PDF e Immagini",
        "btn_add": "➕ Aggiungi file",
        "btn_up": "⬆ Su",
        "btn_down": "⬇ Giù",
        "btn_remove": "❌ Rimuovi",
        "btn_clear": "🗑 Svuota",
        "btn_info": "ℹ️ Informazioni sull'app",
        "btn_merge": "🚀 Unisci file in PDF",
        "toc_checkbox": "Crea sommario interattivo (attivo per impostazione predefinita)",
        "listbox_header": "File selezionati (ordine di unione):",
        "file_dialog_title": "Seleziona file PDF e immagini",
        "file_type_all": "Tutti i file supportati",
        "file_type_pdf": "Documenti PDF",
        "file_type_img": "Immagini",
        "save_dialog_title": "Salva PDF finale come...",
        "warn_title": "Attenzione",
        "warn_no_files": "Si prega di aggiungere file da unire!",
        "success_title": "Successo",
        "success_toc": "PDF interattivo con sommario creato con successo:",
        "success_no_toc": "PDF senza sommario creato con successo:",
        "error_title": "Errore",
        "error_merge": "Impossibile unire i file:\n",
        "toc_title": "Sommario",
        "info_title": "Informazioni sull'app",
        "info_header": "ℹ️ Informazioni sull'app",
        "info_sec1": " 1. Scrivi allo sviluppatore ",
        "info_contact": "Contatta su Telegram: ",
        "info_sec2": " 2. Funzionalità ",
        "info_features": (
            "• Unione di documenti PDF e immagini (PNG, JPG, BMP)\n"
            "• Attivazione e disattivazione del sommario\n"
            "• Ridimensionamento proporzionale delle immagini nel formato A4\n"
            "• Generazione automatica di un sommario interattivo con puntini\n"
            "• Link cliccabili alle pagine e segnalibri laterali (outline)\n"
            "• Facile gestione dell'ordine e rimozione dei file selezionati"
        ),
        "btn_close": "Chiudi",
    },
    "fr": {
        "lang_name": "🌐 Français",
        "app_title": "Fusionner PDF et Images",
        "btn_add": "➕ Ajouter des fichiers",
        "btn_up": "⬆ Monter",
        "btn_down": "⬇ Descendre",
        "btn_remove": "❌ Supprimer",
        "btn_clear": "🗑 Effacer",
        "btn_info": "ℹ️ Informations sur l'application",
        "btn_merge": "🚀 Fusionner les fichiers en PDF",
        "toc_checkbox": "Créer une table des matières interactive (activée par défaut)",
        "listbox_header": "Fichiers sélectionnés (ordre de fusion) :",
        "file_dialog_title": "Sélectionner des fichiers PDF et des images",
        "file_type_all": "Tous les fichiers pris en charge",
        "file_type_pdf": "Documents PDF",
        "file_type_img": "Images",
        "save_dialog_title": "Enregistrer le PDF final sous...",
        "warn_title": "Attention",
        "warn_no_files": "Veuillez ajouter des fichiers à fusionner !",
        "success_title": "Succès",
        "success_toc": "PDF interactif avec table des matières créé avec succès :",
        "success_no_toc": "PDF sans table des matières créé avec succès :",
        "error_title": "Erreur",
        "error_merge": "Impossible de fusionner les fichiers :\n",
        "toc_title": "Table des matières",
        "info_title": "Informations sur l'application",
        "info_header": "ℹ️ Informations sur l'application",
        "info_sec1": " 1. Écrire au développeur ",
        "info_contact": "Contacter sur Telegram : ",
        "info_sec2": " 2. Fonctionnalités ",
        "info_features": (
            "• Fusion de documents PDF et d'images (PNG, JPG, BMP)\n"
            "• Activation et désactivation de la table des matières\n"
            "• Redimensionnement proportionnel des images au format A4\n"
            "• Génération automatique d'une table des matières interactive avec pointillés\n"
            "• Liens cliquables vers les pages et signets latéraux (outline)\n"
            "• Modification facile de l'ordre et suppression des fichiers sélectionnés"
        ),
        "btn_close": "Fermer",
    },
    "pl": {
        "lang_name": "🌐 Polski",
        "app_title": "Łączenie PDF i Obrazów",
        "btn_add": "➕ Dodaj pliki",
        "btn_up": "⬆ Wyżej",
        "btn_down": "⬇ Niżej",
        "btn_remove": "❌ Usuń",
        "btn_clear": "🗑 Wyczyść",
        "btn_info": "ℹ️ Informacje o aplikacji",
        "btn_merge": "🚀 Połącz pliki w PDF",
        "toc_checkbox": "Twórz interaktywny spis treści (domyślnie włączone)",
        "listbox_header": "Wybrane pliki (kolejność łączenia):",
        "file_dialog_title": "Wybierz pliki PDF i obrazy",
        "file_type_all": "Wszystkie obsługiwane",
        "file_type_pdf": "Dokumenty PDF",
        "file_type_img": "Obrazy",
        "save_dialog_title": "Zapisz końcowy PDF jako...",
        "warn_title": "Uwaga",
        "warn_no_files": "Proszę dodać pliki do połączenia!",
        "success_title": "Sukces",
        "success_toc": "Interaktywny PDF ze spisem treści został pomyślnie utworzony:",
        "success_no_toc": "PDF bez spisu treści został pomyślnie utworzony:",
        "error_title": "Błąd",
        "error_merge": "Nie udało się połączyć plików:\n",
        "toc_title": "Spis treści",
        "info_title": "Informacje o aplikacji",
        "info_header": "ℹ️ Informacje o aplikacji",
        "info_sec1": " 1. Napisz do twórcy ",
        "info_contact": "Skontaktuj się na Telegramie: ",
        "info_sec2": " 2. Możliwości ",
        "info_features": (
            "• Łączenie dokumentów PDF i obrazów (PNG, JPG, BMP)\n"
            "• Włączanie i wyłączanie spisu treści\n"
            "• Proporcjonalne skalowanie obrazów do formatu A4\n"
            "• Automatyczne generowanie interaktywnego spisu treści z kropkami\n"
            "• Klikalne linki do stron i zakładki boczne (outline)\n"
            "• Wygodna zmiana kolejności i usuwanie wybranych plików"
        ),
        "btn_close": "Zamknij",
    }
}


def run_gui():
    """
    Графический интерфейс на Tkinter с поддержкой локализации (RU, UK, DE, IT, FR, PL),
    информацией о приложении и возможностью включения/выключения оглавления.
    """
    import tkinter as tk
    from tkinter import filedialog, messagebox

    current_lang = "ru"

    root = tk.Tk()
    t_init = TRANSLATIONS[current_lang]
    root.title(t_init["app_title"])
    root.geometry("740x540")
    root.minsize(680, 500)

    selected_files = []
    toc_var = tk.BooleanVar(value=True)  # По умолчанию включено

    def update_listbox():
        listbox.delete(0, tk.END)
        for idx, f in enumerate(selected_files, start=1):
            listbox.insert(tk.END, f"{idx}. {os.path.basename(f)}")

    def add_files():
        t = TRANSLATIONS[current_lang]
        files = filedialog.askopenfilenames(
            title=t["file_dialog_title"],
            filetypes=[(t["file_type_all"], "*.pdf *.png *.jpg *.jpeg *.bmp"),
                       (t["file_type_pdf"], "*.pdf"),
                       (t["file_type_img"], "*.png *.jpg *.jpeg *.bmp")]
        )
        if files:
            selected_files.extend(files)
            update_listbox()

    def move_up():
        sel = listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            selected_files[idx], selected_files[idx - 1] = selected_files[idx - 1], selected_files[idx]
            update_listbox()
            listbox.selection_set(idx - 1)

    def move_down():
        sel = listbox.curselection()
        if sel and sel[0] < len(selected_files) - 1:
            idx = sel[0]
            selected_files[idx], selected_files[idx + 1] = selected_files[idx + 1], selected_files[idx]
            update_listbox()
            listbox.selection_set(idx + 1)

    def remove_selected():
        sel = listbox.curselection()
        if sel:
            idx = sel[0]
            selected_files.pop(idx)
            update_listbox()

    def clear_all():
        selected_files.clear()
        update_listbox()

    def merge():
        t = TRANSLATIONS[current_lang]
        if not selected_files:
            messagebox.showwarning(t["warn_title"], t["warn_no_files"])
            return

        save_path = filedialog.asksaveasfilename(
            title=t["save_dialog_title"],
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        if not save_path:
            return

        try:
            should_make_toc = toc_var.get()
            process_files(selected_files, save_path, make_toc=should_make_toc, toc_title=t["toc_title"])
            msg = t["success_toc"] if should_make_toc else t["success_no_toc"]
            messagebox.showinfo(t["success_title"], f"{msg}\n{save_path}")
        except Exception as e:
            messagebox.showerror(t["error_title"], f"{t['error_merge']}{e}")

    def open_dev_link(event=None):
        webbrowser.open_new_tab("https://t.me/ExpertMebeli")

    def show_info_window():
        t = TRANSLATIONS[current_lang]
        info_win = tk.Toplevel(root)
        info_win.title(t["info_title"])
        info_win.geometry("540x420")
        info_win.resizable(False, False)
        info_win.transient(root)
        info_win.grab_set()

        # Заголовок
        tk.Label(
            info_win,
            text=t["info_header"],
            font=("Arial", 13, "bold"),
            fg="#1565C0"
        ).pack(pady=(12, 5))

        main_frame = tk.Frame(info_win, padx=15, pady=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Раздел 1: Написать разработчику
        dev_frame = tk.LabelFrame(main_frame, text=t["info_sec1"], font=("Arial", 10, "bold"), fg="#2E7D32", padx=10, pady=8)
        dev_frame.pack(fill=tk.X, pady=(0, 10))

        dev_lbl = tk.Label(dev_frame, text=t["info_contact"], font=("Arial", 9, "bold"))
        dev_lbl.pack(side=tk.LEFT)

        dev_link = tk.Label(dev_frame, text="t.me/ExpertMebeli", font=("Arial", 9, "underline", "bold"), fg="#1E88E5", cursor="hand2")
        dev_link.pack(side=tk.LEFT)
        dev_link.bind("<Button-1>", open_dev_link)

        # Раздел 2: Возможности
        features_frame = tk.LabelFrame(main_frame, text=t["info_sec2"], font=("Arial", 10, "bold"), fg="#1565C0", padx=10, pady=8)
        features_frame.pack(fill=tk.BOTH, expand=True)

        features_label = tk.Label(features_frame, text=t["info_features"], font=("Arial", 9), justify=tk.LEFT, anchor="w")
        features_label.pack(anchor="w", fill=tk.BOTH, expand=True)

        tk.Button(info_win, text=t["btn_close"], command=info_win.destroy, font=("Arial", 10, "bold"), width=12, bg="#E0E0E0").pack(pady=10)

    def change_language(lang_code):
        nonlocal current_lang
        current_lang = lang_code
        t = TRANSLATIONS[current_lang]

        root.title(t["app_title"])
        lang_button.config(text=t["lang_name"] + " ▾")
        btn_info.config(text=t["btn_info"])
        btn_add.config(text=t["btn_add"])
        btn_up.config(text=t["btn_up"])
        btn_down.config(text=t["btn_down"])
        btn_remove.config(text=t["btn_remove"])
        btn_clear.config(text=t["btn_clear"])
        toc_checkbox.config(text=t["toc_checkbox"])
        btn_merge.config(text=t["btn_merge"])
        listbox_label.config(text=t["listbox_header"])

    # Верхний контейнер: Слева управление файлами, Справа кнопка информации о приложении и выпадающее меню локализации
    top_container = tk.Frame(root)
    top_container.pack(fill=tk.X, padx=10, pady=10)

    # Правый блок верхнего контейнера (Локализация + Инфо)
    right_toolbar = tk.Frame(top_container)
    right_toolbar.pack(side=tk.RIGHT, anchor="ne")

    # Кнопка локализации с выпадающим меню (Справа вверху)
    lang_button = tk.Menubutton(
        right_toolbar,
        text=t_init["lang_name"] + " ▾",
        font=("Arial", 10, "bold"),
        bg="#ECEFF1",
        fg="#37474F",
        relief=tk.RAISED,
        padx=8,
        pady=5
    )
    lang_menu = tk.Menu(lang_button, tearoff=0)
    lang_button["menu"] = lang_menu

    for code_key, data_dict in TRANSLATIONS.items():
        lang_menu.add_command(
            label=data_dict["lang_name"],
            command=lambda c=code_key: change_language(c)
        )

    lang_button.pack(side=tk.RIGHT, padx=(5, 0))

    # Кнопка вызова окна информации о приложении
    btn_info = tk.Button(
        right_toolbar,
        text=t_init["btn_info"],
        command=show_info_window,
        bg="#E3F2FD",
        fg="#1565C0",
        font=("Arial", 10, "bold"),
        relief=tk.RAISED,
        padx=8,
        pady=5
    )
    btn_info.pack(side=tk.RIGHT, padx=(0, 5))

    # Слева: Кнопки управления файлами
    btn_frame = tk.Frame(top_container)
    btn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

    btn_add = tk.Button(btn_frame, text=t_init["btn_add"], command=add_files, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
    btn_add.pack(side=tk.LEFT, padx=(0, 5))

    btn_up = tk.Button(btn_frame, text=t_init["btn_up"], command=move_up)
    btn_up.pack(side=tk.LEFT, padx=2)

    btn_down = tk.Button(btn_frame, text=t_init["btn_down"], command=move_down)
    btn_down.pack(side=tk.LEFT, padx=2)

    btn_remove = tk.Button(btn_frame, text=t_init["btn_remove"], command=remove_selected)
    btn_remove.pack(side=tk.LEFT, padx=2)

    btn_clear = tk.Button(btn_frame, text=t_init["btn_clear"], command=clear_all)
    btn_clear.pack(side=tk.LEFT, padx=2)

    # Список выбранных файлов
    listbox_frame = tk.Frame(root)
    listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    listbox_label = tk.Label(listbox_frame, text=t_init["listbox_header"], font=("Arial", 10, "bold"), anchor="w")
    listbox_label.pack(anchor="w", pady=(0, 2))

    scrollbar = tk.Scrollbar(listbox_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Arial", 11), selectmode=tk.SINGLE)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    # Чекбокс оглавления
    options_frame = tk.Frame(root)
    options_frame.pack(fill=tk.X, padx=10, pady=5)

    toc_checkbox = tk.Checkbutton(
        options_frame,
        text=t_init["toc_checkbox"],
        variable=toc_var,
        font=("Arial", 11)
    )
    toc_checkbox.pack(side=tk.LEFT)

    # Кнопка запуска
    btn_merge = tk.Button(root, text=t_init["btn_merge"], command=merge, bg="#2196F3", fg="white", font=("Arial", 12, "bold"), height=2)
    btn_merge.pack(fill=tk.X, padx=10, pady=10)

    root.mainloop()


def main():
    if len(sys.argv) < 2:
        run_gui()
        return

    files = sys.argv[1:]

    output_name = input("Введите имя итогового файла (без расширения): ").strip()
    if not output_name:
        output_name = "project_with_interactive_toc"

    ans = input("Создавать оглавление? (Д/н, по умолчанию Да): ").strip().lower()
    make_toc = True
    if ans in ("н", "n", "нет", "no"):
        make_toc = False

    process_files(files, output_name, make_toc=make_toc)


if __name__ == "__main__":
    main()
