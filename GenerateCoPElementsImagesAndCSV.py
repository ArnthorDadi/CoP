import os
from PIL import Image
import pytesseract
import cv2 as cv
import pytesseract as tes
from langdetect import detect

def getElementText(file_name):
	img = cv.imread(file_name)
	height,width,_ = img.shape
	roi = img[0:180, 20:width]

	element_text = tes.image_to_string(roi)
	element_explanation = []
	element_name = []
	for line in element_text.split('\n'):
		try:
			if(line[0] == '(' and line[-1] == ')'):
				element_name.append(line[1:-1])
			if(detect(line) == 'en'):
				element_explanation.append(line)
		except:
			x = 1
	return [', '.join(element_name), ' '.join(element_explanation)]



def getDifficulty(col):
	elementValueLetter = 'A'
	elementValueNumber = 0.1
	if(col == 0):
		elementValueLetter = 'A'
		elementValueNumber = 0.1
	elif(col == 1):
		elementValueLetter = 'B'
		elementValueNumber = 0.2
	elif(col == 2):
		elementValueLetter = 'C'
		elementValueNumber = 0.3
	elif(col == 3):
		elementValueLetter = 'D'
		elementValueNumber = 0.4
	elif(col == 4):
		elementValueLetter = 'E'
		elementValueNumber = 0.5
	elif(col == 5):
		elementValueLetter = 'F/G/H'
		elementValueNumber = 0.6

	return [elementValueLetter, elementValueNumber]

def getGroupName(split_group_name):
	if(len(split_group_name) == 2):
		temp = []
		try:
			temp = split_group_name[0].split(".-")
			split_group_name.append(split_group_name[-1])
			split_group_name[0] = temp[0]
			split_group_name[1] = temp[1]
		except:
			temp = split_group_name[1].split(".-")
			split_group_name = [split_group_name[0], temp[0], temp[1]]

	group_name_list = []

	for line in split_group_name:
		try:
			if(detect(line.strip()) == 'en'):
				clean_line = line.replace("\n","").strip()
				group_name_list.append(clean_line)
		except:
			x = 1
	return group_name_list

def standardizeGroup(group):
	if(group == "EG I" or group == "EG " or group == "EG |"):
		group = "I"
	elif(group == "EG Il"):
		group = "II"
	elif(group == "EG Ill"):
		group = "III"
	elif(group == "EG IV"):
		group = "IV"
	return group

def getCoPPageGroup(img):
	elementGroupBox = (40, 122, 2298, 122+60)
	elementGroupImg = img.crop(elementGroupBox)

	cop_page_group_text = tes.image_to_string(elementGroupImg)
	group_and_rest = cop_page_group_text.split(":")
	group = standardizeGroup(group_and_rest[0])

	group_name_list =  getGroupName(group_and_rest[1].split(" - "))
	return [group, " ".join(group_name_list)]

def isValidFile(file_name, start_page, end_page):
	if(file_name[-4:] != ".png"):
		return False
	cop_page = int(file_name[-7:-4])
	if(cop_page < start_page or end_page < cop_page):
		return False
	return True

def createDirectoryIfNotExists(saveLocation):
	if(not os.path.isdir(saveLocation)):
		os.mkdir(saveLocation)

SEPARATOR = '|'
BASE_IMAGE_PATH = "img/cop"

APPARATUS = ["floor", "pommel-horse", "rings", "vault", "parallel-bars", "high-bar"]
APPARATUS_ELEMENT_PAGES = {
	"floor": (43, 53),
    "pommel-horse": (66, 77),
    "rings": (85, 101),
    "vault": (108, 115),
    "parallel-bars": (122, 137),
    "high-bar": (145, 161),
}

NR_OF_ROWS = 4
NR_OF_COLS = 6

START_X = 41.5
START_Y = 180
OFFSET_Y = 2
OFFSET_X = 2

WIDTH = 416 - START_X
HEIGHT = 532 - START_Y

# Setup
saveToAbsLocation = "/Users/arnthordadi/Documents/projects/routine-builder/src/assets" #input("Destination (absolute) path for images and csv: ")

if(saveToAbsLocation == ""):
	saveToAbsLocation = "."


createDirectoryIfNotExists(f"{saveToAbsLocation}/csv")

