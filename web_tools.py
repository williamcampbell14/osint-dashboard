import http.cookiejar
import urllib.request
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen
from urllib import parse, robotparser, request
import requests
import ipinfo
from dotenv import load_dotenv
import dns.resolver
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from concurrent.futures import ThreadPoolExecutor
import socket
import os
import re

# for screenshot
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def findTitle(url, timeout=10):
    try:
        cookiejar = http.cookiejar.CookieJar()

        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookiejar))
        urllib.request.install_opener(opener)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=timeout) as response:
            html_content = response.read().decode('utf-8')
            return html_content.split('<title>')[1].split('</title>')[0]
    except (IndexError, urllib.error.HTTPError):
        return ""
    except socket.timeout:
        return ""


def get_favicon(domain):
    return 'https://icon.horse/icon/' + domain


def website_information(website):
    title = findTitle(website)
    parsed_url = urlparse(website)
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]

    ip_addresses = [res[4][0] for res in socket.getaddrinfo(domain, 80)]
    # Choosing the first IP address from the list
    ip_address = ip_addresses[0]
    favicon_link = get_favicon(domain)
    return (domain, ip_address, title, favicon_link)


def get_redirects(url, max_redirects=10, timeout=10):
    redirects = []
    for _ in range(max_redirects):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(
                url, allow_redirects=False, timeout=timeout, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {'Error': f'Failed to fetch URL: {e}'}
        if 300 <= response.status_code < 400:
            redirects.append(url)

            url = response.headers['Location']
        else:
            break

    return {'Redirected From': redirects, 'Final URL': url}


def get_cookies(domain, timeout=5):
    try:
        response = requests.get(domain, timeout=timeout)
        cookies = response.cookies
        cookies_dict = {cookie.name: cookie.value for cookie in cookies}
        return cookies_dict

    except requests.exceptions.Timeout as e:
        return {'Error': f'Timeout error: {e}'}
    except requests.exceptions.RequestException as e:
        return {'Error': f'Failed to fetch URL: {e}'}


def get_headers(domain, timeout=5):
    try:
        response = requests.get(domain, timeout=timeout)
        headers = response.headers
        headers_dict = {header: value for header, value in headers.items()}
        return headers_dict
    except requests.exceptions.Timeout as e:
        return {'Error': f'Timeout error: {e}'}
    except requests.exceptions.RequestException as e:
        return {'Error': f'Failed to fetch URL: {e}'}


load_dotenv()
ipinfo_api_key = os.getenv('IPINFO_API_KEY')


def get_ip_info(ip_address):
    try:
        handler = ipinfo.getHandler(ipinfo_api_key)

        details = handler.getDetails(ip_address)
        return (details.all)
    except ValueError as e:
        return {'Error': f'{e}'}


def get_records(domain):
    results = {}
    record_types = ['NONE', 'A', 'NS', 'MD', 'MF', 'CNAME', 'SOA', 'MB', 'MG', 'MR', 'NULL', 'WKS', 'PTR', 'HINFO', 'MINFO', 'MX', 'TXT', 'RP', 'AFSDB', 'X25', 'ISDN', 'RT', 'NSAP', 'NSAP-PTR', 'SIG', 'KEY', 'PX', 'GPOS', 'AAAA', 'LOC', 'NXT', 'SRV', 'NAPTR', 'KX', 'CERT', 'A6',
                    'DNAME', 'OPT', 'APL', 'DS', 'SSHFP', 'IPSECKEY', 'RRSIG', 'NSEC', 'DNSKEY', 'DHCID', 'NSEC3', 'NSEC3PARAM', 'TLSA', 'HIP', 'CDS', 'CDNSKEY', 'CSYNC', 'SPF', 'UNSPEC', 'EUI48', 'EUI64', 'TKEY', 'TSIG', 'IXFR', 'AXFR', 'MAILB', 'MAILA', 'ANY', 'URI', 'CAA', 'TA', 'DLV']

    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            results[record_type] = [rdata.to_text() for rdata in answers]
        except dns.resolver.NoAnswer:
            pass
        except dns.resolver.NXDOMAIN:
            pass
        except Exception as e:
            continue

    return results


def get_ssl(hostname, port=443):
    context = ssl.create_default_context()
    conn = context.wrap_socket(socket.socket(
        socket.AF_INET, socket.SOCK_STREAM), server_hostname=hostname)
    conn.connect((hostname, port))

    certs = conn.getpeercert(True)
    certificate = x509.load_der_x509_certificate(certs, default_backend())
    subject = next((attr.value for attr in certificate.subject if attr.oid ==
                   x509.NameOID.COMMON_NAME), None)
    issuer = next((attr.value for attr in certificate.issuer if attr.oid ==
                  x509.NameOID.ORGANIZATION_NAME), None)
    certificate_info = {
        "subject": subject,
        "issuer": issuer,
        "serial_number": certificate.serial_number,
        "not_valid_before": certificate.not_valid_before.isoformat(),
        "not_valid_after": certificate.not_valid_after.isoformat()
    }
    return certificate_info


def get_sitemaps(website, timeout=5):
    robotstxturl = parse.urljoin(website, "robots.txt")
    sitemaps = []
    try:
        socket.setdefaulttimeout(timeout)
        rp = robotparser.RobotFileParser()
        rp.set_url(robotstxturl)
        rp.read()
        sitemaps = rp.site_maps()
    except error.URLError as e:
        if isinstance(e.reason, socket.timeout):
            print(f"Timeout Error: {e}")
        else:
            print(f"URLError: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        socket.setdefaulttimeout(None)

    return sitemaps


def sitemap_parser(sitemap):
    try:
        r = request.urlopen(sitemap)
        xml = r.read().decode('utf8')
        elements = re.findall(r'<loc>(.*?)<\/loc>', xml, re.DOTALL)

        urls = []

        for element in elements:
            try:
                if element.endswith('.xml'):
                    # Recursively call sitemap_parser
                    urls.extend(sitemap_parser(element))
                else:
                    urls.append(element)
            except Exception as e:
                print(f"Error parsing sub-sitemap '{element}': {str(e)}")

        return urls
    except Exception as e:
        print(f"Error accessing sitemap '{sitemap}': {str(e)}")
        return []


def site_maps(url):
    sitemaps = get_sitemaps(url)
    if sitemaps is None:
        return {"Pages": []}
    all_urls = []

    for sitemap in sitemaps:
        all_urls.extend(sitemap_parser(sitemap))

    urls_dict = {"Pages": all_urls}

    return (urls_dict)


def find_open_port(hostname, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)

    result = sock.connect_ex((hostname, port))
    sock.close()

    return result == 0


def check_ports(url):
    ports_to_check = [21, 22, 23, 25, 53, 80, 110,
                      143, 443, 465, 587, 993, 995, 3306, 3389, 8080]
    open_ports = []
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda port: (
            port, find_open_port(url, port)), ports_to_check))

    for port, is_open in results:
        if is_open:
            open_ports.append(port)
    return {"Open Ports": open_ports}


