import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

def get_driver(headless=False):
    """
    Initializes Chrome driver with a persistent user profile.
    This keeps the user logged in to Google/YouTube Studio.
    """
    # Create profile path in AppData/Local/Temp to avoid project folder locking issues
    import tempfile
    profile_path = os.path.join(tempfile.gettempdir(), "Venta_APP_Chrome_Profile")
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
        
    # Remove lock files to prevent SessionNotCreated errors on crash/restart
    # On Windows, these files prevent a new instance from starting if the previous one didn't close cleanly.
    lock_files = ["SingletonLock", "SingletonCookie", "SingletonSocket", "lock"]
    
    def try_remove_locks():
        removed_all = True
        for lock_name in lock_files:
            lock_file = os.path.join(profile_path, lock_name)
            if os.path.exists(lock_file):
                try: 
                    os.remove(lock_file)
                    print(f"Removed old Chrome lock: {lock_name}")
                except Exception:
                    removed_all = False
        return removed_all

    if not try_remove_locks():
        print("Profile locked. Attempting to force-close Chrome processes...")
        import subprocess
        try:
            # Kill any running Chrome or ChromeDriver processes to release locks
            subprocess.run(["taskkill", "/f", "/im", "chrome.exe", "/t"], capture_output=True)
            subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe", "/t"], capture_output=True)
            time.sleep(2) # Wait for OS to release file handles
            try_remove_locks() # Try again after killing
        except Exception as e:
            print(f"Force-close failed: {e}")
            
    # Auto-delete corrupt JSON template files that cause EOF errors
    import json
    for json_file in ["Local State", "Default/Preferences"]:
        file_path = os.path.join(profile_path, json_file)
        if os.path.exists(file_path):
            try:
                # If it's empty (0 bytes) or corrupted json, this will fail
                if os.path.getsize(file_path) == 0:
                    os.remove(file_path)
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        json.load(f)
            except Exception:
                try: os.remove(file_path)
                except: pass
    
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={profile_path}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Hide automation flags from Google to prevent login blocks
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        # Headless mode sometimes is detected by Google easily, so add user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute script to hide webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def check_login_status():
    """
    Chequea de forma silenciosa e instantánea si existe el perfil y tiene cookies.
    Evita lanzar un navegador headless que bloquearía el perfil.
    """
    import os
    import tempfile
    
    # Ruta al archivo de cookies del perfil que usa la App
    profile_path = os.path.join(tempfile.gettempdir(), "Venta_APP_Chrome_Profile", "Default", "Network", "Cookies")
    
    if os.path.exists(profile_path):
        try:
            # Un perfil virgen sin login de Google suele tener < 10KB de cookies.
            # Una sesión iniciada genera un archivo de Cookies de más de 20KB.
            if os.path.getsize(profile_path) >= 8000: # 8KB como umbral de seguridad
                return True
        except:
            pass
    return False

def logout_user():
    """Borra la carpeta del perfil de Chrome para forzar el cierre de sesión."""
    import tempfile
    import shutil
    profile_path = os.path.join(tempfile.gettempdir(), "Venta_APP_Chrome_Profile")
    if os.path.exists(profile_path):
        try:
            shutil.rmtree(profile_path)
            return True
        except:
            return False
    return False

def open_browser_for_login(on_login_success=None):
    """
    Opens the browser specifically for the user to log in.
    Navigates to YouTube and automatically closes when login is detected.
    """
    try:
        # Open NON-headless for actual login
        driver = get_driver(headless=False)
        print("Opening YouTube for login...")
        driver.get("https://studio.youtube.com")
        print("Login window open. Please log in...")
        
        while True:
            try:
                if not driver.window_handles:
                    break
                
                current_url = driver.current_url
                if "studio.youtube.com" in current_url and "accounts.google.com" not in current_url:
                    # Look for avatar to confirm successful login to studio
                    try:
                        avatar = driver.find_elements(By.ID, "avatar-btn")
                        if avatar or "channel" in current_url:
                            print("Login successful detected!")
                            if on_login_success:
                                on_login_success()
                            time.sleep(2)  # Give user a moment to see it's done
                            driver.quit()
                            break
                    except:
                        pass
                time.sleep(1)
            except:
                break
        print("Login browser session ended.")
    except Exception as e:
        print(f"Login Browser Error: {e}")

