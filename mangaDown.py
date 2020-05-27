#! python3
# download manga from kissmanga

import lxml
import  img2pdf, os, re, requests, time, zipfile
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from wand.image import Image
# Have to install ImageMagick for transparency issues - Windows: http://docs.wand-py.org/en/latest/guide/install.html#install-imagemagick-on-windows

# Use Colors for numbering (if you want).  They're commented out below
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Inverts the Chapter List from 1 - X
def invert_list(input_list):
    input_list.reverse()
    return input_list


def downloadManga(manga, manga_name, chapter_name, create_pdf, create_cbz):

    # Create a Manga Directory if one does not exist
    os.chdir(owd)
    os.makedirs("manga", exist_ok=True)
    os.chdir("manga")

    # Create the Series Directory
    base_filename = manga_name.replace("/", "-")
    os.makedirs(manga_name, exist_ok=True)

    # Download the page.
    print("Loading the Page...")
    time.sleep(3)
    browser.get(manga)

    # Find the URL of the comic image.
    print("Retrieving Images...")
    comicElem = browser.find_element_by_css_selector("#divImage")
    eles = comicElem.find_elements_by_css_selector("*")
    if comicElem == []:
        print("Could not find comic images.")
    else:
        j = 1
        file_number = 1
        for i in eles:
            if j == (len(eles) / 2) + 1:
                break
            comicUrl = i.find_element_by_xpath(
                "/html/body/div[1]/div[4]/div[11]/p[" + str(j) + "]/img"
            ).get_attribute("src")
            j += 1
            # Download the image.
            print("Downloading image %s..." % (comicUrl))
            res = requests.get(comicUrl)
            res.raise_for_status()
            imageFile = open(
                os.path.join(
                    base_filename,
                    os.path.basename(chapter_name + "-" + str(file_number) + ".jpg"),
                ),
                "wb",
            )
            file_number += 1
            for chunk in res.iter_content(100000):
                imageFile.write(chunk)
            imageFile.close()

    # Creating a pdf and catching transparency errors
    os.chdir(base_filename)
    dl_file_list = [i for i in os.listdir(".") if i.endswith(".jpg")]
    transparency_file_list = []
    transparency_failure = 0
    if create_pdf:
        while transparency_failure < 2:
            try:
                if transparency_file_list:
                    with open(chapter_name + ".pdf", "wb") as f:
                        f.write(img2pdf.convert(transparency_file_list))
                        break
                else:
                    with open(chapter_name + ".pdf", "wb") as f:
                        f.write(img2pdf.convert(dl_file_list))
                        break
            except img2pdf.AlphaChannelError:
                print("Alpha Channel Error - Converting images to remove alpha channel")
                for transparent_images in dl_file_list:
                    converted_name = transparent_images.replace('.jpg', '')+'_converted.jpg'
                    with Image(filename=transparent_images) as img:
                        img.alpha_channel = 'remove'
                        img.save(filename=converted_name)
                transparency_file_list = [p for p in os.listdir(".") if p.endswith("converted.jpg")]
                transparency_file_list.sort(key=lambda f: int(re.sub('\D', '', f)))
                transparency_failure += 1
                pass
        print(chapter_name, '.pdf created.', sep='')

    if create_cbz:
        with zipfile.ZipFile(chapter_name + ".cbz", "w") as cbz_file:
            for manga_page in dl_file_list:
                cbz_file.write(manga_page)
        print(chapter_name,'.cbz created.', sep='')

    # Delete images - need to wait for cbz and pdf to be complete to prevent permissions issues
    print("Cleaning directory...")
    time.sleep(2)
    for images in dl_file_list:
        os.remove(images)
    for converted_images in transparency_file_list:
        os.remove(converted_images)


