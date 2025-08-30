# DC-Dark-Legion-Helper
Currently a bleed simulator for DC Dark Legion.

## [Download](https://github.com/Thecarlosmff/DC-Dark-Legion-Helper/releases) 

 ![Help](Help.png)
 
## Setup (For devs)

1. **Windows**  
   - Double-click `setup_env_windows.bat`  
   - Wait until it finishes installing Python + dependencies  
   - Run:  
     ```
     venv\Scripts\activate.bat
     python main.py
     ```

2. **Linux / macOS**  
   - Run in terminal:  
     ```bash
     chmod +x setup_env_mac-linux.sh
     ./setup_env.sh
     source venv/bin/activate
     python main.py
     ```

### Notes
- First run will set everything up.  
- Next time, just activate the environment and run the app.  
- If Python was already installed, it won’t reinstall.  


## How to create an executable file

   ```bash
   pip install PyInstaller
   pyinstaller --noconsole --onefile -F main.py
   ```
