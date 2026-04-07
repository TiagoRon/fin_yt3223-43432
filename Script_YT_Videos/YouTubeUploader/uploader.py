import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_driver():
    """
    Initializes Chrome driver with a persistent user profile.
    This allows the user to log in once and keep the session.
    """
    chrome_options = Options()
    
    # Path to the persistent profile directory
    # We use a local folder 'chrome_profile' in the current working directory
    current_dir = os.getcwd()
    profile_dir = os.path.join(current_dir, "chrome_profile")
    
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
        
    chrome_options.add_argument(f"user-data-dir={profile_dir}")
    
    # Standard options to avoid detection issues (though not guaranteed)
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Stability options to prevent crashes (GPU errors, session invalid)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def find_element_by_any(wait, strategies):
    """
    Tries to find an element using a list of (By, value) tuples.
    Returns the element if found, or raises TimeoutException if none work.
    """
    last_exception = None
    for by, value in strategies:
        try:
            element = wait.until(EC.element_to_be_clickable((by, value)))
            return element
        except Exception as e:
            last_exception = e
            continue
    raise last_exception

def safe_send_keys(driver, element, text):
    """
    Robust text entry. Tries:
    1. Click + Ctrl-A + Backspace + SendKeys
    2. JavaScript with input event dispatching
    """
    try:
        # Method 1: Human-like interaction
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        element.click()
        time.sleep(0.5)
        
        # Clear using keyboard shortcuts (more reliable for custom inputs)
        from selenium.webdriver.common.keys import Keys
        element.send_keys(Keys.CONTROL + "a")
        time.sleep(0.2)
        element.send_keys(Keys.BACK_SPACE)
        time.sleep(0.2)
        
        element.send_keys(text)
        time.sleep(0.5)
        
        # Verify if text stuck (optional, simple check)
        if element.text.strip() == "":
            raise Exception("Text not set via keyboard")
            
    except Exception as e:
        print(f"Standard typing failed ({e}), trying advanced JS...")
        try:
            # Method 2: JS with event dispatch (needed for React/Angular/Polymer)
            driver.execute_script("""
                var params = arguments[0];
                var text = arguments[1];
                params.innerText = text;
                params.textContent = text;
                params.dispatchEvent(new Event('input', { bubbles: true }));
                params.dispatchEvent(new Event('change', { bubbles: true }));
            """, element, text)
        except Exception as js_e:
             print(f"JS injection also failed: {js_e}")

def upload_video_selenium(driver, file_path, title, description, tags, privacy_status="private"):
    """
    Automates the YouTube upload process using Selenium.
    """
    try:
        wait = WebDriverWait(driver, 60)
        
        # ... (Navigation logic remains the same, skipping to Fill Details) ...
        # [We assume navigation is handled by previous steps content, focusing on Fill Details here]
        # Re-adding the navigation logic truncated in replacement to keep file valid if needed, 
        # but the tool replaces chunks. 
        # CAUTION: The replacement chunk must match the target content exactly.
        # I need to target specifically the safe_send_keys and the Fill Details section.
        
        # Since I cannot see the full file state perfectly after multiple edits, I will target safe_send_keys 
        # up to the end of Description setting to be safe.
        pass # Logic handled in replacement content below
        
    except Exception:
        pass 
        
# [ACTUAL REPLACEMENT CONTENT]
# Note: I am replacing `safe_send_keys` and the "Fill Details" section.

def safe_send_keys(driver, element, text):
    """
    Robust text entry. Tries:
    1. Click + Ctrl-A + Backspace + SendKeys
    2. JavaScript with input event dispatching
    """
    try:
        # Method 1: Human-like interaction
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        element.click()
        time.sleep(0.5)
        
        # Clear using keyboard shortcuts
        from selenium.webdriver.common.keys import Keys
        element.send_keys(Keys.CONTROL + "a")
        time.sleep(0.2)
        element.send_keys(Keys.BACK_SPACE)
        time.sleep(0.2)
        
        element.send_keys(text)
        
    except Exception as e:
        print(f"Standard typing failed ({e}), trying advanced JS...")
        try:
            # Method 2: JS with event dispatch
            driver.execute_script("""
                var elm = arguments[0];
                var txt = arguments[1];
                elm.innerText = txt;
                elm.dispatchEvent(new Event('input', { bubbles: true }));
                elm.dispatchEvent(new Event('change', { bubbles: true }));
            """, element, text)
        except Exception as js_e:
             print(f"JS injection also failed: {js_e}")

