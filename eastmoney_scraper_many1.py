import os
import re
import time
import shutil
import requests
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from openpyxl import Workbook


class EastmoneyReportScraper:
    def __init__(self):
        pass

    # Remove illegal characters from filename
    def sanitize_filename(self, filename):
        return re.sub(r'[\\/:*?"<>|]', '', filename)

    # Wait for download completion - look for PDF files starting with expected_prefix and not ending with .crdownload
    def wait_for_file(self, download_dir, expected_prefix, timeout=30):
        t0 = time.time()
        while True:
            for file in os.listdir(download_dir):
                if file.endswith(".pdf") and file.startswith(expected_prefix) and not file.endswith(".crdownload"):
                    return os.path.join(download_dir, file)
            if time.time() - t0 > timeout:
                break
            time.sleep(0.5)
        return None

    # Use Selenium to download PDF files, first to pdf_downloads folder then move to target folder with new name
    def download_pdf(self, pdf_url, target_folder, new_filename, count, driver, infoCode):
        try:
            expected_prefix = f"H3_{infoCode}_1"  # Expected prefix of downloaded filename
            driver.get(pdf_url)
            print(f"Downloading: {pdf_url} (File {count})")
            download_dir = os.path.abspath("pdf_downloads")

            # Wait for file download completion (adjust timeout as needed)
            downloaded_file = self.wait_for_file(download_dir, expected_prefix, timeout=30)
            if downloaded_file:
                new_path = os.path.join(target_folder, new_filename)
                os.rename(downloaded_file, new_path)
                print(f"Download successful: {new_path}")
            else:
                print(f"Download failed: {pdf_url}, corresponding file not found in {download_dir}.")
        except Exception as e:
            print(f"Exception occurred while downloading {pdf_url}: {e}")

    # Request API to get data, with parameters pageNo, pageNum, pageNumber
    def get_data_from_api(self, begin_time, end_time, page_size, page_num=1):
        url = "https://reportapi.eastmoney.com/report/list2"
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/133.0.0.0 Safari/537.36")
        }

        payload = {
            "beginTime": begin_time,
            "endTime": end_time,
            "industryCode": "*",
            "ratingChange": None,
            "rating": None,
            "orgCode": None,
            "code": "*",
            "rcode": "",
            "pageSize": page_size,
            "p": page_num,
            "pageNo": page_num,
            "pageNum": page_num,
            "pageNumber": page_num
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print("Request status code:", response.status_code)
            if response.status_code != 200:
                print("Request failed, status code:", response.status_code)
                return None
            return response.json()
        except Exception as e:
            print(f"Exception occurred while requesting API: {e}")
            return None

    # Format date
    def format_publish_date(self, date_str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
            return date_obj.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Failed to format date {date_str}:", e)
            return "unknown_date"

    # Optimize table format and save as Excel file
    def save_to_excel(self, records):
        if not records:
            print("No report data captured, no need to save Excel file.")
            return

        df = pd.DataFrame(records)

        if 'publishDate' in df.columns:
            df['publishDate'] = df['publishDate'].apply(self.format_publish_date)
        else:
            print("Missing publishDate field in records.")

        if 'publishDate' in df.columns:
            df.sort_values(by="publishDate", ascending=False, inplace=True)

        output_excel = "report_data.xlsx"
        writer = pd.ExcelWriter(output_excel, engine='openpyxl')
        df.to_excel(writer, index=False, sheet_name='Reports')

        workbook = writer.book
        worksheet = workbook['Reports']
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = max_length + 2
            worksheet.column_dimensions[column].width = adjusted_width

        writer.close()
        print(f"Data saved to: {output_excel}")

    # Configure Chrome browser options
    def configure_browser(self):
        download_dir = os.path.abspath("pdf_downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Use ChromeDriverManager to automatically manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def scrape(self, start_date, end_date, output_file, desired_count):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        records = []
        driver = self.configure_browser()

        # Create folder named with start and end dates
        folder_name = f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
        target_folder = os.path.abspath(folder_name)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        current_date = start_date
        while current_date <= end_date:
            print(f"Scraping data for {current_date.strftime('%Y-%m-%d')}...")
            begin_time_str = current_date.strftime("%Y-%m-%d")
            end_time_str = current_date.strftime("%Y-%m-%d")
            per_page = 50
            page_num = 1
            total_fetched_today = 0
            seen_infoCodes = set()

            while total_fetched_today < desired_count:
                print(f"Fetching page {page_num} data...")
                json_data = self.get_data_from_api(begin_time_str, end_time_str, per_page, page_num)
                if not json_data or "data" not in json_data:
                    print("No data obtained, exiting loop.")
                    break

                data_list = json_data["data"]
                if not data_list:
                    print("No data on current page, exiting loop.")
                    break

                for item in data_list:
                    infoCode = item.get("infoCode", "")
                    if infoCode in seen_infoCodes:
                        continue
                    seen_infoCodes.add(infoCode)

                    if total_fetched_today >= desired_count:
                        break

                    title = item.get("title", "")
                    stockName = item.get("stockName", "")
                    stockCode = item.get("stockCode", "")
                    orgName = item.get("orgName", "")
                    publishDate = item.get("publishDate", "")
                    indvInduName = item.get("indvInduName", "")

                    date_str = self.format_publish_date(publishDate)

                    timestamp = int(time.time() * 1000)
                    pdf_url = f"https://pdf.dfcfw.com/pdf/H3_{infoCode}_1.pdf?{timestamp}.pdf"

                    sanitized_title = self.sanitize_filename(title)
                    new_filename = f"{stockCode}-{sanitized_title}-{date_str}.pdf"
                    new_path = os.path.join(target_folder, new_filename)

                    if os.path.exists(new_path):
                        print(f"File {new_path} already exists, skipping download.")
                    else:
                        total_fetched_today += 1
                        self.download_pdf(pdf_url, target_folder, new_filename, total_fetched_today, driver, infoCode)

                    records.append({
                        "title": title,
                        "stockName": stockName,
                        "stockCode": stockCode,
                        "orgName": orgName,
                        "publishDate": publishDate,
                        "infoCode": infoCode,
                        "indvInduName": indvInduName,
                        "pdf_filename": new_path
                    })

                    time.sleep(1)  # Prevent too frequent requests
                page_num += 1

            current_date += timedelta(days=1)

        self.save_to_excel(records)
        driver.quit()

        download_dir = os.path.abspath("pdf_downloads")
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
            print(f"Download directory deleted: {download_dir}")


def get_eastmoney_data(start_date="2025-04-09 00:00:00", end_date="2025-04-10 00:00:00", output_file="eastmoney_report_data.xlsx",
                       desired_count=1):
    # Initialize scraper (custom cookies can be passed)
    scraper = EastmoneyReportScraper()
    scraper.scrape(start_date, end_date, output_file, desired_count=desired_count)