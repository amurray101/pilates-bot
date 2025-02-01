# requirements.txt
python-dotenv==1.0.0
selenium==4.16.0
schedule==1.2.1
webdriver_manager==4.0.1

# booking_agent.py
import os
import time
import schedule
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

class WorkoutBookingAgent:
    def __init__(self):
        load_dotenv()
        self.email = os.getenv('MARIANA_EMAIL')
        self.password = os.getenv('MARIANA_PASSWORD')
        self.studio_url = os.getenv('STUDIO_URL')
        self.preferred_classes = os.getenv('PREFERRED_CLASSES').split(',')
        self.preferred_times = os.getenv('PREFERRED_TIMES').split(',')
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(ChromeDriverManager().install(), options=options)
        
    def login(self, driver):
        try:
            driver.get(self.studio_url)
            
            # Wait for login form
            wait = WebDriverWait(driver, 10)
            email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            password_field = driver.find_element(By.NAME, "password")
            
            # Enter credentials
            email_field.send_keys(self.email)
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log In')]")
            login_button.click()
            
            # Wait for successful login
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "schedule")))
            return True
            
        except TimeoutException:
            print("Login failed - timeout")
            return False
            
    def book_class(self):
        driver = self.setup_driver()
        
        try:
            if not self.login(driver):
                return
                
            # Navigate to schedule page
            schedule_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Schedule')]"))
            )
            schedule_link.click()
            
            # Look for preferred classes
            for class_name in self.preferred_classes:
                class_elements = driver.find_elements(
                    By.XPATH, 
                    f"//div[contains(@class, 'class-name') and contains(text(), '{class_name}')]"
                )
                
                for class_element in class_elements:
                    time_element = class_element.find_element(
                        By.XPATH, 
                        "./ancestor::div[contains(@class, 'class-card')]//div[contains(@class, 'time')]"
                    )
                    
                    # Check if class time matches preferred times
                    class_time = time_element.text
                    if any(preferred_time in class_time for preferred_time in self.preferred_times):
                        # Find and click book button
                        book_button = class_element.find_element(
                            By.XPATH,
                            "./ancestor::div[contains(@class, 'class-card')]//button[contains(text(), 'Book')]"
                        )
                        book_button.click()
                        
                        # Confirm booking if necessary
                        try:
                            confirm_button = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Confirm')]"))
                            )
                            confirm_button.click()
                            print(f"Successfully booked {class_name} at {class_time}")
                            return True
                        except TimeoutException:
                            print("No confirmation needed or booking failed")
                            
        except Exception as e:
            print(f"Error booking class: {str(e)}")
            
        finally:
            driver.quit()
            
        return False

def run_agent():
    agent = WorkoutBookingAgent()
    agent.book_class()

if __name__ == "__main__":
    # Schedule the agent to run daily at 7 AM
    schedule.every().day.at("07:00").do(run_agent)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
