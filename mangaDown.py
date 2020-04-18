#! python3
# download manga from kissmanga

import requests, os, time, img2pdf
from selenium import webdriver

baseUrl = 'https://kissmanga.com/Manga/'    
os.makedirs('manga', exist_ok=True)    # store comics in ./manga

def downloadManga(mangaName):
    os.chdir('manga')
    os.makedirs(mangaName.split('/')[0], exist_ok=True) 
    # Download the page.
    print('Downloading page %s...' % baseUrl+mangaName)
    browser = webdriver.Firefox()
    browser.get(baseUrl+mangaName) #handle exceptions here
    time.sleep(15)
    
    #Find the URL of the comic image.
    comicElem = browser.find_element_by_css_selector('#divImage')
    eles = comicElem.find_elements_by_css_selector('*')
    if comicElem == []:
        print('Could not find comic images.')
    else:
        j=1
        base_filename = mangaName.split("/")[0]
        k=1
        for i in eles:
            if(j == (len(eles)/2)+1):
                break
            comicUrl = i.find_element_by_xpath('/html/body/div[1]/div[4]/div[11]/p['+str(j)+']/img').get_attribute('src')
            j = j+1
            # Download the image.
            print('Downloading image %s...' % (comicUrl))
            res = requests.get(comicUrl)
            res.raise_for_status()
            imageFile = open(os.path.join(mangaName.split('/')[0], os.path.basename(base_filename + "_" + str(k) + '.jpg')),'wb')
            k += 1
            for chunk in res.iter_content(100000):
                imageFile.write(chunk)
            imageFile.close()

    #creating a pdf
    os.chdir(mangaName.split('/')[0])
    with open(mangaName.split('/')[0]+".pdf", "wb") as f:
        f.write(img2pdf.convert([i for i in os.listdir('.') if i.endswith(".jpg")]))       
    print('Done')   

name = input('Enter manga name and chapter no. in kissmanga format: ')
#eg - Hajime-no-Ippo/Ch-1239----In-His-Hand
downloadManga(name)
