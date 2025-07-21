# Client app
Desktop client for receipt app
works with windows 10/11

## Installation
1. Create and activate python venv:
```
python -m venv .venv
source .venv/Scripts/activate
```
2. Install dependencies:
```
pip install app/requirements.txt
```
3. build app with PyInstaller:
```
cd app
pyinstaller snapshot-1-0.spec
```
Application will be built as an exe file if app/dist directory
## Run the app
To launch app just click on exe file

### Run without build
To run app without build, complete dependencies installation and run:
```
python app/main.py
```