def safe_send_keys(driver, element, text):
    """Types text safely avoiding TrustedHTML errors and ensuring YouTube syncs state."""
    try:
        # 1. Focus the element
        driver.execute_script("arguments[0].focus();", element)
        time.sleep(0.2)
        
        # 2. Clear content via keys (Most robust for contenteditable)
        # We use Control+A followed by Backspace to clear everything YouTube put there by default
        from selenium.webdriver.common.keys import Keys
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.BACKSPACE)
        time.sleep(0.2)
        
        # 3. Clear via JS using safe properties (Avoid innerHTML)
        # innerText and textContent are usually allowed by TrustedHTML policies
        driver.execute_script(
            "arguments[0].innerText = ''; "
            "arguments[0].textContent = ''; "
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true})); "
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            element
        )
        time.sleep(0.1)
        
        # 4. Set text via JS (Supports emojis/complex chars)
        driver.execute_script(
            "arguments[0].innerText = arguments[1]; "
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true})); "
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            element, text
        )
        
        # 5. Trigger an extra keyboard event to ensure YouTube's internal 'save' state is dirty
        # Sometimes setting innerText via JS doesn't enable the 'Next' button if no keyboard event followed.
        element.send_keys(" ")
        element.send_keys(Keys.BACKSPACE)
        time.sleep(0.2)
        
    except Exception as e:
        print(f"safe_send_keys failed: {e}")
        # Fallback to pure Selenium
        try:
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.BACKSPACE)
            element.send_keys(text)
        except: pass

def close_studio_popups(driver):
    """
    Looks for and closes common YouTube Studio popups/overlays
    that might block interaction with the upload buttons.
    """
    popups_selectors = [
        "//ytcp-button[@id='dismiss-button']",
        "//ytcp-button[contains(text(), 'Dismiss')]",
        "//ytcp-button[contains(text(), 'Entendido')]",
        "//ytcp-button[contains(text(), 'Cerrar')]",
        "//ytcp-button[contains(text(), 'Close')]",
        "//ytcp-button[contains(text(), 'Got it')]",
        "//div[contains(@class, 'dismiss-button')]",
        "//ytcp-dialog//ytcp-button"
    ]
    
    found_any = False
    # Check multiple times with small delay to catch popups that appear after a few seconds
    for _ in range(3):
        for selector in popups_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for el in elements:
                    if el.is_displayed():
                        print(f"Closing YouTube Studio popup: {selector}")
                        try: el.click()
                        except: driver.execute_script("arguments[0].click();", el)
                        found_any = True
            except:
                pass
        if found_any:
            time.sleep(1)
            found_any = False # Continue checking for others
        time.sleep(1)

