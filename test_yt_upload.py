import sys
import os
import time

sys.path.append(os.path.abspath("."))
from src.uploader import get_driver, safe_send_keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def upload_dummy():
    driver = get_driver()
    try:
        videopath = os.path.abspath(r"output\TEST_Los_Rostros_Más_ÚNICOS_del_Planeta_Tierra_Top3\short_final.mp4")
        if not os.path.exists(videopath):
            print(f"File not found: {videopath}")
            return
            
        print("Navigating to YouTube Studio...")
        driver.get("https://studio.youtube.com")
        wait = WebDriverWait(driver, 15)
        
        print("Clicking Create -> Upload...")
        try:
            upload_icon = wait.until(EC.element_to_be_clickable((By.ID, "upload-icon")))
            print("FOUND upload-icon")
            upload_icon.click()
        except:
            print("Trying create-icon approach...")
            create_btn = wait.until(EC.element_to_be_clickable((By.ID, "create-icon")))
            create_btn.click()
            time.sleep(1)
            upload_menu_item = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='text-item-0' or contains(text(), 'Upload') or contains(text(), 'Subir')]")))
            upload_menu_item.click()
        
        time.sleep(2)
        print("Uploading file...")
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        file_input.send_keys(videopath)
        
        time.sleep(5)
        
        print("Selecting Not made for kids...")
        kids_radio = wait.until(EC.presence_of_element_located((By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", kids_radio)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", kids_radio)
        
        print("Clicking Next through modals...")
        while True:
            schedule_elements = driver.find_elements(By.NAME, "SCHEDULE")
            if len(schedule_elements) > 0 and schedule_elements[0].is_displayed():
                schedule_radio = schedule_elements[0]
                break
            try:
                # Need short wait so we don't block 15 seconds if next button isn't there
                short_wait = WebDriverWait(driver, 2)
                next_btn = short_wait.until(EC.element_to_be_clickable((By.ID, "next-button")))
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(1)
            except Exception as e:
                time.sleep(1)
            
        print("Clicking Schedule Radio...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", schedule_radio)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", schedule_radio)
        
        time.sleep(1)
        
        schedule_date = "25/03/2026"
        schedule_time = "18:00"
        
        print("--- TESTING DATE/TIME INJECTION ---")
        try:
            print("Setting Date...")
            date_container = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='datepicker-trigger'] | //*[contains(@class, 'datepicker')]")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_container)
            time.sleep(0.5)
            
            current_date_val = driver.execute_script("return arguments[0].innerText || arguments[0].textContent;", date_container)
            try:
                d_parts = schedule_date.split("/")
                if len(d_parts) == 3:
                    d, m, y = int(d_parts[0]), int(d_parts[1]), int(d_parts[2])
                    es_m = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
                    en_m = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    
                    is_english = current_date_val and any(en in current_date_val for en in en_m)
                    if is_english:
                        schedule_date_str = f"{en_m[m-1]} {d}, {y}"
                    else:
                        schedule_date_str = f"{d} {es_m[m-1]} {y}"
                    print(f"Reformatted date for YouTube Locale: {schedule_date_str} (Based on '{current_date_val}')")
            except Exception as e:
                print(f"Date formatting fallback due to: {e}")
                schedule_date_str = schedule_date

            driver.execute_script("arguments[0].click();", date_container)
            time.sleep(0.5)
            
            actions = ActionChains(driver)
            import pyperclip
            
            actions.send_keys(Keys.END).perform()
            actions.send_keys(Keys.BACKSPACE * 20).perform()
            time.sleep(0.5)
            
            pyperclip.copy(schedule_date_str)
            actions.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
            time.sleep(0.5)
            
            actions.send_keys(Keys.TAB).perform()
            time.sleep(0.5)
            
            print("Setting Time...")
            # We will grab the parent row that contains BOTH date and time
            # The date container is already found. Let's find its parent.
            parent_row = date_container.find_element(By.XPATH, "./ancestor::div[contains(@class, 'style-scope ytcp-video-schedule')]")
            print("FOUND PARENT ROW HTML:")
            print(parent_row.get_attribute('outerHTML'))
            
            # Now let's try to specifically find the time input within that parent row
            time_container = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='time-of-day-trigger'] | //*[contains(@class, 'time-picker')]")))
            print("\nFOUND TIME CONTAINER HTML:")
            print(time_container.get_attribute('outerHTML'))
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", time_container)
            time.sleep(0.5)
            
            driver.execute_script("arguments[0].click();", time_container)
            time.sleep(0.5)
            
            actions.send_keys(Keys.END).perform()
            actions.send_keys(Keys.BACKSPACE * 10).perform()
            time.sleep(0.5)
            
            pyperclip.copy(schedule_time)
            actions.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
            time.sleep(0.5)
            
            actions.send_keys(Keys.ENTER).perform()
            time.sleep(0.5)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            print("SUCCESSFULLY INJECTED DATE AND TIME.")
            
            try:
                overlay = driver.find_element(By.TAG_NAME, "tp-yt-iron-overlay-backdrop")
                print("Overlay displayed?", overlay.is_displayed())
            except:
                print("No overlay found.")
            
            print("Clicking Save in 10s (Check visual state)...")
            time.sleep(10)
            
            try:
                done_btn = wait.until(EC.element_to_be_clickable((By.ID, "done-button")))
                done_btn.click()
                print("SAVED!")
            except Exception as e:
                print("Failed to click save button:", e)
                
            time.sleep(5)
            
        except Exception as e:
            print(f"Error setting date/time: {e}")

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except: pass

if __name__ == "__main__":
    upload_dummy()