for apparatus_index, apparatus in enumerate(APPARATUS):
# 	if(apparatus != APPARATUS[3]):
# 		continue
	print(f"{apparatus_index+1}/{len(APPARATUS)}: {apparatus}")

	createDirectoryIfNotExists(f"{saveToAbsLocation}/img")
	createDirectoryIfNotExists(f"{saveToAbsLocation}/img/elements")
	createDirectoryIfNotExists(f"{saveToAbsLocation}/img/elements/{apparatus}")
	apparatusElementFile = open(f"{saveToAbsLocation}/csv/{apparatus}.csv", "w+")
	if(apparatus != APPARATUS[3]):
		apparatusElementFile.write(f"name,explanation,group,group_name,element_alphabetic_value,element_numeric_value,page_nr,row,col,img_url\n")
	else:
		apparatusElementFile.write(f"name,explanation,group,group_name,element_numeric_value,page_nr,row,col,img_url\n")
	start_page = APPARATUS_ELEMENT_PAGES[apparatus][0]
	end_page = APPARATUS_ELEMENT_PAGES[apparatus][1]

	nr_of_pages = end_page - start_page + 1
	total_nr_of_elements = nr_of_pages * NR_OF_ROWS * NR_OF_COLS
	nr_of_elements_done = 0

	page_index = 0

	for file_name in os.listdir(BASE_IMAGE_PATH):
		if(not isValidFile(file_name, start_page, end_page)):
			continue
		page_index += 1
		# "cop is short for "Code of Points"
		cop_page = int(file_name[-7:-4])
		cop_page_img = Image.open(f"{BASE_IMAGE_PATH}/{file_name}")
		group, group_name = getCoPPageGroup(cop_page_img)
		print(f"  Page: {page_index}/{nr_of_pages}")
		print(f"    ", end='')
		for row in range(NR_OF_ROWS):
			for col in range(NR_OF_COLS):
				x = START_X + col * (WIDTH + OFFSET_X)
				y = START_Y + row * (HEIGHT + OFFSET_Y)
				box = (x, y, x + WIDTH, y + HEIGHT)
				cropped_cop_page_img = cop_page_img.crop(box)

				element_alphabetic_value = 'A'
				element_numeric_value = 0.1

				if(apparatus != APPARATUS[3]):
					element_alphabetic_value, element_numeric_value = getDifficulty(col)

				cropped_cop_page_img.save(f"{saveToAbsLocation}/img/elements/{apparatus}/page-{cop_page}-row-{row+1}-col-{col+1}.png")

				if(apparatus == APPARATUS[3]):
					cop_element_img = cv.imread(f"{saveToAbsLocation}/img/elements/{apparatus}/page-{cop_page}-row-{row+1}-col-{col+1}.png")
					height,width,_ = cop_element_img.shape
					cropped_image = cop_element_img[height-50:height, 0:150]
					element_text = tes.image_to_string(cropped_image)
					element_numeric_value = element_text.strip()

				name, explanation = getElementText(f"{saveToAbsLocation}/img/elements/{apparatus}/page-{cop_page}-row-{row+1}-col-{col+1}.png")
				if(apparatus != APPARATUS[3]):
					apparatusElementFile.write(f"{name}{SEPARATOR}{explanation}{SEPARATOR}{group}{SEPARATOR}{group_name}{SEPARATOR}{element_alphabetic_value}{SEPARATOR}{element_numeric_value}{SEPARATOR}{cop_page}{SEPARATOR}{row+1}{SEPARATOR}{col+1}{SEPARATOR}{saveToAbsLocation}/img/elements/{apparatus}/page-{cop_page}-row-{row+1}-col-{col+1}.png\n")
				else:
					apparatusElementFile.write(f"{name}{SEPARATOR}{explanation}{SEPARATOR}{group}{SEPARATOR}{group_name}{SEPARATOR}{element_numeric_value}{SEPARATOR}{cop_page}{SEPARATOR}{row+1}{SEPARATOR}{col+1}{SEPARATOR}{saveToAbsLocation}/img/elements/{apparatus}/page-{cop_page}-row-{row+1}-col-{col+1}.png\n")
				nr_of_elements_done += 1
		print(f"{round(nr_of_elements_done/total_nr_of_elements * 100, 2)}%", end=" ")

		print()
	apparatusElementFile.close()

# for file_name in os.listdir(BASE_IMAGE_PATH):
# 	if(file_name[-4:] != ".png"):
# 		continue
# 	split_file_name = file_name.split(".")
# 	split_split_file_name = split_file_name[0].split("-")
# 	page_nr = split_split_file_name[-1]
#
# 	img = Image.open(f"{BASE_IMAGE_PATH}/{file_name}")
#
# 	elementGroupBox = (40, 122, 2298, 122+60)
# 	elementGroupImg = img.crop(elementGroupBox)
#
# 	text = tes.image_to_string(elementGroupImg)
# 	textSplit = text.split(":")
# 	elementGroup = textSplit[0]
# 	elementGroupName = ''
#
# 	for line in textSplit[1].split(" - "):
# 		print(line)
# 		try:
# 			if(detect(line) == 'en'):
# 				elementGroupName = line
# 		except:
# 			x = 1
#
# 	if(not os.path.isdir(f"{saveToAbsLocation}/{APPARATUS[2]}/element-page-{page_nr}")):
# 		os.mkdir(f"{saveToAbsLocation}/{APPARATUS[2]}/element-page-{page_nr}")
#
# 	for row in range(NR_OF_ROWS):
# 		for col in range(NR_OF_COLS):
# 			elementValues = getDifficulty(col)
#
# 			elementValueLetter = elementValues[0]
# 			elementValueNumber = elementValues[1]
#
# 			x = START_X + col * (WIDTH + OFFSET_X)
# 			y = START_Y + row * (HEIGHT + OFFSET_Y)
# 			box = (x, y, x + WIDTH, y + HEIGHT)
# 			img2 = img.crop(box)
# 			img2.save(f"{saveToAbsLocation}/{APPARATUS[2]}/element-page-{page_nr}/row-{row+1}-col-{col+1}.png")
# 			texts = getElementText(f"{saveToAbsLocation}/{APPARATUS[2]}/element-page-{page_nr}/row-{row+1}-col-{col+1}.png")
# 			pommelHorseFile.write(f"{texts['name']}{SEPARATOR}{texts['explanation']}{SEPARATOR}{elementGroup}{SEPARATOR}{elementGroupName}{SEPARATOR}{elementValueLetter}{SEPARATOR}{elementValueNumber}{SEPARATOR}{page_nr}{SEPARATOR}{row+1}{SEPARATOR}{col+1}{SEPARATOR}{APPARATUS[2]}/element-page-{page_nr}/row-{row+1}-col-{col+1}.png\n")
#
# pommelHorseFile.close()
