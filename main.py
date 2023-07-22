from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from webdriver_manager.chrome import ChromeDriverManager
import requests
import sys
from dateutil.relativedelta import *
from dateutil.easter import *
from dateutil.rrule import *
from dateutil import parser
from datetime import datetime

def login(driver, strUsername, strPassword):
    driver.get("https://www.cloudlab.us/login.php")
    time.sleep(2)
    username = driver.find_element(By.XPATH, '//form[@id="quickvm_login_form"]//input[@name="uid"]')
    username.send_keys(strUsername)
    password = driver.find_element(By.XPATH, '//form[@id="quickvm_login_form"]//input[@name="password"]')
    password.send_keys(strPassword)
    btn = driver.find_element(By.XPATH, '//button[@id="quickvm_login_modal_button"]')
    btn.click()

def getUuidsOfExperiment(driver):
    rows = driver.find_elements(By.XPATH, '//div[@id="experiments"]/div[@id="experiments_content"]//table[@id="experiments_table"]/tbody/tr[@role="row"]')
    uuids = []
    if len(rows) > 0:
        print("Index      Experiment Name                                     UUID")
        for i, row in enumerate(rows):
            #print(row.get_attribute('innerHTML'))
            a = row.find_element(By.TAG_NAME, 'a')
            uuid = str(a.get_attribute("href")).split('=')[-1]
            uuids.append(uuid)
            experimentName = a.text
            print("  [%d] %20s %40s" % (i, experimentName, uuid))
        experID = int(input("Please select the experiment you want to Auto-Extend [0 - {}]: ".format(len(rows) - 1)))
        return uuids[experID]
    else:
        print("No existed experiments, quit.")
        sys.exit(0)

def getExpireTime(driver, uuid):
    driver.get('https://www.cloudlab.us/status.php?uuid={}'.format(uuid))
    time.sleep(1)
    exTime = driver.find_element(By.ID, "quickvm_expires").text
    return parser.parse(exTime)


def getSessionBySelenium(driver):
    sess = requests.Session()
    selenium_user_agent = driver.execute_script("return navigator.userAgent;")
    sess.headers.update({"user-agent": selenium_user_agent})
    for cookie in driver.get_cookies():
        sess.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
    return sess

def extendCloudlab(driver, uuid):
    payload = {
        'ajax_route': 'status',
        'ajax_method': 'RequestExtension',
        'ajax_args[uuid]': uuid,
        'ajax_args[howlong]': '168',
        'ajax_args[reason]': '111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111',
    }

    sess = getSessionBySelenium(driver)
    ret = sess.post('https://www.cloudlab.us/server-ajax.php', data=payload)
    print(ret.text)
    print("extend finish!")

def cmpAndWait(driver, uuid, remainHours=25):
    exTime = getExpireTime(chrome, uuid)
    print("------Experiment Expired Time: {}------".format(exTime))
    print("------Current Time: {}------".format(datetime.now()))
    print("------Experiment will be extended at {}------".format(exTime - relativedelta(hours=remainHours)))
    print("------OK, You can leave now------")
    while True:
        now = datetime.now()
        if now + relativedelta(hours=remainHours) > exTime:
            print('------CurrentTime: {}, Extending cloudlab...------'.format(now))
            extendCloudlab(driver, uuid)
            time.sleep(1)
            exTime = getExpireTime(chrome, uuid)
            print('------Extend Finished! Next Extend Time will be: {}------'.format(exTime - relativedelta(hours=remainHours)))
        else:
            time.sleep(1799) # sleep for 1 hour

try:
    service = Service(ChromeDriverManager().install())
except:
    service = Service("./linux64_114.0.5735.90_chromedriver/chromedriver")

options = webdriver.ChromeOptions()
options.add_argument("--disable-notifications")
options.add_argument("window-size=1920x1080")
options.add_argument("--headless")
chrome = webdriver.Chrome(service=service, options=options)

print("------PLEASE RUN THIS PROGRAM IN TMUX------")
userName = input("Enter Your Username: ")
password = input("Enter Your Password: ")
print("------STILL HAVE SOMETHING TO ENTER. DON'T LEAVE------")
login(chrome, userName, password)
time.sleep(2)
uuid = getUuidsOfExperiment(chrome)


remainHours = input("Input remain hours to extend your cloudlab, press enter to use default value (25): ")
remainHours = remainHours.strip()

if len(remainHours) > 0:
    cmpAndWait(chrome, uuid, remainHours=int(remainHours))
else:
    cmpAndWait(chrome, uuid)