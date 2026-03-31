import time
import logging
import threading
import base64
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class TeamsSeleniumBot:
    """Manages Microsoft Teams interactions via Selenium with RAG integration."""
    
    def __init__(self):
        self._drivers: Dict[str, webdriver.Chrome] = {}
        self._active_threads: Dict[str, threading.Thread] = {}
        self._last_captions: Dict[str, List[Dict]] = {}
        self._locks = threading.Lock()
        
        # Pre-install ChromeDriver for faster session starts
        logger.info("Initializing Selenium Service...")
        self._service = Service(ChromeDriverManager().install())
        
    def _get_chrome_options(self, headless: bool = False) -> Options:
        """Configure Chrome for background Teams joining."""
        chrome_options = Options()
        
        # Bypass mic/camera popups
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--use-fake-device-for-media-stream")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--window-size=1280,720")
        
        if headless:
            chrome_options.add_argument("--headless=new")
            
        # Add preferences to auto-allow media
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1, 
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.notifications": 1 
        })
        
        return chrome_options

    def join_meeting(self, meeting_url: str, display_name: str = "RAG Agent", headless: bool = False) -> Dict[str, str]:
        """Start a new thread to join the meeting with thread safety."""
        session_id = f"meeting_{int(time.time())}"
        
        thread = threading.Thread(
            target=self._run_bot,
            args=(session_id, meeting_url, display_name, headless),
            daemon=True
        )
        thread.start()
        
        with self._locks:
            self._active_threads[session_id] = thread
            
        return {"session_id": session_id, "status": "joining"}

    def _run_bot(self, session_id: str, meeting_url: str, display_name: str, headless: bool):
        """Internal method to execute the Selenium script with precision clicking."""
        driver = None
        try:
            options = self._get_chrome_options(headless=headless)
            driver = webdriver.Chrome(service=self._service, options=options)
            
            with self._locks:
                self._drivers[session_id] = driver
            
            wait = WebDriverWait(driver, 20)
            logger.info(f"SeleniumBot[{session_id}]: Navigating to meeting URL...")
            driver.get(meeting_url)
            
            # Step 1: Handle "Continue on this browser"
            try:
                continue_xpath = "//button[contains(., 'Continue on this browser')] | //button[contains(@aria-label, 'Continue on this browser')]"
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, continue_xpath)))
                btn.click()
                logger.info(f"SeleniumBot[{session_id}]: [CLICK] Bypassed launcher.")
                time.sleep(3)
            except:
                logger.warning(f"SeleniumBot[{session_id}]: Continue button not found (already bypassed?).")

            # Step 2: Enter display name
            try:
                name_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Type your name'] | //input")))
                name_input.send_keys(display_name)
                logger.info(f"SeleniumBot[{session_id}]: Entered name: {display_name}")
            except Exception as e:
                logger.error(f"SeleniumBot[{session_id}]: Name input failed: {e}")

            # Step 3: Click the Final Join Button
            try:
                join_xpath = "//button[contains(@data-tid, 'prejoin-join-button')] | //button[contains(., 'Join now')]"
                join_button = wait.until(EC.element_to_be_clickable((By.XPATH, join_xpath)))
                join_button.click()
                logger.info(f"SeleniumBot[{session_id}]: Successfully Joined meeting.")
            except Exception as e:
                logger.error(f"SeleniumBot[{session_id}]: Join button click failed: {e}")

            time.sleep(10) # Wait for UI stabilization
            
            # Step 4: UI Setup (Captions & Intro)
            try:
                # 4a. Enable Captions
                logger.info(f"SeleniumBot[{session_id}]: [CLICK] Opening 'More' menu...")
                more_xpath = "//button[@id='callingButtons-showMessageMoreBtn'] | //button[contains(., 'More')]"
                more_btn = wait.until(EC.element_to_be_clickable((By.XPATH, more_xpath)))
                more_btn.click()
                time.sleep(2)
                
                logger.info(f"SeleniumBot[{session_id}]: [CLICK] Enabling Captions...")
                captions_xpath = "//div[@id='closed-captions-button'] | //div[contains(., 'Captions')]"
                captions_btn = driver.find_element(By.XPATH, captions_xpath)
                driver.execute_script("arguments[0].click();", captions_btn)
                
                # 4b. Send Intro Message
                time.sleep(2)
                intro_msg = "Hello everyone! I am the RAG Agent. I'm here to listen and help answer any questions you have about our project documents. Just ask me anything!"
                self._send_chat_message(session_id, driver, intro_msg, is_intro=True)
                    
            except Exception as e:
                logger.warning(f"SeleniumBot[{session_id}]: UI setup semi-failed (captions/intro): {e}")

            # Step 5: Start Monitoring Loop
            self._monitor_meeting(session_id, driver)
                
        except Exception as e:
            logger.error(f"SeleniumBot[{session_id}] critical error: {str(e)}")
        finally:
            self.stop_meeting(session_id)

    def _monitor_meeting(self, session_id: str, driver: webdriver.Chrome):
        """Infinite loop to scrape captions and respond."""
        last_text = ""
        logger.info(f"SeleniumBot[{session_id}]: Monitoring meeting for speech...")
        
        while session_id in self._drivers:
            try:
                # Scrape Captions (High precision for Free Version)
                caption_xpath = "//span[@data-tid='closed-caption-text'] | //div[contains(@class, 'closed-caption')]//span"
                captions = driver.find_elements(By.XPATH, caption_xpath)
                
                if captions:
                    newest_text = captions[-1].text.strip()
                    
                    # Identify speaker
                    speaker_name = "Participant"
                    try:
                        speaker_xpath = "./preceding-sibling::div | ../preceding-sibling::div"
                        speaker_el = captions[-1].find_element(By.XPATH, speaker_xpath)
                        if speaker_el.text: 
                            speaker_name = speaker_el.text.split('\n')[0]
                    except: pass

                    if newest_text and newest_text != last_text:
                        logger.info(f"Captured: {speaker_name}: {newest_text}")
                        last_text = newest_text
                        
                        with self._locks:
                            self._last_captions.setdefault(session_id, []).append({
                                "speaker": speaker_name,
                                "text": newest_text,
                                "timestamp": time.strftime("%H:%M:%S"),
                                "is_bot": False
                            })
                            if len(self._last_captions[session_id]) > 20:
                                self._last_captions[session_id].pop(0)
                        
                        # Trigger RAG Response
                        if "?" in newest_text or "bot" in newest_text.lower() or "agent" in newest_text.lower():
                            self._generate_meeting_response(session_id, driver, newest_text)
                
                time.sleep(3)
            except Exception as e:
                logger.debug(f"Monitor heartbeat: {e}")
                time.sleep(3)

    def _send_chat_message(self, session_id: str, driver: webdriver.Chrome, message: str, is_intro: bool = False):
        """Helper to open chat and send message with 'element not interactable' safety."""
        try:
            logger.info(f"SeleniumBot[{session_id}]: [CLICK] Preparing Meeting Chat...")
            chat_xpath = "//button[@id='chat-button'] | //button[contains(., 'Chat')]"
            chat_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, chat_xpath)))
            
            if chat_btn.get_attribute("aria-pressed") == "false":
                try: chat_btn.click()
                except: driver.execute_script("arguments[0].click();", chat_btn)
                time.sleep(2)

            input_xpath = "//div[@data-tid='ckeditor_nested-editable'] | //div[@role='textbox']"
            input_box = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, input_xpath)))
            
            driver.execute_script("arguments[0].focus();", input_box)
            input_box.click() 
            
            prefix = "[RAG BOT]: " if not is_intro else ""
            input_box.send_keys(f"{prefix}{message}")
            time.sleep(1)

            send_xpath = "//button[@data-tid='newMessageCommands-send'] | //button[contains(@aria-label, 'Send')]"
            send_btn = driver.find_element(By.XPATH, send_xpath)
            driver.execute_script("arguments[0].click();", send_btn)
            
            logger.info(f"SeleniumBot[{session_id}]: [SEND] Chat updated.")
        except Exception as e:
            logger.warning(f"SeleniumBot[{session_id}]: Chat send failed: {e}")

    def _generate_meeting_response(self, session_id: str, driver: webdriver.Chrome, text: str):
        """Bridge between Selenium loop and RAG Agent."""
        try:
            from .main import agent
            result = agent.ask(text)
            answer = result.get("answer", "")
            if not answer: return

            self._send_chat_message(session_id, driver, answer)

            with self._locks:
                if session_id in self._last_captions:
                    self._last_captions[session_id].append({
                        "speaker": "RAG Bot",
                        "text": answer,
                        "timestamp": time.strftime("%H:%M:%S"),
                        "is_bot": True
                    })
                    logger.info(f"SeleniumBot[{session_id}]: Dashboard sync complete.")

        except Exception as e:
            logger.error(f"RAG Bridge error: {e}")

    def stop_meeting(self, session_id: str):
        """Cleanly close a meeting session."""
        with self._locks:
            driver = self._drivers.pop(session_id, None)
            self._active_threads.pop(session_id, None)
            
        if driver:
            try:
                driver.quit()
                logger.info(f"SeleniumBot[{session_id}]: Driver closed.")
            except: pass

    def get_status(self) -> Dict:
        """Return currently active session IDs."""
        with self._locks:
            return {
                "active_sessions": list(self._drivers.keys()),
                "count": len(self._drivers)
            }

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Fetch session data for the frontend dashboard."""
        with self._locks:
            if session_id in self._drivers:
                return {
                    "call_connection_id": f"sel_{session_id}",
                    "meeting_url": "Selenium Browser Session",
                    "status": "connected",
                    "joined_at": "Active",
                    "participant_count": 1,
                    "event_count": 0,
                    "recent_events": [],
                    "transcript": self._last_captions.get(session_id, []),
                }
        return None

    def send_manual_chat(self, session_id: str, message: str):
        """Force the bot to send a specific message to the meeting chat."""
        with self._locks:
            driver = self._drivers.get(session_id)
        
        if not driver:
            raise Exception("Session not found")
            
        self._send_chat_message(session_id, driver, message, is_intro=True) # is_intro=True avoids the [RAG BOT] prefix

    def trigger_action(self, session_id: str, action: str):
        """Manually trigger a UI action from the dashboard."""
        with self._locks:
            driver = self._drivers.get(session_id)
        
        if not driver:
            raise Exception("Session not found")

        wait = WebDriverWait(driver, 5)
        if action == "chat":
            chat_xpath = "//button[@id='chat-button'] | //button[contains(., 'Chat')]"
            btn = wait.until(EC.presence_of_element_located((By.XPATH, chat_xpath)))
            driver.execute_script("arguments[0].click();", btn)
            logger.info(f"Manual Action[{session_id}]: Toggled Chat")
            
        elif action == "more":
            more_xpath = "//button[@id='callingButtons-showMessageMoreBtn'] | //button[contains(., 'More')]"
            btn = wait.until(EC.presence_of_element_located((By.XPATH, more_xpath)))
            driver.execute_script("arguments[0].click();", btn)
            logger.info(f"Manual Action[{session_id}]: Toggled More Menu")
            
        elif action == "mute":
            # Look specifically for the button when it says "Mute" (meaning it is currently active)
            mute_xpath = "//button[@id='microphone-button' and contains(@aria-label, 'Mute') and not(contains(@aria-label, 'Unmute'))]"
            try:
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, mute_xpath)))
                driver.execute_script("arguments[0].click();", btn)
                logger.info(f"Manual Action[{session_id}]: Muted")
            except:
                logger.warning(f"Manual Action[{session_id}]: Could not find Mute button (already muted?)")
                
        elif action == "unmute":
            # Look specifically for the button when it says "Unmute"
            unmute_xpath = "//button[@id='microphone-button' and contains(@aria-label, 'Unmute')]"
            try:
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, unmute_xpath)))
                driver.execute_script("arguments[0].click();", btn)
                logger.info(f"Manual Action[{session_id}]: Unmuted")
            except:
                logger.warning(f"Manual Action[{session_id}]: Could not find Unmute button (already unmuted?)")

        elif action == "captions":
            # Very aggressive search for the Captions button/menuitem
            captions_xpath = (
                "//div[@id='closed-captions-button'] | "
                "//button[contains(., 'Captions')] | "
                "//div[@role='menuitem' and contains(., 'Captions')] | "
                "//*[contains(@aria-label, 'Captions')]"
            )
            # Find all potential matches and try clicking the first visible one
            elements = driver.find_elements(By.XPATH, captions_xpath)
            clicked = False
            for el in elements:
                if el.is_displayed():
                    try:
                        driver.execute_script("arguments[0].click();", el)
                        clicked = True
                        logger.info(f"Manual Action[{session_id}]: Toggled Captions via JS")
                        break
                    except: continue
            
            if not clicked:
                # Last resort: wait and click standard
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, captions_xpath)))
                btn.click()
                logger.info(f"Manual Action[{session_id}]: Toggled Captions via standard click")

# Global instance
teams_selenium_bot = TeamsSeleniumBot()
