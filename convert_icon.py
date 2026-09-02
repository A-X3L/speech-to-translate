"""
Convertisseur Automatique d'Image en Icône Windows (.ico)
==========================================================
Usage :
1. Placez votre image PNG personnalisée (ex: dango_translate_icon_512.png, peas_translate_icon_512.png ou icon.png).
2. Lancez ce script : python convert_icon.py
3. Il génère automatiquement 'icon.ico' en multi-résolutions (256x256, 128x128, 64x64, 48x48, 32x32, 16x16)
4. Exécutez ensuite 'creer_raccourci_bureau.bat' pour appliquer l'icône à votre raccourci Windows !
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    print("[INFO] Installation de Pillow pour la conversion d'image...")
    os.system(f'"{sys.executable}" -m pip install pillow --quiet')
    from PIL import Image

def convert_to_icon():
    print("=" * 60)
    print("  CONVERTISSEUR D'ICÔNE POUR RACCOURCI BUREAU WINDOWS")
    print("=" * 60)
    
    candidates = [
        "dango_translate_icon_512.png",
        "peas_translate_icon_512.png",
        "app_icon.png", 
        "icon.png", 
        "custom_icon.png", 
        "logo.png", 
        "icon.jpg", 
        "app_icon.jpg"
    ]
    src_file = None
    
    for fname in candidates:
        if os.path.exists(fname):
            src_file = fname
            break
            
    if not src_file:
        png_files = [f for f in os.listdir(".") if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        if png_files:
            src_file = png_files[0]

    if not src_file:
        print("\n[ERREUR] Aucune image PNG trouvée dans le dossier !")
        print("Veuillez placer votre image sous le nom 'dango_translate_icon_512.png' ou 'icon.png'.")
        input("\nAppuyez sur Entrée pour quitter...")
        return

    print(f"\n[1/2] Chargement de l'image source : {src_file}")
    img = Image.open(src_file)
    
    if img.mode != "RGBA":
        img = img.convert("RGBA")
        
    output_ico = "icon.ico"
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    print(f"[2/2] Génération du fichier multi-résolutions '{output_ico}'...")
    img.save(output_ico, format="ICO", sizes=icon_sizes)
    
    print(f"\n[SUCCÈS] L'icône '{output_ico}' a été créée avec succès !")
    print("Vous pouvez maintenant double-cliquer sur 'creer_raccourci_bureau.bat'.")
    print("=" * 60)

if __name__ == "__main__":
    convert_to_icon()
