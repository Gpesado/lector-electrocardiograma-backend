from .Pixel import Pixel
from .VectorNico import VectorNico
import cv2
import numpy as np
import base64
from PIL import Image, ImageFile
from io import BytesIO


from flask import Flask, request, jsonify
app = Flask(__name__)
saveInMemoryFileName = 'C:/Users/gonza/Desktop/TESIS/TESIS_FINAL/BACKEND/test.png'

####################################################################
################### Auxiliar Methods ###############################
####################################################################
def saveFileToDisk(inMemoryImg):
    encoded_data = inMemoryImg.split(',')[1]
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    with open(saveInMemoryFileName, 'wb') as f:
        print("WRITING FILE IN PATH: ", saveInMemoryFileName)
        im = Image.open(BytesIO(base64.b64decode(encoded_data)))
        im.save(saveInMemoryFileName, 'PNG')
        f.close
    return saveInMemoryFileName

def isRed(basePixel: Pixel, redPixel: Pixel, graduation):
    if (basePixel.red > (redPixel.red - graduation)
        and ((basePixel.green + basePixel.blue < 255) and not(basePixel.green > 150 and basePixel.blue > 150))):
        return True
    else:
        return False

def isBlack(basePixel: Pixel, blackPixel: Pixel, graduation):
    if (basePixel.green <= (blackPixel.green + graduation) 
        and basePixel.blue <= (blackPixel.blue + graduation)
        and basePixel.red <= (blackPixel.red + graduation)):
        return True
    else:
        return False

def setPixel(image, row, col, pixel: Pixel):
    image.itemset((row, col, 0), pixel.blue)
    image.itemset((row, col, 1), pixel.green)
    image.itemset((row, col, 2), pixel.red)

def calculateValueFromPixels(y, yBase):
    return yBase - y

####################################################################
################### Start Program ##################################
####################################################################
@app.route("/")
def home_view():
    return "<h1>Welcome to Geeks for Geeks</h1>"

@app.route("/process", methods=['GET', 'POST'])
def process():
    content = request.json
    imgFromEndpoint = content['image']
    file_path = saveFileToDisk(imgFromEndpoint)
    print("READING FILE IN PATH: ", file_path)
    image = cv2.imread(file_path)
    assert not isinstance(image,type(None)), 'image not found'
    print("img = [", image, "]")
    imageFinal = cv2.imread(file_path)
    assert not isinstance(imageFinal,type(None)), 'image Final not found'
    print("img Final = [", imageFinal, "]")

    # NUMBER OF ROWS AND COLS IN IMAGE
    rows = image.shape[0:2][0]
    cols = image.shape[0:2][1]

    red = Pixel(0, 0, 255)
    redGraduation = 50;
    black = Pixel(0, 0, 0)
    blackGraduation = 50;
    white = Pixel(255, 255, 255)

    # MODIFICAMOS LA IMAGEN ORIGINAL Y DETECTAMOS EL NEGRO EN LA FOTO, PORQUE ESTE ES EL ELECTRO QUE QUEREMOS PASAR
    for row in range(0, rows):
        for col in range(0, cols):
            pixel = Pixel(image.item(row, col, 0), image.item(row, col, 1), image.item(row, col, 2))

            if isBlack(pixel, black, blackGraduation):
                setPixel(imageFinal, row, col, black)
            else:
                setPixel(imageFinal, row, col, white)

    #cv2.imshow("CUADRICULA - ORIGINAL", image)
    #cv2.imshow("CUADRICULA - FINAL", imageFinal)
    #cv2.waitKey(0)

    # TRANSFORMAMOS LA FOTO MODIFICADA EN EL VECTOR QUE RECIBE EL PROGRAMA DE NICO
    final = []
    yBase = 0
    for col in range(0, cols):
        for row in range(0, rows):
            pixel = Pixel(imageFinal.item(row, col, 0), imageFinal.item(row, col, 1), imageFinal.item(row, col, 2))
            if isBlack(pixel, black, 0):
                if len(final) == 0:
                    yBase = row
                    final.append(VectorNico(len(final), 0))
                else:
                    final.append(VectorNico(len(final), calculateValueFromPixels(row, yBase)))
                    #print(f"COL: {col} ROW: {row}")
                break

    #TEST DE VECTOR
    showResult = []
    for i in range (0, len(final)):
        final[i].mostrar()
        showResult.append(final[i].toString() + " \n")
        
    return ''.join(showResult)
