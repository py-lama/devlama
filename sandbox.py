#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import tempfile
import shutil
import logging
import time
import traceback
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Union
from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

# Common imports that will be added to the sandbox environment
COMMON_IMPORTS = """
# Standard library imports
import sys
import traceback
import importlib.util
from typing import Dict, Any, Optional, Tuple, List, Union

# Dependency mapping from import name to PyPI package name
DEPENDENCY_MAP = {
    # Web and Browser Automation
    'selenium': 'selenium',
    'selenium.webdriver': 'selenium',
    'webdriver_manager': 'webdriver-manager',
    'pyautogui': 'pyautogui',
    'playwright': 'playwright',
    
    # Data Analysis
    'numpy': 'numpy',
    'pandas': 'pandas',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'scipy': 'scipy',
    'sklearn': 'scikit-learn',
    'tensorflow': 'tensorflow',
    'torch': 'torch',
    'keras': 'keras',
    
    # Web Development
    'flask': 'flask',
    'django': 'django',
    'fastapi': 'fastapi',
    'requests': 'requests',
    'aiohttp': 'aiohttp',
    'bs4': 'beautifulsoup4',
    'lxml': 'lxml',
    
    # Utilities
    'dotenv': 'python-dotenv',
    'PIL': 'pillow',
    'yaml': 'pyyaml',
    'dateutil': 'python-dateutil',
    'pytz': 'pytz',
    'tqdm': 'tqdm',
}

# Initialize package availability dictionary
PACKAGE_AVAILABILITY = {}

# Try to import common packages and check their availability
for pkg in DEPENDENCY_MAP.keys():
    try:
        # Convert package name to main module name (e.g., bs4.BeautifulSoup -> bs4)
        main_pkg = pkg.split('.')[0]
        if main_pkg not in PACKAGE_AVAILABILITY:
            importlib.import_module(main_pkg)
            PACKAGE_AVAILABILITY[main_pkg] = True
    except ImportError:
        PACKAGE_AVAILABILITY[main_pkg] = False

# Add HAS_* flags for commonly used packages
for pkg in ['selenium', 'pyautogui', 'pandas', 'numpy', 'tensorflow', 'torch']:
    has_pkg = PACKAGE_AVAILABILITY.get(pkg, False)
    globals()['HAS_' + pkg.upper()] = has_pkg


def get_chrome_options(headless: bool = True):
    """Configure Chrome options for Selenium.

    Args:
        headless (bool): Whether to run Chrome in headless mode

    Returns:
        Options: Configured Chrome options
    """
    options = Options()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return options


def install_package(package_name: str) -> bool:
    """Install a Python package using pip.

    Args:
        package_name (str): Name of the package to install

    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except Exception as e:
        print("Failed to install " + package_name + ": " + str(e), file=sys.stderr)
        return False

def ensure_dependencies(import_names: Union[str, list]) -> bool:
    """Ensure that the specified packages are available, installing them if necessary.

    Args:
        import_names (Union[str, list]): Single import name or list of import names

    Returns:
        bool: True if all dependencies are available or successfully installed
    """

    if isinstance(import_names, str):
        import_names = [import_names]
    
    all_available = True
    
    for import_name in import_names:
        main_pkg = import_name.split('.')[0]
        
        # Check if already available
        if PACKAGE_AVAILABILITY.get(main_pkg, False):
            continue
            
        # Try to import to verify
        try:
            importlib.import_module(main_pkg)
            PACKAGE_AVAILABILITY[main_pkg] = True
            continue
        except ImportError:
            pass
            
        # Try to install the package
        pypi_name = DEPENDENCY_MAP.get(import_name)
        if not pypi_name:
            pypi_name = DEPENDENCY_MAP.get(main_pkg, main_pkg)
            
        print(f"Installing required package: {pypi_name}")
        if install_package(pypi_name):
            try:
                importlib.import_module(main_pkg)
                PACKAGE_AVAILABILITY[main_pkg] = True
                print(f"Successfully installed and imported {main_pkg}")
            except ImportError:
                print(
                    f"Failed to import {main_pkg} after installation",
                    file=sys.stderr
                )
                all_available = False
        else:
            all_available = False
    
    return all_available

