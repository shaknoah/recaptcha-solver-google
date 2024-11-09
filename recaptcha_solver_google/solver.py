import os
import urllib.request
import random
import time
import platform
import zipfile
import tarfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydub import AudioSegment
import speech_recognition as sr


class RecaptchaSolver:
    def __init__(self, driver):
        self.driver = driver
        self.ffmpeg_path = self.ensure_ffmpeg()

    def ensure_ffmpeg(self):
        """
    Ensure FFmpeg is available, downloading it if necessary.
    """
        ffmpeg_path = os.path.join("/tmp", "ffmpeg")
        
        # Check if FFmpeg is already in the system PATH
        ffmpeg_in_path = os.system("where ffmpeg") == 0 or os.system("which ffmpeg") == 0
        
        if ffmpeg_in_path:
            print("FFmpeg is already installed in the system PATH.")
            return None  # Return None to indicate no need to download

        # Check if FFmpeg is in the temporary directory
        if os.path.exists(ffmpeg_path) and os.path.exists(os.path.join(ffmpeg_path, "ffprobe")):
            print("FFmpeg is already installed in the temporary directory.")
            return ffmpeg_path

        print("FFmpeg not found. Downloading FFmpeg...")
        system = platform.system().lower()
        
        # Define download URLs based on the OS
        ffmpeg_urls = {
            "windows": "https://ffmpeg.org/releases/ffmpeg-release-full.7z",  # Use 7z for Windows
            "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz",
            "darwin": "https://evermeet.cx/ffmpeg/getrelease/zip"  # For macOS
        }
        ffmpeg_url = ffmpeg_urls.get(system)
        
        # Download and extract FFmpeg if URL available for this OS
        if ffmpeg_url:
            os.makedirs(ffmpeg_path, exist_ok=True)
            ffmpeg_archive = os.path.join(ffmpeg_path, "ffmpeg.7z" if system == "windows" else "ffmpeg.tar.xz" if system == "linux" else "ffmpeg.zip")
            
            # Download FFmpeg
            try:
                urllib.request.urlretrieve(ffmpeg_url, ffmpeg_archive)
            except Exception as e:
                print(f"Error downloading FFmpeg: {e}")
                return None
            
            # Unzip or untar based on the system type
            if system == "linux":
                os.system(f"tar -xJf {ffmpeg_archive} -C {ffmpeg_path} --strip-components=1")
            elif system == "windows":
                os.system(f"7z x {ffmpeg_archive} -o{ffmpeg_path}")  # Make sure 7z is installed
            elif system == "darwin":
                os.system(f"unzip -o {ffmpeg_archive} -d {ffmpeg_path}")  # Use -o to overwrite without prompt
                
            print("FFmpeg downloaded and extracted successfully.")
        else:
            raise Exception("FFmpeg auto-download is not available for this OS. Please install FFmpeg manually.")

        # Set pydub to use downloaded FFmpeg binaries
        AudioSegment.ffmpeg = os.path.join(ffmpeg_path, "ffmpeg")
        AudioSegment.ffprobe = os.path.join(ffmpeg_path, "ffprobe")
        
        return ffmpeg_path



    def solve_captcha(self):
        """
        Solve the reCAPTCHA using audio recognition.
        """
        try:
            WebDriverWait(self.driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )
        except Exception as e:
            raise Exception(f"reCAPTCHA iframe not found: {e}")

        time.sleep(0.1)

        checkbox = self.driver.find_element(By.CLASS_NAME, 'rc-anchor-content')
        checkbox.click()
        self.driver.switch_to.default_content()
        time.sleep(1)

        try:
            audio_challenge_frame = WebDriverWait(self.driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@title, 'recaptcha')]"))
            )
        except Exception as e:
            raise Exception(f"Audio challenge iframe not found: {e}")

        try:
            audio_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, 'recaptcha-audio-button'))
            )
            audio_button.click()
            time.sleep(2)
        except Exception as e:
            raise Exception(f"Audio button click failed: {e}")

        for attempt in range(3):
            if self.process_audio_captcha():
                print(f"Successfully solved the CAPTCHA on attempt {attempt + 1}")
                return True
            else:
                print(f"Attempt {attempt + 1} failed. Requesting a new CAPTCHA audio.")
                self.request_new_captcha()

        raise Exception("Failed to solve the CAPTCHA after multiple attempts")

    def process_audio_captcha(self):
        """
        Process the audio CAPTCHA by downloading the audio, converting to text, and submitting the solution.
        """
        try:
            src = self.driver.find_element(By.ID, 'audio-source').get_attribute('src')
            audio_file = self.download_audio_file(src)
            audio_text = self.convert_audio_to_text(audio_file)
            audio_response = self.driver.find_element(By.ID, 'audio-response')
            audio_response.send_keys(audio_text.lower())
            time.sleep(0.1)
            verify_button = self.driver.find_element(By.ID, 'recaptcha-verify-button')
            verify_button.click()
            time.sleep(2)
            return self.is_solved()
        except Exception as e:
            print(f"Error processing audio CAPTCHA: {e}")
            return False

    def download_audio_file(self, src):
        path_to_mp3 = os.path.join("/tmp/", f"{random.randrange(1, 1000)}.mp3")
        path_to_wav = os.path.join("/tmp/", f"{random.randrange(1, 1000)}.wav")
        urllib.request.urlretrieve(src, path_to_mp3)
        sound = AudioSegment.from_mp3(path_to_mp3)
        sound.export(path_to_wav, format="wav")
        return path_to_wav

    def convert_audio_to_text(self, audio_file):
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                print(f"Processed audio text: {text}")
                return text
            except sr.UnknownValueError:
                print("Could not understand the audio.")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
        
        return ""

    def request_new_captcha(self):
        try:
            reload_button = self.driver.find_element(By.ID, 'recaptcha-reload-button')
            reload_button.click()
            time.sleep(2)
        except Exception as e:
            print(f"Failed to request new CAPTCHA: {e}")

    def is_solved(self):
        try:
            self.driver.switch_to.default_content()
            WebDriverWait(self.driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )
            self.driver.find_element(By.CLASS_NAME, 'recaptcha-checkbox-checkmark')
            return True
        except:
            return False
# Main script
def solve_captcha_for_google_recaptcha(driver):
    """
    Takes a Selenium WebDriver instance (driver) and attempts to solve the CAPTCHA.
    """
    solver = RecaptchaSolver(driver)
    try:
        if solver.solve_captcha():
            print("CAPTCHA solved successfully.")
        else:
            print("Failed to solve the CAPTCHA.")
    except Exception as e:
        print(f"Error during CAPTCHA solving: {e}")

if __name__ == "__main__":
    driver = webdriver.Chrome()
    driver.get("https://www.google.com/recaptcha/api2/demo")

    # Call the solve_captcha_with_driver function with the current driver
    solve_captcha_for_google_recaptcha(driver)
    
    driver.quit()
