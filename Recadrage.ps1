# ==============================================================================
# Script de Recadrage & Redimensionnement Automatique d'Icône (512x512)
# ==============================================================================
# Ce script prépare votre image pour une conversion optimale en icône Windows.
#
# Utilisation :
#   Faites un clic droit sur ce fichier > "Exécuter avec PowerShell"
#   Ou lancez : powershell -ExecutionPolicy Bypass -File Recadrage.ps1
# ==============================================================================

Add-Type -AssemblyName System.Drawing

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  RECADRAGE ET NORMALISATION D'ICÔNE (512x512 PNG)" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $CurrentDir) { $CurrentDir = Get-Location }

# Recherche de l'image source
$Candidates = @(
    "dango_translate_icon_512.png",
    "peas_translate_icon_512.png",
    "app_icon.png",
    "icon.png",
    "custom_icon.png",
    "logo.png"
)

$SourceFile = $null
foreach ($Candidate in $Candidates) {
    $TestPath = Join-Path $CurrentDir $Candidate
    if (Test-Path $TestPath) {
        $SourceFile = $TestPath
        break
    }
}

if (-not $SourceFile) {
    $AnyImage = Get-ChildItem -Path $CurrentDir -Include *.png, *.jpg, *.jpeg, *.webp -File | Select-Object -First 1
    if ($AnyImage) {
        $SourceFile = $AnyImage.FullName
    }
}

if (-not $SourceFile) {
    Write-Host "[ERREUR] Aucune image trouvée dans le dossier !" -ForegroundColor Red
    Write-Host "Placez votre image (ex: dango_translate_icon_512.png) dans ce dossier et réessayez."
    Read-Host "Appuyez sur Entrée pour quitter..."
    exit 1
}

Write-Host "[INFO] Image source détectée : $(Split-Path $SourceFile -Leaf)" -ForegroundColor Green

$SourceImage = [System.Drawing.Image]::FromFile($SourceFile)
$TargetSize = 512

# Calcul du ratio pour centrer sans déformation
$RatioX = $TargetSize / $SourceImage.Width
$RatioY = $TargetSize / $SourceImage.Height
$Ratio = [Math]::Min($RatioX, $RatioY)

$NewWidth = [int]($SourceImage.Width * $Ratio)
$NewHeight = [int]($SourceImage.Height * $Ratio)
$PosX = [int](($TargetSize - $NewWidth) / 2)
$PosY = [int](($TargetSize - $NewHeight) / 2)

$SquareBitmap = New-Object System.Drawing.Bitmap($TargetSize, $TargetSize, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$Graphics = [System.Drawing.Graphics]::FromImage($SquareBitmap)

# Qualité maximale
$Graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$Graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$Graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$Graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

$Graphics.Clear([System.Drawing.Color]::Transparent)
$Graphics.DrawImage($SourceImage, $PosX, $PosY, $NewWidth, $NewHeight)

$OutputFile = Join-Path $CurrentDir "icon_512x512.png"
$SquareBitmap.Save($OutputFile, [System.Drawing.Imaging.ImageFormat]::Png)

$Graphics.Dispose()
$SquareBitmap.Dispose()
$SourceImage.Dispose()

Write-Host "[SUCCÈS] Image recadrée en 512x512 carrée : icon_512x512.png" -ForegroundColor Green
Write-Host "Vous pouvez maintenant lancer 'python convert_icon.py' pour générer 'icon.ico' !" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