# Web automation utilities
if PACKAGE_AVAILABILITY.get('selenium', False):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    if PACKAGE_AVAILABILITY.get('webdriver_manager', False):
        from webdriver_manager.chrome import ChromeDriverManager
    
    def init_webdriver(headless: bool = True, max_retries: int = 3) -> webdriver.Chrome:
        """Initialize and return a Selenium WebDriver instance with retry logic.
        
        Args:
            headless: Whether to run the browser in headless mode
            max_retries: Maximum number of retry attempts
        
        Returns:
            WebDriver: Configured WebDriver instance
        
        Raises:
            RuntimeError: If WebDriver initialization fails after all retries
        """
        if not ensure_dependencies(['selenium']):
            raise ImportError("Selenium is required but could not be installed.")
        
        options = get_chrome_options(headless)
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f'Initializing WebDriver (attempt {attempt}/{max_retries})')
                
                if PACKAGE_AVAILABILITY.get('webdriver_manager', False):
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                else:
                    driver = webdriver.Chrome(options=options)
                
                # Set reasonable timeouts
                driver.set_page_load_timeout(30)
                driver.set_script_timeout(30)
                driver.implicitly_wait(10)
                
                logger.info('WebDriver initialized successfully')
                return driver
                
            except Exception as e:
                last_error = e
                logger.warning(f'WebDriver initialization attempt {attempt} failed: {str(e)}')
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        error_msg = f'Failed to initialize WebDriver after {max_retries} attempts: {str(last_error)}'
        logger.error(error_msg)
        raise RuntimeError(error_msg) from last_error
    
    def take_screenshot(driver: webdriver.Chrome, path: Optional[str] = None) -> str:
        """Take a screenshot of the current browser window.
        
        Args:
            driver: Selenium WebDriver instance
            path: Path to save the screenshot. If None, saves to a timestamped file in ~/.pylama/screenshots
            
        Returns:
            str: Absolute path where the screenshot was saved
            
        Raises:
            ValueError: If the provided path has an invalid extension
            RuntimeError: If the screenshot cannot be saved
        """
        try:
            if path:
                # Ensure the path has a .png extension
                if not path.lower().endswith('.png'):
                    raise ValueError("Screenshot path must have a .png extension")
                
                # Convert to absolute path and create directories
                abs_path = os.path.abspath(path)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            else:
                # Use default directory in user's home folder
                screenshot_dir = os.path.expanduser('~/.pylama/screenshots')
                os.makedirs(screenshot_dir, exist_ok=True)
                
                # Generate filename with timestamp and random string for uniqueness
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
                filename = f'screenshot_{timestamp}_{random_str}.png'
                abs_path = os.path.join(screenshot_dir, filename)
            
            logger.debug(f'Attempting to save screenshot to: {abs_path}')
            
            # Take the screenshot
            driver.save_screenshot(abs_path)
            
            # Verify the screenshot was saved
            if not os.path.exists(abs_path):
                raise RuntimeError(f'Screenshot file was not created at {abs_path}')
                
            file_size = os.path.getsize(abs_path)
            if file_size == 0:
                os.remove(abs_path)  # Clean up empty file
                raise RuntimeError('Screenshot file is empty')
                
            logger.info(f'Screenshot saved successfully: {abs_path} ({file_size} bytes)')
            return abs_path
            
        except Exception as e:
            error_msg = f'Error taking screenshot: {str(e)}'
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
    
    def capture_webpage_screenshot(url: str, output_path: Optional[str] = None, 
                                   wait_time: int = 5, max_retries: int = 2) -> str:
        """Capture a screenshot of a webpage with retry logic.
        
        Args:
            url: URL of the webpage to capture
            output_path: Path to save the screenshot. If None, a default path is used
            wait_time: Seconds to wait for the page to load before taking the screenshot
            max_retries: Maximum number of retry attempts
            
        Returns:
            str: Absolute path where the screenshot was saved
            
        Raises:
            ValueError: If the URL is invalid
            RuntimeError: If the screenshot cannot be captured after all retries
        """
        if not url or not isinstance(url, str) or not url.startswith(('http://', 'https://')):
            raise ValueError(f'Invalid URL: {url}')
        
        driver = None
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f'Capture attempt {attempt}/{max_retries} for {url}')
                
                # Initialize WebDriver
                driver = init_webdriver()
                
                # Navigate to the URL
                logger.debug(f'Loading URL: {url}')
                driver.get(url)
                
                # Wait for the page to load
                logger.debug(f'Waiting {wait_time} seconds for page to load')
                time.sleep(wait_time)
                
                # Take the screenshot
                screenshot_path = take_screenshot(driver, output_path)
                logger.info(f'Successfully captured screenshot: {screenshot_path}')
                return screenshot_path
                
            except Exception as e:
                last_error = e
                logger.warning(f'Attempt {attempt} failed: {str(e)}')
                
                # Clean up failed attempt
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = None
                    
                if attempt < max_retries:
                    retry_delay = wait_time * 2  # Exponential backoff
                    logger.info(f'Retrying in {retry_delay} seconds...')
                    time.sleep(retry_delay)
                    
        # If we get here, all attempts failed
        error_msg = f'Failed to capture screenshot after {max_retries} attempts: {str(last_error)}'
        logger.error(error_msg)
        raise RuntimeError(error_msg) from last_error
        
        finally:
            # Ensure driver is always closed
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.warning(f'Error closing WebDriver: {str(e)}')
            raise ImportError("Selenium is required but could not be installed.")
        
        options = get_chrome_options(headless)
        last_error = None
        
    Raises:
        ValueError: If the provided path has an invalid extension
        RuntimeError: If the screenshot cannot be saved
    """
    try:
        if path:
            # Ensure the path has a .png extension
            if not path.lower().endswith('.png'):
                raise ValueError("Screenshot path must have a .png extension")
            
            # Convert to absolute path and create directories
            abs_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        else:
            # Use default directory in user's home folder
            screenshot_dir = os.path.expanduser('~/.pylama/screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # Generate filename with timestamp and random string for uniqueness
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
            filename = f'screenshot_{timestamp}_{random_str}.png'
            abs_path = os.path.join(screenshot_dir, filename)
        
        logger.debug(f'Attempting to save screenshot to: {abs_path}')
        
        # Take the screenshot
        driver.save_screenshot(abs_path)
        
        # Verify the screenshot was saved
        if not os.path.exists(abs_path):
            raise RuntimeError(f'Screenshot file was not created at {abs_path}')
            
        file_size = os.path.getsize(abs_path)
        if file_size == 0:
            os.remove(abs_path)  # Clean up empty file
            raise RuntimeError('Screenshot file is empty')
            
        logger.info(f'Screenshot saved successfully: {abs_path} ({file_size} bytes)')
        return abs_path
        
    except Exception as e:
        error_msg = f'Error taking screenshot: {str(e)}'
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

def capture_webpage_screenshot(url: str, output_path: Optional[str] = None, 
                             wait_time: int = 5, max_retries: int = 2) -> str:
    """Capture a screenshot of a webpage with retry logic.
    
    Args:
        url: URL of the webpage to capture
        output_path: Path to save the screenshot. If None, a default path is used
        wait_time: Seconds to wait for the page to load before taking the screenshot
        max_retries: Maximum number of retry attempts
        
    Returns:
        str: Absolute path where the screenshot was saved
        
    Raises:
        ValueError: If the URL is invalid
        RuntimeError: If the screenshot cannot be captured after all retries
    """
    if not url or not isinstance(url, str) or not url.startswith(('http://', 'https://')):
        raise ValueError(f'Invalid URL: {url}')
    
    driver = None
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f'Capture attempt {attempt}/{max_retries} for {url}')
            
            # Initialize WebDriver
            driver = init_webdriver()
            
            # Navigate to the URL
            logger.debug(f'Loading URL: {url}')
            driver.get(url)
            
            # Wait for the page to load
            logger.debug(f'Waiting {wait_time} seconds for page to load')
            time.sleep(wait_time)
            
            # Take the screenshot
            screenshot_path = take_screenshot(driver, output_path)
            logger.info(f'Successfully captured screenshot: {screenshot_path}')
            return screenshot_path
            
        except Exception as e:
            last_error = e
            logger.warning(f'Attempt {attempt} failed: {str(e)}')
            
            # Clean up failed attempt
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
                
            if attempt < max_retries:
                retry_delay = wait_time * 2  # Exponential backoff
                logger.info(f'Retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
                
    # If we get here, all attempts failed
    error_msg = f'Failed to capture screenshot after {max_retries} attempts: {str(last_error)}'
    logger.error(error_msg)
    raise RuntimeError(error_msg) from last_error
    
    finally:
        # Ensure driver is always closed
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f'Error closing WebDriver: {str(e)}')

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sandbox.log')
    ]
)

logger = logging.getLogger('sandbox_docker')

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()


class DockerSandbox:
    """Klasa do uruchamiania kodu w bezpiecznym środowisku Docker."""

    def __init__(self, headless: bool = True):
        """Inicjalizacja środowiska sandbox.
        
        Args:
            headless: Czy uruchamiać przeglądarkę w trybie bezgłowym (domyślnie: True)
        """
        self.docker_image = os.getenv('DOCKER_IMAGE', 'python:3.9-slim')
        self.container_name = os.getenv('DOCKER_CONTAINER_NAME', 'pylama-sandbox')
        self.docker_port = os.getenv('DOCKER_PORT', '11434')
        self.log_dir = os.path.abspath(os.getenv('LOG_DIR', './logs'))
        self.output_dir = os.path.abspath(os.getenv('OUTPUT_DIR', './output'))
        self.headless = headless
        
        # Upewnij się, że katalogi istnieją
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Sprawdź, czy Docker jest zainstalowany
        self._check_docker_installation()
        
        # Konfiguracja WebDrivera
        self._setup_webdriver()
        
        logger.info(f"Zainicjalizowano DockerSandbox (image: {self.docker_image}, headless: {self.headless})")

        # Upewnij się, że katalogi istnieją
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # Sprawdź, czy Docker jest zainstalowany
        self._check_docker_installation()

    def _check_docker_installation(self) -> None:
        """Sprawdza, czy Docker jest zainstalowany i dostępny."""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )

            if result.returncode != 0:
                logger.error("Docker nie jest prawidłowo zainstalowany.")
                logger.error(f"Błąd: {result.stderr}")
                raise RuntimeError("Docker nie jest zainstalowany lub dostępny.")

            logger.info(f"Docker zainstalowany: {result.stdout.strip()}")
        except FileNotFoundError:
            logger.error("Docker nie jest zainstalowany lub nie jest dostępny w ścieżce systemowej.")
            raise RuntimeError("Docker nie jest zainstalowany.")

    def is_container_running(self) -> bool:
        """Sprawdza, czy kontener Docker jest już uruchomiony."""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Names}}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )

            return self.container_name in result.stdout
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania stanu kontenera: {e}")
            return False

    def start_container(self) -> bool:
        """Uruchamia kontener Docker z Ollama, jeśli nie jest już uruchomiony."""
        if self.is_container_running():
            logger.info(f"Kontener '{self.container_name}' już działa.")
            return True

        logger.info(f"Uruchamianie kontenera '{self.container_name}'...")

        try:
            # Najpierw sprawdź, czy obrazu nie trzeba pobrać
            result = subprocess.run(
                ['docker', 'image', 'inspect', self.docker_image],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )

            if result.returncode != 0:
                logger.info(f"Pobieranie obrazu Docker '{self.docker_image}'...")
                pull_result = subprocess.run(
                    ['docker', 'pull', self.docker_image],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    text=True
                )
                logger.info(f"Obraz Docker pobrany: {self.docker_image}")

            # Uruchom kontener
            run_result = subprocess.run(
                [
                    'docker', 'run',
                    '--name', self.container_name,
                    '-d',  # Uruchom w tle
                    '-p', f'{self.docker_port}:11434',  # Przekierowanie portu
                    '--rm',  # Usuń kontener po zatrzymaniu
                    '-v', f'{os.path.abspath(self.output_dir)}:/output',  # Montowanie katalogu wyjściowego
                    self.docker_image
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )

            if run_result.returncode != 0:
                logger.error(f"Błąd podczas uruchamiania kontenera: {run_result.stderr}")
                return False

            # Daj kontenerowi czas na uruchomienie
            logger.info("Czekanie na uruchomienie kontenera...")
            time.sleep(5)

            # Sprawdź czy faktycznie działa
            if self.is_container_running():
                logger.info(f"Kontener '{self.container_name}' uruchomiony pomyślnie.")
                return True
            else:
                logger.error("Kontener nie uruchomił się poprawnie.")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"Błąd podczas uruchamiania kontenera Docker: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd: {e}")
            return False

    def stop_container(self) -> bool:
        """Zatrzymuje kontener Docker, jeśli jest uruchomiony."""
        if not self.is_container_running():
            logger.info(f"Kontener '{self.container_name}' nie jest uruchomiony.")
            return True

        logger.info(f"Zatrzymywanie kontenera '{self.container_name}'...")

        try:
            result = subprocess.run(
                ['docker', 'stop', self.container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )

            logger.info(f"Kontener '{self.container_name}' zatrzymany.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Błąd podczas zatrzymywania kontenera: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd: {e}")
            return False

    def _setup_webdriver(self):
        """Konfiguruje WebDrivera do użycia w kontenerze."""
        self.chrome_options = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--disable-extensions',
            '--disable-software-rasterizer',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-zygote',
            '--single-process',
            '--disable-notifications',
        ]
        
        if self.headless:
            self.chrome_options.append('--headless')
    
    def _get_docker_run_command(self, command: str) -> List[str]:
        """Tworzy komendę do uruchomienia w kontenerze Docker."""
        cmd = [
            'docker', 'exec',
            '-e', 'PYTHONUNBUFFERED=1',
            '-e', f'DISPLAY=:99',
            '-w', '/app',
            self.container_name
        ]
        
        if isinstance(command, str):
            cmd.extend(['sh', '-c', command])
        else:
            cmd.extend(command)
            
        return cmd
    
    def _install_dependencies_in_container(self):
        """Instaluje wymagane zależności w kontenerze."""
        logger.info("Instalowanie zależności w kontenerze...")
        
        # Aktualizacja pakietów i instalacja wymaganych zależności systemowych
        commands = [
            'apt-get update',
            'apt-get install -y wget gnupg2 unzip xvfb \
                libxss1 libappindicator1 libindicator7 fonts-liberation \
                libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 \
                libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 \
                libnss3 libx11-xcb1 libxcb-dri3-0 libxcomposite1 \
                libxdamage1 libxext6 libxfixes3 libxrandr2 libxshmfence1',
            'wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -',
            'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list',
            'apt-get update',
            'apt-get install -y google-chrome-stable',
            'pip install --upgrade pip',
            'pip install selenium webdriver-manager pyautogui pillow',
            'mkdir -p /app/output',
            'chmod -R 777 /app/output'
        ]
        
        for cmd in commands:
            try:
                subprocess.run(
                    self._get_docker_run_command(cmd),
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=300
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Błąd podczas instalacji zależności: {e.stderr.decode()}")
                raise
    
    def execute_code(self, code: str, timeout: int = 300) -> Tuple[bool, str, str]:
        """Wykonuje kod Pythona w kontenerze Docker.

        Args:
            code: Kod Python do wykonania
            timeout: Limit czasu wykonania w sekundach (domyślnie 300s)
            
        Returns:
            Krotka (sukces, stdout, stderr)
        """
        # Przygotuj kod do wykonania
        chrome_options_str = ' '.join([f'"{opt}"' for opt in self.chrome_options])
        
        wrapped_code = f"""