def upload_video_selenium(driver, file_path, title, description, tags, privacy_status="private", schedule_date=None, schedule_time=None):
    # ... (Keep existing navigation code, only replace from start of function down to description) ...
    # This might be too large for a single replace if I don't match exactly.
    # Let's replace just safe_send_keys first, then the call sites if needed. 
    # Actually, the user says "no pone titulo". The selectors might be finding the wrong element?
    # The xpath //div[@id='title-textarea']//div[@contenteditable='true'] is usually correct.
    
    # I will replace safe_send_keys definition.
    pass

# REAL PLAN:
# 1. Update safe_send_keys
# 2. Update the "Fill Details" block to use improved selectors/logic if needed.


def safe_click(driver, element):
    """
    Tries to click normally. If that fails, uses JavaScript.
    """
    try:
        element.click()
    except Exception as e:
        print(f"Standard click failed ({e}), trying JS click...")
        driver.execute_script("arguments[0].click();", element)

def upload_video_selenium(driver, file_path, title, description, tags, privacy_status="private"):
    """
    Automates the YouTube upload process using Selenium.
    """
    try:
        wait = WebDriverWait(driver, 60) # Increased timeout significantly
        
        # 2. Go to Upload Page directly
        print("Navigating to Upload Page...")
        # Using the direct URL is more reliable than clicking buttons
        driver.get("https://studio.youtube.com/channel/UC/videos/upload?d=ud")
        
        # Check if we are logged in.
        time.sleep(5)
        if "accounts.google.com" in driver.current_url:
            print("Please log in to your Google Account in the browser window.")
            while "accounts.google.com" in driver.current_url:
                time.sleep(2)
            print("Login detected! Proceeding...")
            # Navigate again to ensure we are on the upload page
            driver.get("https://studio.youtube.com/channel/UC/videos/upload?d=ud")

        # Attempt to close any "Welcome" or "Feature" popups
        try:
            print("Checking for popups...")
            close_popups = driver.find_elements(By.ID, "close-icon")
            for btn in close_popups:
                if btn.is_displayed():
                    btn.click()
            time.sleep(1)
        except:
            pass

        # 3. Upload File
        print(f"Uploading file: {file_path}")
        # Wait for file input - the direct URL should load the dialog immediately
        try:
            file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
            file_input.send_keys(file_path)
        except Exception as e:
            print(f"File input not found immediately: {e}")
            print("Trying to click 'Create' as fallback...")
            # Fallback to manual navigation if direct URL failed to load dialog
            try:
                create_button = find_element_by_any(wait, [
                    (By.ID, "create-icon"),
                    (By.CSS_SELECTOR, "#create-icon"),
                    (By.XPATH, "//*[text()='Create']")
                ])
                safe_click(driver, create_button)
                time.sleep(1)
                upload_button = find_element_by_any(wait, [
                    (By.ID, "text-item-0"),
                    (By.XPATH, "//*[text()='Upload videos']")
                ])
                safe_click(driver, upload_button)
                
                file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
                file_input.send_keys(file_path)
            except Exception as e2:
                print(f"Fallback failed too: {e2}")
                return False
        
        # Wait for the upload dialog to appear
        print("Waiting for upload dialog...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//ytcp-uploads-dialog")))

        # 4. Fill Details
        # Title
        print("Setting Title...")
        try:
            # Wait for any content to load
            time.sleep(5) 
            
            # 1. Try Specific Selectors
            try:
                title_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='title-textarea']//div[@contenteditable='true']")))
                safe_send_keys(driver, title_box, title)
                print("Set Title via ID.")
            except:
                print("Specific Title ID failed. Searching for ANY text box...")
                # 2. Generic Fallback: Find ALL contenteditable divs
                text_boxes = driver.find_elements(By.XPATH, "//div[@contenteditable='true']")
                print(f"Found {len(text_boxes)} text boxes.")
                
                if len(text_boxes) > 0:
                    # Usually 0 is Title, 1 is Description
                    print("Writing to first text box (Title)...")
                    safe_send_keys(driver, text_boxes[0], title)
                else:
                    raise Exception("No text boxes found in dialog!")

        except Exception as e:
            print(f"Failed to set title: {e}")
            # Dump HTML specifically here to debug this step
            with open("debug_title_fail.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        
        # Description
        print("Setting Description...")
        try:
            # Try specific first
            try:
                desc_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='description-textarea']//div[@contenteditable='true']")))
                safe_send_keys(driver, desc_box, description)
            except:
                # Fallback to second box
                text_boxes = driver.find_elements(By.XPATH, "//div[@contenteditable='true']")
                if len(text_boxes) > 1:
                    print("Writing to second text box (Description)...")
                    safe_send_keys(driver, text_boxes[1], description)
                
        except Exception as e:
            print(f"Failed to set description: {e}")
        
        # Audience - "No, it's not made for kids"
        print("Setting Audience...")
        try:
            not_kids_radio = wait.until(EC.element_to_be_clickable((By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK")))
            not_kids_radio.click()
        except:
             # Try finding by ID/XPath if name fails
             driver.find_element(By.ID, "VIDEO_MADE_FOR_KIDS_NOT_MFK").click()

        # 5. Next Steps
        print("Clicking Next (Checks)...")
        next_button = wait.until(EC.element_to_be_clickable((By.ID, "next-button")))
        next_button.click()
        
        # Video Elements
        print("Clicking Next (Video Elements)...")
        time.sleep(2) 
        next_button.click()
        
        # Checks
        print("Clicking Next (Checks)...")
        time.sleep(2)
        next_button.click()
        
def upload_video_selenium(driver, file_path, title, description, tags, privacy_status="private", schedule_date=None, schedule_time=None):
    """
    Automates the YouTube upload process using Selenium.
    privacy_status: 'private', 'public', 'unlisted', or 'schedule'
    """
    try:
        wait = WebDriverWait(driver, 60) # Increased timeout significantly
        
        # ... (Navigation and Details steps assumed untouched by this chunk replacement) ...

        # [SKIP TO VISIBILITY SECTION - We assume Step 1-5 logic is above]
        
        # NOTE: Replacing the visibility section and function end
        # CAUTION: I need to replace from "Setting Visibility" downwards
        pass

# [ACTUAL REPLACEMENT CONTENT]
# Re-implementing from Step 6 downwards

        # 6. Visibility
        print(f"Setting Visibility to {privacy_status}...")
        
        if privacy_status.lower() == "schedule":
            # Click Schedule Radio Button
            try:
                # Usually the radio button for schedule is named 'SCHEDULE' or found by text
                schedule_strategies = [
                    (By.NAME, "SCHEDULE"),
                    (By.XPATH, "//tp-yt-paper-radio-button[@name='SCHEDULE']"),
                    (By.XPATH, "//*[text()='Schedule' or text()='Programar']")
                ]
                schedule_radio = find_element_by_any(wait, schedule_strategies)
                # Scroll to it
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", schedule_radio)
                time.sleep(1)
                schedule_radio.click()
                print("Clicked Schedule.")
                
                # Wait for date/time inputs to appear
                time.sleep(2)
                
                # SET DATE
                if schedule_date:
                    print(f"Setting Date: {schedule_date}")
                    # Usually input type="text" inside a datepicker
                    try:
                        # Find the input that has a placeholder like 'Enter date' or similar, 
                        # or specifically inside the datepicker element.
                        # Common selector:
                        date_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@class, 'tp-yt-paper-input')]"))) 
                        # This selector is vague, better be specific if possible.
                        # Often the first input in the schedule section is date, second is time.
                        
                        # Let's find inputs inside the schedule container
                        schedule_container = driver.find_element(By.ID, "schedule-radio-button")
                        # Actually 'schedule-radio-button' might be just the radio.
                        # Let's check for "datepicker-trigger" or similar
                        
                        # Robust: Find the input that holds the date.
                        # Usually it has an initial value of today/tomorrow.
                        # Let's try finding by placeholder or just the first text input available in the visibility step *after* clicking schedule.
                        
                        # Assuming date is the first input, time is the second in that section.
                        inputs = driver.find_elements(By.XPATH, "//div[@id='step-visibility']//input[@type='text']")
                        # There might be others (links etc). 
                        
                        # Using specific datepicker element
                        date_input = driver.find_element(By.XPATH, "//ytcp-date-picker//input")
                        safe_send_keys(driver, date_input, schedule_date)
                        # Press Enter to close calendar if it popups
                        from selenium.webdriver.common.keys import Keys
                        date_input.send_keys(Keys.ENTER)
                        time.sleep(1)
                        print("Date set.")
                    except Exception as e:
                        print(f"Failed to set date: {e}")

                # SET TIME
                if schedule_time:
                    print(f"Setting Time: {schedule_time}")
                    try:
                        # Time picker input
                        time_input = driver.find_element(By.XPATH, "//ytcp-time-of-day-picker//input")
                        safe_send_keys(driver, time_input, schedule_time)
                        time_input.send_keys(Keys.ENTER)
                        time.sleep(1)
                        print("Time set.")
                    except Exception as e:
                        print(f"Failed to set time: {e}")

            except Exception as e:
                print(f"Failed to Select Schedule: {e}")
                # Fallback to private if scheduling fails
                print("Falling back to Private...")
                driver.find_element(By.NAME, "PRIVATE").click()

        else:
            # Normal Privacy (Private, Public, Unlisted)
            try:
                # Strategies for finding the privacy radio button
                priv_upper = privacy_status.upper()
                privacy_strategies = [
                    (By.NAME, priv_upper),
                    (By.XPATH, f"//tp-yt-paper-radio-button[@name='{priv_upper}']"),
                    (By.XPATH, f"//*[@name='{priv_upper}']"),
                    # Fallback to text label
                    (By.XPATH, f"//*[text()='Private' or text()='Privado']" if priv_upper == 'PRIVATE' else f"//*[text()='{privacy_status}']") 
                ]
                
                privacy_radio = find_element_by_any(wait, privacy_strategies)
                privacy_radio.click()
                
            except Exception as e:
                print(f"Could not click specific visibility '{privacy_status}': {e}")
                try:
                    print("Clicking first radio button as fallback (usually Private)...")
                    driver.find_element(By.XPATH, "//tp-yt-paper-radio-button").click()
                except:
                    pass
        
        # 7. Publish/Save (Button text changes to "Schedule" if scheduled)
        print("Publishing/Scheduling...")
        done_button = wait.until(EC.element_to_be_clickable((By.ID, "done-button")))
        done_button.click()
        
        # Wait for completion
        print("Waiting for completion...")
        time.sleep(5)
        
        try:
            close_button = wait.until(EC.element_to_be_clickable((By.ID, "close-button")))
            close_button.click()
        except:
            print("Could not find close button, possibly checking copyright or processing...")
        
        print("Upload Process Finished!")
        return True

    except Exception as e:
        print(f"Selenium Upload Error: {e}")
        # Take screenshot for debug if possible (saved to local dir)
        try:
             driver.save_screenshot("debug_error.png")
             print("Saved debug_error.png")
             with open("debug_page.html", "w", encoding="utf-8") as f:
                 f.write(driver.page_source)
             print("Saved debug_page.html")
        except:
             pass
        return False
