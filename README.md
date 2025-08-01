# Photis desktop client
Compatible with windows 10/11 and linux distributions

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
This will launch pyinstaller build proccess. As result application will be built as an exe file in app/dist directory
## Run the app
To launch app just click on exe file

### Run without build / installation 
To run app without build, complete point 1 in Installation proccess and simply run ``` python app/main.py ```