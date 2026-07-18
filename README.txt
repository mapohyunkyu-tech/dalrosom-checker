MARKET SCOUT EXE BUILD PACKAGE

IMPORTANT
- This package does not contain a prebuilt Windows EXE.
- A Windows EXE cannot be safely compiled in the current Linux environment.
- The project is ready for PyInstaller.
- You can build in GitHub Actions without installing Python on your PC.

METHOD A - BUILD IN GITHUB, NO PYTHON ON YOUR PC
1. Create a free GitHub account.
2. Create a new private repository.
3. Upload every file and folder from this package.
   Keep the .github/workflows/build-windows.yml path unchanged.
4. Open the Actions tab.
5. Select "Build Windows EXE".
6. Click "Run workflow".
7. When it finishes, download the MarketScout_Windows artifact.
8. Extract MarketScout_Windows.zip.
9. Double-click MarketScout.exe.

METHOD B - BUILD LOCALLY
1. Install Python 3.11 or newer.
2. Double-click build.bat.
3. The finished portable package is:
   release\MarketScout_Windows.zip

PORTABLE APP
- No Python is required after the EXE is built.
- Keep all files inside the MarketScout folder.
- Run MarketScout.exe.
- Results are saved in output.
- History is saved in data.
- Product values remain Korean because Korean keywords must be matched.
- File names, code, folders, and sheet names are English.

CHROME
- Google Chrome must be installed.
- Selenium Manager downloads or locates the matching driver automatically.
- Internet access is required during use.

LIMITS
- The program can collect only ranking information visible on the public webpage.
- A Naver layout change can require a collector update.
- Windows Defender may scan an unsigned PyInstaller application on first run.
