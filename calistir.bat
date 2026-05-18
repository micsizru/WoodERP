@echo off
rem Konsolun Turkce karakterleri desteklemesi icin UTF-8 aktif et
chcp 65001 >nul
title WoodERP Baslatici ve Kurucu

echo ===================================================
echo             WoodERP Akilli Baslatici
echo ===================================================
echo [BILGI] WoodERP altyapisi ve bagimliliklari kontrol ediliyor...
echo.

rem 1. Python yuklu mu kontrol et
python --version >nul 2>&1
if %errorlevel% equ 0 goto PYTHON_EXISTS

:NO_PYTHON
echo [HATA] Bilgisayarinizda Python bulunamadi!
echo WoodERP'yi calistirabilmek iÃ§in Python gereklidir.
echo.
set /p secim="Sizin icin otomatik olarak Python 3.11 kurmami ister misiniz? (E/H): "

if /i "%secim%"=="E" goto INSTALL_PYTHON
goto EXIT_NO_PYTHON

:INSTALL_PYTHON
echo.
echo [KURULUM] Python 3.11 indiriliyor ve kuruluyor, lutfen bekleyin...
echo [BILGI] Acilan pencerede Yonetici izni istenirse lutfen onay veriniz.
echo.

rem winget ile sessiz kurulum dener
winget install --id Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 goto INSTALL_FAILED

echo.
echo [BASARILI] Python basariyla kuruldu!
echo [ONEMLI] Ortam degiskenlerinin aktif olmasi icin bu pencereyi kapatip
echo           calistir.bat dosyasini yeniden baslatmaniz gerekmektedir.
echo.
pause
exit /b

:INSTALL_FAILED
echo.
echo [HATA] Otomatik kurulum basarisiz oldu veya winget paketi bulunamadi.
echo Lutfen Python'i resmi sitesinden (python.org) manuel olarak indirin.
pause
exit /b

:EXIT_NO_PYTHON
echo.
echo [HATA] Python olmadan WoodERP calistirilamaz. Cikis yapiliyor...
pause
exit /b


:PYTHON_EXISTS
echo [OK] Sistemde Python algilandi. Surum:
python --version
goto CHECK_VENV


:CHECK_VENV
echo.
echo [BILGI] Sanal ortam (venv) durumu sorgulaniyor...
if exist venv goto ACTIVATE_VENV

:CREATE_VENV
echo [ILK KURULUM] Sanal ortam (venv) bulunamadi. SÄ±fÄ±rdan olusturuluyor...
python -m venv venv
if %errorlevel% neq 0 goto VENV_FAILED

echo [OK] Sanal ortam (venv) basariyla olusturuldu!
echo.
echo [BILGI] Bagimlilik kutuphaneleri (requirements.txt) kontrol ediliyor...
echo [YUKLEME] pip paket yoneticisi en son surume guncelleniyor...
echo.

call venv\Scripts\activate
python -m pip install --upgrade pip >nul 2>&1

echo [YUKLEME] Gerekli kutuphaneler kuruluyor...
echo [BILGI] Bu islem internet hizinizla alakali olarak birkac dakika surebilir.
echo.

pip install -r requirements.txt
if %errorlevel% neq 0 goto PIP_FAILED

echo.
echo [OK] Tum kutuphaneler basariyla kuruldu ve entegre edildi!
goto START_APP


:VENV_FAILED
echo [HATA] Sanal ortam olusturulamadi! Lutfen Python kurulumunuzu kontrol edin.
pause
exit /b


:PIP_FAILED
echo [HATA] KÃ¼tÃ¼phaneler yuklenirken bir sorun olustu! Internet baglantinizi kontrol edin.
pause
exit /b


:ACTIVATE_VENV
echo [OK] Klasor kontrolu: Aktif bir sanal ortam (venv) zaten mevcut.
echo [BILGI] Sanal ortam aktiflestiriliyor...
call venv\Scripts\activate
goto START_APP


:START_APP
echo.
echo ===================================================
echo [BASARILI] WoodERP Baslatiliyor...
echo ===================================================
echo Uygulama Adresi: http://127.0.0.1:5000
echo Kapatmak icin bu terminali veya pencereyi kapatabilirsiniz.
echo ===================================================
echo.

rem Arka planda 2 saniye bekleyip tarayiciyi tamamen SIZI ve GIZLI sekilde acar (ikinci pencereyi acar kalmaz!)
start /b powershell -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process http://127.0.0.1:5000"

python app.py
pause
