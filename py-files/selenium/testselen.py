from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://web.whatsapp.com/")

# Wait for user to scan QR code and load chats manually
input("Press Enter after scanning QR code and selecting a chat...")

# Locate the message box
message_box = driver.find_element_by_xpath(
    '//div[@contenteditable="true"][@data-testid="conversation-compose-box-input"]'
)

# Send a message
message_box.send_keys("Hello from automation!")