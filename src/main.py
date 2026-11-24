#main.py
import RPi.GPIO as GPIO
import time
import os
import shutil
from RPLCD.i2c import CharLCD


#setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=20, rows=4, charmap='A00', auto_linebreaks=True)
lcd.clear()

LED_RUNNING = 17
LED_SD = 27
LED_OK = 22
LED_ERROR = 10
current_user = 0
current_choice = 0
BUTTON_back = 5
BUTTON_forward = 6
BUTTON_confirm = 26
username = os.getlogin()
users = ["Janek", "Helena"]
choice = ["Yes", "No "]
sd_path = f"/media/{username}"
backup_path = "/backup-data"
backup_done = False
os.makedirs(backup_path, exist_ok=True)
GPIO.setup(LED_RUNNING, GPIO.OUT)
GPIO.setup(LED_SD, GPIO.OUT)
GPIO.setup(LED_OK, GPIO.OUT)
GPIO.setup(LED_ERROR, GPIO.OUT)
GPIO.setup(BUTTON_back, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_forward, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_confirm, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#find sd card
def find_sd(): 
    if os.path.exists(sd_path):
        for item in os.listdir(sd_path):
            full_path = os.path.join(sd_path, item)
            if os.path.ismount(full_path):
                return full_path
    return None

#copy sd card files to backup folder
def copy_sd_to_backup(sd_mount):
    try:
        for item in os.listdir(sd_mount):
            source = os.path.join(sd_mount, item)
            dest = os.path.join(backup_path, item)
            if os.path.isdir(source):
                shutil.copytree(source, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(source, dest)
        return True
    except Exception as e:
        GPIO.output(LED_ERROR, GPIO.HIGH)
        return False

#deletes sd card
def clear_sd(sd_mount):
    try:
        for item in os.listdir(sd_mount):
            path = os.path.join(sd_mount, item)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        return True
    except Exception as err:
        return False
    
#start
GPIO.output(LED_RUNNING, GPIO.HIGH)
lcd.cursor_pos = (0, 0)
lcd.write_string("Running")
lcd.cursor_pos = (1, 0)
lcd.write_string("insert SD-card")

#lcd_status, shortens the proccess of writing on the lcd display
def lcd_status(l1, l2, l3, l4, clear_lcd):
    if clear_lcd == "Yes":
        lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string(l1)
    lcd.cursor_pos = (1, 0)
    lcd.write_string(l2)
    lcd.cursor_pos = (2, 0)
    lcd.write_string(l3)
    lcd.cursor_pos = (3, 0)
    lcd.write_string(l4)


#main loop
while True:
    sd_mount = find_sd()
    if sd_mount and backup_done == False:
        GPIO.output(LED_SD, GPIO.HIGH)
        lcd_status("insert sd card", "", "", "", Yes) 
        user_selected = False
        while not user_selected and find_sd(): #select user
            lcd_status("select user", f">{users[current_user]}", "", "", Yes)
            if GPIO.input(BUTTON_forward) == GPIO.LOW:
                current_user = (current_user + 1) % len(users)
            elif GPIO.input(BUTTON_back) == GPIO.LOW:
                current_user = (current_user - 1) % len(users)
            elif GPIO.input(BUTTON_confirm) == GPIO.LOW:
                backup_user_path = f"/backup-data/{users[current_user]}"
                os.makedirs(backup_user_path, exist_ok=True)
                backup_path = f"/backup-data/{users[current_user]}"
                user_selected = True
                break
            time.sleep(0.3)

        if user_selected and find_sd(): #backup SD-card
            lcd_status(f"selected user: {users[current_user]}", "", "", "", Yes)
            time.sleep(0.5)
            lcd_status("starting backup...", "", "", "", Yes)
            success = copy_sd_to_backup(sd_mount)
            if success:
                lcd_status("backup done", "", "", "", Yes)
                GPIO.output(LED_OK, GPIO.HIGH)
                backup_done = True
                time.sleep(0.4)
                lcd_status("", "erase SD-card?", "", "", No) #ask for deletion of SD-card
                delete_choice = False
                while find_sd() and not delete_choice:
                    lcd_status("", "", f">{choice[current_choice]}", "", No)
                    if GPIO.input(BUTTON_forward) == GPIO.LOW:
                        current_choice = (current_choice + 1) % len(choice)
                    elif GPIO.input(BUTTON_back) == GPIO.LOW:
                        current_choice = (current_choice - 1) % len(choice)
                    elif GPIO.input(BUTTON_confirm) == GPIO.LOW:
                        if choice[current_choice] == "Yes":
                            lcd_status("press confirm to", "erase else take out", "SD-card", "", Yes)
                            if GPIO.input(BUTTON_confirm) == GPIO.LOW:
                                clear_sd(sd_mount)
                                delete_choice = True
                        if choice[current_choice] == "No":
                            delete_choice = True
                    time.sleep(0.2)
            if not success:
                GPIO.output(LED_ERROR, GPIO.HIGH)
    else:
        GPIO.output(LED_SD, GPIO.LOW)
        GPIO.output(LED_OK, GPIO.LOW)
        GPIO.output(LED_ERROR, GPIO.LOW)
        lcd_status("insert SD-card", "", "", "", "Yes")
        backup_done = False
    time.sleep(0.5)