import sys
import os
import traceback
from pathlib import Path

# Dodaj katalog wyjściowy do ścieżki
sys.path.append('/app')

# Ustaw zmienne środowiskowe
os.environ['DISPLAY'] = ':99'
os.environ['PYTHONUNBUFFERED'] = '1'

# Uruchom Xvfb w tle
import subprocess
xvfb_process = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24'])
try:
    # Importy
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    import pyautogui
    
    # Konfiguracja opcji Chrome
    options = Options()
    for opt in [{chrome_options_str}]:
        options.add_argument(opt)
    
    # Inicjalizacja WebDrivera
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Błąd podczas inicjalizacji WebDrivera: {e}")
        driver = webdriver.Chrome(options=options)
    
    # Uruchom kod użytkownika
    try:
        # Kod użytkownika
        {code}
        
        # Jeśli wykonanie dotarło tutaj, zakładamy sukces
        sys.exit(0)
    except Exception as e:
        print(f"Błąd podczas wykonywania kodu: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            driver.quit()
        except:
            pass
finally:
    # Zakończ proces Xvfb
    xvfb_process.terminate()
    xvfb_process.wait()
"""

        # Przygotuj katalog tymczasowy
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, 'script.py')
            
            # Zapisz skrypt do pliku
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(wrapped_code)
            
            # Uruchom kontener, jeśli nie jest uruchomiony
            if not self.is_container_running():
                self.start_container()
            
            try:
                # Skopiuj skrypt do kontenera
                subprocess.run(
                    ['docker', 'cp', script_path, f"{self.container_name}:/app/script.py"],
                    check=True
                )
                
                # Wykonaj skrypt w kontenerze
                result = subprocess.run(
                    self._get_docker_run_command('python script.py'),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout
                )
                
                # Zapisz logi
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                log_file = os.path.join(self.log_dir, f"execution-{timestamp}.log")
                
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== KOD ===\n{code}\n\n")
                    f.write(f"=== STDOUT ===\n{result.stdout}\n\n")
                    f.write(f"=== STDERR ===\n{result.stderr}\n\n")
                    f.write(f"=== STATUS ===\n{'Sukces' if result.returncode == 0 else 'Błąd'} (kod wyjścia: {result.returncode})")
                
                return result.returncode == 0, result.stdout, result.stderr
                
            except subprocess.TimeoutExpired:
                return False, "", f"Przekroczony limit czasu wykonania ({timeout}s)"
            except subprocess.CalledProcessError as e:
                return False, e.stdout or "", e.stderr or "Nieznany błąd"
            except Exception as e:
                return False, "", f"Błąd podczas wykonywania kodu: {str(e)}")
                pass

    def install_dependencies(self, packages: List[str]) -> Tuple[bool, str, str]:
        """
        Instaluje zależności w kontenerze Docker.

        Args:
            packages: Lista pakietów do zainstalowania

        Returns:
            Tuple zawierający (sukces, stdout, stderr)
        """
        if not packages:
            return True, "", ""

        if not self.is_container_running():
            if not self.start_container():
                return False, "", "Nie udało się uruchomić kontenera Docker."

        try:
            packages_str = ' '.join(packages)
            install_cmd = f"pip install {packages_str}"

            run_result = subprocess.run(
                [
                    'docker', 'exec',
                    self.container_name,
                    'bash', '-c', install_cmd
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
                timeout=180  # Dłuższy timeout dla instalacji pakietów
            )

            success = run_result.returncode == 0
            stdout = run_result.stdout
            stderr = run_result.stderr

            # Zapisz logi
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            log_file = os.path.join(self.log_dir, f"pip-install-{timestamp}.log")

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== INSTALACJA PAKIETÓW ===\n{packages_str}\n\n")
                f.write(f"=== STDOUT ===\n{stdout}\n\n")
                f.write(f"=== STDERR ===\n{stderr}\n\n")
                f.write(f"=== STATUS ===\n{'Sukces' if success else 'Błąd'} (kod wyjścia: {run_result.returncode})")

            if success:
                logger.info(f"Pakiety zainstalowane pomyślnie: {packages_str}")
            else:
                logger.error(f"Błąd podczas instalacji pakietów: {stderr}")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            return False, "", "Przekroczony limit czasu instalacji pakietów (180s)"
        except Exception as e:
            logger.error(f"Błąd podczas instalacji pakietów: {e}")
            return False, "", str(e)

    def pull_ollama_model(self, model_name: str) -> Tuple[bool, str, str]:
        """
        Pobiera model Ollama w kontenerze Docker.

        Args:
            model_name: Nazwa modelu do pobrania

        Returns:
            Tuple zawierający (sukces, stdout, stderr)
        """
        if not self.is_container_running():
            if not self.start_container():
                return False, "", "Nie udało się uruchomić kontenera Docker."

        try:
            run_result = subprocess.run(
                [
                    'docker', 'exec',
                    self.container_name,
                    'ollama', 'pull', model_name
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
                timeout=600  # Dłuższy timeout dla pobierania modelu (10 minut)
            )

            success = run_result.returncode == 0
            stdout = run_result.stdout
            stderr = run_result.stderr

            # Zapisz logi
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            log_file = os.path.join(self.log_dir, f"ollama-pull-{model_name}-{timestamp}.log")

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== POBIERANIE MODELU ===\n{model_name}\n\n")
                f.write(f"=== STDOUT ===\n{stdout}\n\n")
                f.write(f"=== STDERR ===\n{stderr}\n\n")
                f.write(f"=== STATUS ===\n{'Sukces' if success else 'Błąd'} (kod wyjścia: {run_result.returncode})")

            if success:
                logger.info(f"Model '{model_name}' pobrany pomyślnie.")
            else:
                logger.error(f"Błąd podczas pobierania modelu '{model_name}': {stderr}")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            return False, "", f"Przekroczony limit czasu pobierania modelu '{model_name}' (600s)"
        except Exception as e:
            logger.error(f"Błąd podczas pobierania modelu: {e}")
            return False, "", str(e)


# Przykład użycia
if __name__ == "__main__":
    sandbox = DockerSandbox()

    try:
        # Uruchom kontener
        if not sandbox.start_container():
            sys.exit(1)

        # Testowy kod Python
        test_code = """
import os
import platform
import sys

print("=== Informacje o środowisku ===")
print(f"Python: {sys.version}")
print(f"Platforma: {platform.platform()}")
print(f"Katalogi: {os.listdir('/')}")
print("=== Koniec ===")
"""

        # Wykonaj kod
        success, stdout, stderr = sandbox.execute_code(test_code)

        print("\n=== Wyniki testu ===")
        print(f"Sukces: {success}")
        print(f"STDOUT:\n{stdout}")

        if stderr:
            print(f"STDERR:\n{stderr}")

    finally:
        # Zatrzymaj kontener
        sandbox.stop_container()