def whois_info(domain):
    valid_tld = ['cc', 'com', 'edu', 'name', 'net']
    try:
        sd, tld = domain.split('.')
        if (tld not in valid_tld):
            return {'error': 'The Whois database only accepts these top level domains: .cc .com .edu .name .net '}
        url = f"https://webwhois.verisign.com/webwhois-ui/rest/whois?q={sd}&tld={tld}&type=domain"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            text = data["message"]
            lines = text.split('\n')
            domain_data = {}

            for i in range(17):
                key, value = lines[i].split(':', 1)
                # Remove leading/trailing whitespaces
                domain_data[key] = value.strip()

            return domain_data
        else:
            return {"error": f"Unable to fetch data. Status code: {response.status_code}"}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}


def get_screenshot(url):
    chrome_options = Options()
    # Run Chrome in headless mode (no GUI)
    chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)

        # Wait for some time to let the page load (adjust this according to your needs)
        driver.implicitly_wait(10)

        # Capture a screenshot and convert it to base64
        screenshot_base64 = driver.get_screenshot_as_base64()

        return {"screenshot": screenshot_base64}

    except Exception as e:
        print(f'Error: {e}')

    finally:
        # Close the WebDriver
        driver.quit()


def get_internal_external_links(url, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        base_url = urlparse(url).scheme + '://' + urlparse(url).hostname
        links = re.findall(r'href=["\'](https?://[^\s"\'<>]+)', response.text)
        internal_links = []
        external_links = []

        for link in links:
            absolute_link = urljoin(base_url, link)
            if urlparse(absolute_link).hostname == urlparse(url).hostname:
                internal_links.append(absolute_link)
            else:
                external_links.append(absolute_link)

        return {'Internal Links': internal_links, 'External Links': external_links}

    except requests.exceptions.RequestException as e:
        return {'error': f'Request error during request to {e}', 'message': 'Some sites might prohibit automated requests.'}


def get_emails(url, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        emails = re.findall(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text)
        return {'Emails': emails}

    except requests.exceptions.RequestException as e:
        return {'error': f'Request error during request to {e}', 'message': 'Some sites might prohibit automated requests.'}


def get_phone_numbers(url, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        text_content = re.sub('<.*?>', ' ', response.text)
        phone_numbers = re.findall(
            r'\b1\s?\(\d{3}\)\s?\d{3}[-.\s]?\d{4}\b', text_content)
        return {'Phone Numbers': phone_numbers}

    except requests.exceptions.RequestException as e:
        return {'error': f'Request error during request to {e}', 'message': 'Some sites might prohibit automated requests.'}