def wait_for_processing(driver, wait, cancel_check=None):
    """
    Waits for the video upload/processing to complete before publishing.
    Looks for positive status text in the dialog.
    This function will wait as long as necessary for the video to upload,
    making it safe for slow connections.
    """
    print("Waiting for video upload to complete...")
    max_wait = 7200  # Wait up to 2 hours for extremely slow connections / large files
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if cancel_check and cancel_check():
            print("Upload cancelled by user.")
            return False
            
        try:
            # First, check if there's any active upload percentage that is NOT 100%
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            
            # If we see "uploading" or "subiendo" but NOT "100%", we MUST wait.
            is_uploading = ("uploading" in page_text or "subiendo" in page_text)
            is_100_percent = ("100%" in page_text)
            
            if is_uploading and not is_100_percent:
                print("Still uploading... waiting.")
                time.sleep(5)
                continue
                
            # If we got here, either there is no "uploading" text, or it reached 100%.
            # Now we look for explicit success strings in the status area.
            status_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'progress-label') or contains(@class, 'status-text') or contains(@class, 'left-section')]")
            
            for el in status_elements:
                text = el.text.lower()
                
                # These keywords guarantee the .mp4 file is fully transferred to YouTube's servers.
                # YouTube might still be "processing" it (HD/4K), but we can safely proceed.
                finished_keywords = [
                    "checks complete", "comprobaciones finalizadas", "no issues found", "comprobaciones terminadas",
                    "no se han encontrado", "procesamiento finalizado", "processing complete",
                    "se completó el procesamiento", "comprobaciones listas", "check complete"
                ]
                
                # Check for uploading states (we still want to wait during "uploading" phase)
                uploading_keywords = ["subiendo", "uploading", "procesando", "processing"]
                
                status_texts = text.split('\n')
                
                for t in status_texts:
                    if any(k in t for k in finished_keywords):
                        print(f"\nUpload and Processing completed successfully! YouTube says: '{t}'")
                        time.sleep(2) # Give it an extra second to settle
                        return True
                        
                # Print current actual status occasionally for user visibility
                if int(time.time() - start_time) % 10 == 0:
                    print(f"Current Status: {status_texts[0] if status_texts else 'Waiting for status update...'}")
                    
        except Exception as e:
            if "invalid session id" in str(e).lower() or "no such window" in str(e).lower() or "not connected" in str(e).lower() or "connection refused" in str(e).lower():
                print("\nSession closed externally. Cancelling wait.")
                return False
            # Ignoring DOM errors during wait loop
            pass
            
        time.sleep(2)
    
    print("Warning: Upload wait timed out after 2 hours. Proceeding anyway.")
    return False

