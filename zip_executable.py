import os
import zipfile
from pathlib import Path

def main():
    print("Erstelle ZIP-Datei für die WCAG Checker Anwendung...")

    # Pfade definieren
    dist_folder = Path('dist')
    zip_folder = dist_folder / 'main'
    output_zip = dist_folder / 'wcag_checker.zip'
    folder_name_in_zip = 'wcag_checker'



    # Sicherstellen, dass der dist-Ordner existiert
    if not os.path.exists(zip_folder):
        raise FileNotFoundError(f"Der Ordner '{zip_folder}' wurde nicht gefunden.")

    # ZIP-Datei erstellen
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(zip_folder):
            for file in files:
                print(f"Füge Datei '{file}' zum ZIP hinzu...")
                file_path = os.path.join(root, file)
                # Relativen Pfad anpassen, um den Ordnernamen im ZIP zu ändern
                arcname = os.path.join(folder_name_in_zip, os.path.relpath(file_path, zip_folder))
                zipf.write(file_path, arcname)

    print(f"ZIP-Datei '{output_zip}' wurde erfolgreich erstellt.")

if __name__ == "__main__":
    main()