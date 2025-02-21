import os
import pathlib
import time
import pyperclip  # Added import
from platform import system
from urllib.parse import quote
from webbrowser import open

import requests
from pyautogui import click, hotkey, press, size

from pywhatkit.core.exceptions import InternetException

WIDTH, HEIGHT = size()


def check_number(number: str) -> bool:
    """Checks the Number to see if contains the Country Code"""
    return "+" in number or "_" in number


def close_tab(wait_time: int = 2) -> None:
    """Closes the Currently Opened Browser Tab"""
    time.sleep(wait_time)
    if system().lower() in ("windows", "linux"):
        hotkey("ctrl", "w")
    elif system().lower() == "darwin":
        hotkey("command", "w")
    else:
        raise Warning(f"{system().lower()} not supported!")
    press("enter")


def check_connection() -> None:
    """Check the Internet connection of the Host Machine"""
    try:
        requests.get("https://google.com")
    except requests.RequestException:
        raise InternetException(
            "Error while connecting to the Internet. Make sure you are connected to the Internet!"
        )


def _web(receiver: str, message: str) -> None:
    """Opens WhatsApp Web based on the Receiver"""
    if check_number(number=receiver):
        open(
            "https://web.whatsapp.com/send?phone="
            + receiver
            + "&text="
            + quote(message)
        )
    else:
        open("https://web.whatsapp.com/accept?code=" + receiver)  # Removed extra quote


def send_message(message: str, receiver: str, wait_time: int = 10) -> None:
    """Optimized message sending with reduced delays"""
    _web(receiver=receiver, message=message)
    time.sleep(5)  # Reduced initial wait for page load
    click(WIDTH / 2, HEIGHT / 2)
    time.sleep(2)  # Reduced wait for chat box focus
    
    # Clipboard-based message handling
    pyperclip.copy(message)
    _paste_content()
    time.sleep(1)  # Short wait before sending
    press("enter")


def _paste_content() -> None:
    """Universal paste command with platform detection"""
    time.sleep(0.5)
    if system().lower() == "darwin":
        hotkey("command", "v")
    else:
        hotkey("ctrl", "v")
    time.sleep(1)  # Ensure paste completes


def copy_image(path: str) -> None:
    """Copy the Image to Clipboard based on the Platform"""
    if system().lower() == "linux":
        if pathlib.Path(path).suffix in (".PNG", ".png"):
            os.system(f"copyq copy image/png - < {path}")
        elif pathlib.Path(path).suffix in (".jpg", ".JPG", ".jpeg", ".JPEG"):
            os.system(f"copyq copy image/jpeg - < {path}")
        else:
            raise Exception(
                f"File Format {pathlib.Path(path).suffix} is not Supported!"
            )
    elif system().lower() == "windows":
        from io import BytesIO
        import win32clipboard
        from PIL import Image

        image = Image.open(path)
        output = BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
    elif system().lower() == "darwin":
        if pathlib.Path(path).suffix in (".jpg", ".jpeg", ".JPG", ".JPEG"):
            os.system(
                f"osascript -e 'set the clipboard to (read (POSIX file \"{path}\") as JPEG picture)'"
            )
        else:
            raise Exception(
                f"File Format {pathlib.Path(path).suffix} is not Supported!"
            )
    else:
        raise Exception(f"Unsupported System: {system().lower()}")


def send_image(path: str, caption: str, receiver: str, wait_time: int = 10) -> None:
    """Optimized image sending with reduced delays"""
    _web(message=caption, receiver=receiver)
    time.sleep(5)  # Reduced initial wait for page load
    click(WIDTH / 2, HEIGHT / 2)
    time.sleep(2)  # Reduced wait for chat box focus
    
    # Handle caption with clipboard
    if caption:
        pyperclip.copy(caption)
        _paste_content()
        time.sleep(1)  # Short wait between operations
    
    # Handle image paste
    copy_image(path=path)
    _paste_content()
    time.sleep(1)  # Short wait before sending
    press("enter")