def upload_video_selenium(driver, video_path, title, description, tags=None, privacy_status="private", schedule_date=None, schedule_time=None, cancel_check=None):
    """
    Automates the video upload process using Selenium.
    Now uses the provided driver instance.
    """
    try:
        driver.get("https://studio.youtube.com")
        wait = WebDriverWait(driver, 60)
        
        # 0. Check if we are redirected to login
        current_url = driver.current_url
        if "accounts.google.com" in current_url:
            print("❌ Error: No se detectó sesión iniciada. Por favor, haz login en la App primero.")
            return "not_logged_in"

        # 1. Clean up potential popups that block the screen
        print("Checking for blocking popups...")
        close_studio_popups(driver)

        print("Navigating to Upload Page...")
        upload_success = False
        
        # Try primary button (The big 'Upload' icon in the middle)
        for attempt in range(3):
            try:
                # Multiple possible selectors for the upload icon/button
                upload_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='upload-icon'] | //*[@id='upload-button'] | //ytcp-button[@id='upload-button']")))
                upload_button.click()
                upload_success = True
                print("Primary upload button clicked.")
                break
            except Exception:
                if attempt < 2:
                    print(f"Retrying upload button detection ({attempt+1}/3)...")
                    close_studio_popups(driver)
                    time.sleep(2)
                
        if not upload_success:
            print("Fallback: Using 'Create' menu...")
            try:
                create_btn = wait.until(EC.element_to_be_clickable((By.ID, "create-icon")))
                create_btn.click()
                time.sleep(1)
                
                # Look for 'Upload' in various languages or IDs
                upload_menu_item = wait.until(EC.element_to_be_clickable((By.XPATH, 
                    "//*[@id='text-item-0'] | //*[contains(text(), 'Subir')] | //*[contains(text(), 'Upload')] | //*[contains(text(), 'Enviar')]"
                )))
                upload_menu_item.click()
                upload_success = True
            except Exception as e:
                print(f"All upload initiation methods failed: {e}")
                return False

        file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        file_input.send_keys(video_path)
        print(f"Uploading file: {video_path}")

        # Wait for Details page
        time.sleep(5)
        
        # Meta Entry
        try:
            print("Setting metadata...")
            # Title
            try:
                title_box = wait.until(EC.presence_of_element_located((By.ID, "title-textarea")))
                title_box = title_box.find_element(By.ID, "textbox")
                safe_send_keys(driver, title_box, title)
            except:
                print("Fallback title entry...")
                boxes = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
                safe_send_keys(driver, boxes[0], title)
            
            # Description
            try:
                desc_box = driver.find_element(By.ID, "description-textarea")
                desc_box = desc_box.find_element(By.ID, "textbox")
                safe_send_keys(driver, desc_box, description)
            except:
                print("Fallback description entry...")
                boxes = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
                if len(boxes) > 1:
                    safe_send_keys(driver, boxes[1], description)
            
            print("Metadata typed.")
        except Exception as e:
            print(f"Error setting metadata: {e}")

        # Select "Not made for kids" (Required for 'Next' button)
        try:
            print("Selecting 'Not made for kids'...")
            kids_radio = wait.until(EC.presence_of_element_located((By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK")))
            driver.execute_script("arguments[0].click();", kids_radio)
            time.sleep(1)
        except Exception as e:
            print("Not made for kids radio button not found or already set.")

        if cancel_check and cancel_check(): return False

        # Wait for actual processing to advance enough
        if wait_for_processing(driver, wait, cancel_check=cancel_check) == False and cancel_check and cancel_check():
            return False

        # Cycle through 'Next' buttons
        for i in range(3):
            print(f"Clicking Next ({i+1}/3)...")
            next_btn = wait.until(EC.element_to_be_clickable((By.ID, "next-button")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            time.sleep(0.5)
            try:
                next_btn.click()
            except:
                driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(2) # Wait for tab transition animation

        # Visibility / Schedule
        print(f"Setting visibility... ({privacy_status})")
        if privacy_status == "schedule" and schedule_date and schedule_time:
             print(f"Scheduling requested for {schedule_date} at {schedule_time}")
             
             # YouTube changed the DOM. ID: schedule-section-header
             try:
                 print("Looking for Schedule section...")
                 schedule_tab = None
                 try:
                     schedule_tab = wait.until(EC.element_to_be_clickable((By.ID, "schedule-section-header")))
                 except:
                     # Fallback to text search
                     els = driver.find_elements(By.XPATH, "//*[text()='Programar' or text()='Schedule' or contains(text(), 'Programar') or contains(text(), 'Schedule')]")
                     for el in els:
                         if el.is_displayed():
                             schedule_tab = el
                             break
                 
                 if schedule_tab:
                     try: schedule_tab.click()
                     except: driver.execute_script("arguments[0].click();", schedule_tab)
                     print("Schedule section expanded.")
                 else:
                     print("❌ Could not find Schedule section header.")
                 
             except Exception as e:
                 print(f"Error expanding Schedule tab: {e}")
             
             time.sleep(1)
             
             # Date Picker
             try:
                 print("Setting Date...")
                 date_container = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='datepicker-trigger'] | //*[contains(@class, 'datepicker')]")))
                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_container)
                 time.sleep(0.5)
                 
                 # Predict language from wrapper text before interacting
                 current_date_val = driver.execute_script("return arguments[0].innerText || arguments[0].textContent;", date_container)
                 try:
                     d_parts = schedule_date.split("/")
                     if len(d_parts) == 3:
                         d, m, y = int(d_parts[0]), int(d_parts[1]), int(d_parts[2])
                         es_m = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
                         en_m = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                         
                         # Robust detection: check for any month name (case-insensitive) in current_date_val
                         current_val_lower = current_date_val.lower() if current_date_val else ""
                         is_english = any(en.lower() in current_val_lower for en in en_m)
                         is_spanish = any(es.lower() in current_val_lower for es in es_m)
                         
                         if is_english or not is_spanish: # Default to English if unsure
                             schedule_date = f"{en_m[m-1]} {d:02d}, {y}"
                         else:
                             schedule_date = f"{d:02d} {es_m[m-1]} {y}"
                         print(f"Reformatted date for YouTube Locale: {schedule_date} (Based on '{current_date_val}')")
                 except Exception as e:
                     print(f"Date formatting fallback due to: {e}")
                 
                 # 1. Focus the Date input via click (calendar opens)
                 driver.execute_script("arguments[0].click();", date_container)
                 time.sleep(0.5)
                 
                 from selenium.webdriver.common.action_chains import ActionChains
                 actions = ActionChains(driver)
                 
                 # 2. Select internal text and clear safely
                 actions.send_keys(Keys.END).perform()
                 actions.send_keys(Keys.BACKSPACE * 20).perform()
                 time.sleep(0.5)
                 
                 # 3. Type Date instantly (avoids OS clipboard permission issues)
                 actions.send_keys(schedule_date).perform()
                 time.sleep(0.5)
                 
                 # 4. Press TAB to lock the Date value
                 actions.send_keys(Keys.TAB).perform()
                 time.sleep(0.5)
                 
                 print("Setting Time...")
                 # The Time input is notoriously difficult to hook.
                 # Strategy: Find ALL the picker containers on the page, and the Time box is always index 1 (the second one)
                 elements = driver.find_elements(By.XPATH, "//tp-yt-paper-input[.//input]")
                 
                 time_container = None
                 # Check if we got at least 2 inputs (Date and Time are usually rendered together)
                 if len(elements) >= 2:
                     # Attempt to find the one that specifically handles time (often the second main input wrapper in this context)
                     # Or iterate to find the one *after* the date.
                     for el in elements:
                         html_content = el.get_attribute('outerHTML').lower()
                         if 'hora' in html_content or 'time' in html_content or 'time-of-day' in html_content:
                             time_container = el
                             break
                     
                     if not time_container:
                         # Fallback to just grabbing the second one on screen if labels are completely obfuscated
                         time_container = elements[1]
                 else:
                     # Absolute worst case fallback if DOM is bizarrely minimal
                     time_container = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input)[last()]")))
                     
                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", time_container)
                 time.sleep(0.5)
                 
                 # 1. Click specifically on the Time input to open the dropdown
                 driver.execute_script("arguments[0].click();", time_container)
                 time.sleep(1)
                 
                 # 2. Find the actual native <input> tag hidden inside the Polymer wrapper
                 time_input = time_container.find_element(By.TAG_NAME, "input")
                 
                 # 3. Clear Time text by sending backspaces directly to the input field
                 time_input.send_keys(Keys.END)
                 for _ in range(10):
                     time_input.send_keys(Keys.BACKSPACE)
                 time.sleep(0.5)
                 
                 # 4. Type Time char-by-char slowly so YouTube validates the dropdown filter
                 for char in schedule_time:
                     time_input.send_keys(char)
                     time.sleep(0.1)
                 time.sleep(0.5)
                 
                 # 5. Press ENTER to explicitly confirm the dropdown selection, then ESCAPE
                 time_input.send_keys(Keys.ENTER)
                 time.sleep(0.5)
                 actions.send_keys(Keys.ESCAPE).perform()
                 time.sleep(1)
                 
             except Exception as e:
                 print(f"Error setting date/time: {e}")
        elif privacy_status == "public":
             public_radio = wait.until(EC.element_to_be_clickable((By.NAME, "PUBLIC")))
             public_radio.click()
        else:
             private_radio = wait.until(EC.element_to_be_clickable((By.NAME, "PRIVATE")))
             private_radio.click()

        # FINAL BUTTON: Search by ID first, then by common text
        print("Clicking Final Button...")
        try:
            done_btn = wait.until(EC.element_to_be_clickable((By.ID, "done-button")))
            done_btn.click()
        except:
            # Fallback for text-based click
            print("Fallback final button click by text...")
            btns = driver.find_elements(By.XPATH, "//ytcp-button")
            found = False
            for b in btns:
                txt = b.text.lower()
                if any(k in txt for k in ["programar", "schedule", "listo", "done", "publicar", "publish", "guardar", "save"]):
                    if b.is_displayed():
                        try: b.click()
                        except: driver.execute_script("arguments[0].click();", b)
                        found = True
                        break
            if not found:
                print("❌ Could not find final button by text either.")
        
        print("Successfully uploaded. Waiting for final confirmation...")
        time.sleep(5)
        return True

    except Exception as e:
        print(f"Upload Fail: {e}")
        return False