if __name__ == "__main__":
    # Searches KissManga for Manga Series
    owd = os.getcwd()
    title = input("Enter manga name: ").replace(" ", "+")
    URL = 'https://kissmanga.com/Search/Manga?keyword=' + title

    # Creates a Headless Firefox container and waits for page load
    print("Launching Firefox silently...")
    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Firefox(options=options)
    browser.implicitly_wait(10)
    browser.get(URL)

    # You may need to adjust this sleep value to be higher if you are getting a CloudFlare/JS error.
    print("Waiting for CloudFlare verification")
    time.sleep(7)

    # Saves the page source to soup and then searches for table data
    soup = BeautifulSoup(browser.page_source, features="lxml")
    table_data = []
    for s in soup.find_all('td'):
        table_data.append(s.text)

    # Replaces escape data (Need to replace this with a dictionary replace)
    table_data = [t.replace('\n', '') for t in table_data]
    table_data = [u.replace('\xa0', '') for u in table_data]

    # Takes the Series Name instead of the latest chapter by getting evens only and prints the titles
    Series_Name = table_data[::2]
    titles = 0
    series_max = len(Series_Name)
    while titles < series_max:
        # Colored Numbers
        #print(f'{bcolors.OKBLUE}{titles + 1}{bcolors.ENDC}. {Series_Name[titles]}')
        # Non-colored Numbers
        print(titles + 1, '. ', Series_Name[titles], sep='')
        titles += 1
        # Add a check later to print only X amount of titles

    # Ensures that a valid integer is put in
    series_selection = -1
    while (series_selection <= 0) or (series_selection > series_max):
        try:
            series_selection = int(input('Please select a series: '))
        except ValueError:
            print("Please input a valid number.")

    # Pastes the Manga Series URL if you want to copy it for later
    series_url = Series_Name[series_selection - 1].replace(" ", "-")
    manga_name = Series_Name[series_selection - 1].replace(':', '')
    manga_url = 'https://kissmanga.com/Manga/' + series_url
    print(manga_url)

    # Saves the page source to chapters and then searches for table data
    print("Finding Chapters...")
    browser.get(manga_url)
    chapters = BeautifulSoup(browser.page_source, features="lxml")
    chapter_names = []
    chapter_urls = []

    # Searches for Chapter Names and saves them
    for z in chapters.find_all('td'):
        chapter_names.append(z.text)

    # Searches for Chapter URLs and saves them
    for y in chapters.find_all('td'):
        x = y.find('a')
        if x is not None:
            chapter_urls.append('https://kissmanga.com' + x['href'])

    # Inverts the Chapter URLs and prints them for selection
    chapter_urls = invert_list(chapter_urls)
    chapter_names = invert_list(chapter_names)

    # Replaces escape data (Need to replace this with a dictionary replace)
    chapter_names = [w.replace('\n', '') for w in chapter_names]
    chapter_names = [v.replace('\xa0', '') for v in chapter_names]

    # Takes the Chapter Name instead of the date by getting evens only and prints the titles
    Chapter_Names = chapter_names[1::2]
    chaps = 0
    chapter_max = len(Chapter_Names)
    while chaps < chapter_max:
        # Colored Numbers
        #print(f'{bcolors.OKGREEN}{chaps + 1}{bcolors.ENDC}. {Chapter_Names[chaps]}')
        # Non-colored Numbers
        print(chaps + 1, '. ', Chapter_Names[chaps], sep='')
        chaps += 1

    # Ensures that a valid integer is put in (Need to make sure it falls within the chapter list)
    chapter_selection = -1
    while (chapter_selection <= 0) or (chapter_selection > chapter_max):
        try:
            chapter_selection = int(input('Please select a chapter: '))
        except ValueError:
            print('Please input a valid number.')
        confirm_chap = input('Are you sure you want to download {}? [y/n]: '.format(Chapter_Names[chapter_selection - 1])).strip().lower().startswith("y")
        if confirm_chap:
            break
        else:
            chapter_selection = 0

    # Prints the Chapter URL based on your selection
    chapter_name = Chapter_Names[chapter_selection - 1].replace(':', '')
    chapter_url = chapter_urls[chapter_selection - 1]
    #print(chapter_url)

    # Creates a PDF or CBZ file
    mk_file = input("Would you like to create a cbz, pdf, or both? [pdf/cbz/both]: ").lower()
    while mk_file not in {'pdf', 'cbz', 'both'}:
        mk_file = input("Would you like to create a cbz, pdf, or both? [pdf/cbz/both]: ").lower()
    if 'cbz' in mk_file:
        mk_cbz = True
        mk_pdf = False
    elif 'pdf' in mk_file:
        mk_cbz = False
        mk_pdf = True
    elif 'both' in mk_file:
        mk_cbz = True
        mk_pdf = True
    downloadManga(chapter_url, manga_name, chapter_name, mk_pdf, mk_cbz)

    # Asks if you want to download another chapter
    another_chapter = input("Would you like to download another chapter? [y/n]: ").strip().lower().startswith("y")
    while another_chapter:
        print("Printing Chapters...")
        chaps = 0
        chapter_max = len(Chapter_Names)
        while chaps < chapter_max:
            print(chaps + 1, '. ', Chapter_Names[chaps], sep='')
            chaps += 1

        # Ensures that a valid integer is put in (Need to make sure it falls within the chapter list)
        chapter_selection = -1
        while (chapter_selection <= 0) or (chapter_selection > chapter_max):
            try:
                chapter_selection = int(input('Please select a chapter:'))
            except ValueError:
                print('Please input a valid number.')
            confirm_chap = input('Are you sure you want to download {}? [y/n]: '.format(Chapter_Names[chapter_selection - 1])).strip().lower().startswith("y")
            if confirm_chap:
                break
            else:
                chapter_selection = 0

        # Chapter Selection
        chapter_url = chapter_urls[chapter_selection-1]
        chapter_name = Chapter_Names[chapter_selection-1].replace(':', '')
        #print(chapter_url)
        time.sleep(3)

        # Downloads the new chapter
        downloadManga(chapter_url, manga_name, chapter_name, mk_pdf, mk_cbz)

        # Resets the While Loop
        another_chapter = input("Would you like to download another chapter? [Y/n] ").strip().lower().startswith("y")

    print("Thanks for using the script!")
    time.sleep(3)

    # Ends session
    browser.close()
    browser.quit()
