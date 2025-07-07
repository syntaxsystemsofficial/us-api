from flask import Flask, request, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
import time
import tempfile

app = Flask(__name__)

@app.route('/api/vin', methods=['GET'])
def get_vin_excel():
    vin = request.args.get("vin")
    if not vin:
        return {"error": "VIN not provided"}, 400

    # Temp download dir for Vercel (must be writable)
    download_dir = tempfile.mkdtemp()

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)

    try:
        # Step 1: Open VIN page
        url = f"https://vpic.nhtsa.dot.gov/decoder/Decoder?VIN={vin}&ModelYear="
        driver.get(url)

        # Step 2: Click full report
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "btnFullReport"))
        ).click()

        # Step 3: Get Export to Excel href
        export_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'ExportToExcel')]"))
        )
        href = export_link.get_attribute("href")

        # Step 4: Download Excel
        response = requests.get(href)
        if response.status_code == 200:
            file_path = os.path.join(download_dir, f"{vin}.xlsx")
            with open(file_path, "wb") as f:
                f.write(response.content)

            return send_file(
                file_path,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f"{vin}.xlsx"
            )
        else:
            return {"error": "Failed to download Excel"}, 500

    finally:
        driver.quit()
