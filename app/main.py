from .Pixel import Pixel
from .VectorNico import VectorNico
import cv2
import numpy as np
import base64
from PIL import Image, ImageFile
from io import BytesIO


from flask import Flask, request, jsonify
app = Flask(__name__)
saveInMemoryFileName = 'test.png'
resultInvalid = -1

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

def isColorWanted(basePixel: Pixel, blackPixel: Pixel, graduation):
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

def getValorTiempoPixel(pixelFrom, pixelTo, horizontalBreakCondition, minimumDiffAllow, debugFlag):
    diff =  pixelFrom - pixelTo 
    if(diff < horizontalBreakCondition and diff > minimumDiffAllow):
        return diff
    else:
        if debugFlag == True: print("discarting result ", pixelTo,"/", pixelFrom , ". Diff is equal to ", diff)
        return resultInvalid

def fixValues(vectoresToFix, vectorWithValue, previousValue, debugFlag):
    cantPerValue = (vectorWithValue.valor - previousValue) / len(vectoresToFix)
    aux = previousValue + cantPerValue
    for vector in vectoresToFix:
        vector.valor = aux
        if debugFlag == True: print("fixed value for ", vector.tiempo, " to value ", vector.valor)
        aux += cantPerValue
    return vectoresToFix

####################################################################
################### CORE Methods ###################################
####################################################################
def foundValueInImage(rows, cols, file_path, image, black, blackGraduation, white):
    imageFinal = cv2.imread(file_path)
    assert not isinstance(imageFinal,type(None)), 'image Final not found'

    for row in range(0, rows):
        for col in range(0, cols):
            pixel = Pixel(image.item(row, col, 0), image.item(row, col, 1), image.item(row, col, 2))

            if isColorWanted(pixel, black, blackGraduation):
                setPixel(imageFinal, row, col, black)
            else:
                setPixel(imageFinal, row, col, white)
    return imageFinal

def convertToVector(cols, rows, imageFinal, black, wantedVia, dissplacementVias):
    final = []
    yBase = 0
    for col in range(0, cols):
        pixelFound = False
        actualVia = 0
        actualViaX = 0
        for row in range(0, rows):
            pixel = Pixel(imageFinal.item(row, col, 0), imageFinal.item(row, col, 1), imageFinal.item(row, col, 2))
            if isColorWanted(pixel, black, 0):
                targetX = 0 if (actualVia == 0) else actualViaX + dissplacementVias
                #print("col",col,"row",row,"targetX",targetX)

                if(wantedVia == actualVia and row >= targetX):
                    #print("FOUND VIA in row ", row, "targetX =" , targetX)
                    pixelFound = True
                    if len(final) == 0:
                        yBase = row
                        final.append(VectorNico(len(final), 0))
                    else:
                        final.append(VectorNico(len(final), calculateValueFromPixels(row, yBase)))
                    break
                else:
                    if(row >= targetX): #we are not in same via 
                        #print("via not used in row ", row, "targetX =" , targetX, "wantedVia",wantedVia,"actualVia",actualVia)
                        actualVia += 1
                        actualViaX = row
                    else: print("we are in same via")
                    
        if pixelFound == False:
            final.append(VectorNico(len(final), 0))

    return final

def findPixelValueInTime(cols, rows, image, red, redGraduation, debugFlag):
    horizontalBreakConditionSearchingBars = rows / 4
    minimumDiffAllow = 5

    pixelValueInTime = resultInvalid
    firstPixelX = resultInvalid
    secondPixelX = resultInvalid
    
    for col in range(0, cols):
        if(pixelValueInTime != resultInvalid):
            if debugFlag == True: print("skip column", col, "with value ", pixelValueInTime)
            break

        for row in range(0, rows):
            pixel = Pixel(image.item(row, col, 0), image.item(row, col, 1), image.item(row, col, 2))
            if isColorWanted(pixel, red, redGraduation):
                if firstPixelX == resultInvalid:
                    #found left side of bar
                    firstPixelX = row
                    if debugFlag == True: print("first value is ", firstPixelX)
                else:
                    #found right side of bar
                    secondPixelX = row
                    if debugFlag == True: print("second value is ", secondPixelX)
                    pixelValueInTime = getValorTiempoPixel(firstPixelX, secondPixelX, horizontalBreakConditionSearchingBars, minimumDiffAllow, debugFlag)
                
                    if pixelValueInTime != resultInvalid:
                        if debugFlag == True: print("found value ", pixelValueInTime, "in row/col = ", row,"/",col)
                        break
                    else:
                        secondPixelX = resultInvalid
    return pixelValueInTime

# BIG SQUARES IS 0,2 SECONDS ,SO ITS 200 MILISECONDS, A BIG SQUARE HAVE 5 SMALL QUARES (IF FOUND THE SIZE OF ONE IN PREVIUS METHOD)
# SO SMALL SQUEARE HAVE 200 / 5 MILISECONDS = 40 MILISECONDS
# IF FOUND THE SIZE OF A SMALL SQUEARE IN valorTiempoPixel VARIABLE SO I ASUME FIRST VECTOR LIKE 0, AND START ADDING THAT TIME TO THE VECTOR
# set correct time to result depending of the pixels used
def fixTimeEscale(final, valorTiempoPixel, lambdaErrors, debugFlag):
    timeValue = 0
    milisecondsPerSmallSquare = 40
    pixelTimeValue =  milisecondsPerSmallSquare / (valorTiempoPixel + lambdaErrors)
    fix = []
    showResult = []
    previousValue = 0
    for i in range(0, len(final)):
        final[i].tiempo = timeValue
        timeValue = timeValue + pixelTimeValue

        if final[i].valor == 0:
            fix.append(final[i])
        else:
            if len(fix) != 0:
                vectoreTofix = fixValues(fix, final[i], previousValue, debugFlag)
                fix = []
                for vectorAux in vectoreTofix:
                    showResult.append(vectorAux.toJSON())
            previousValue = final[i].valor
            showResult.append(final[i].toJSON())
    
    return showResult

####################################################################
################### Start Program ##################################
####################################################################
@app.route("/")
def home_view():
    return "<h1>Welcome to Electro App</h1>"

@app.route("/process", methods=['GET', 'POST'])
def process():
    debugFlag = False
    content = request.json

    # VARIABLE TO FOUND PIXELS IN IMAGES
    red = Pixel(0, 0, 255)
    redGraduation = content['redGraduation']
    black = Pixel(0, 0, 0)
    blackGraduation = content['blackGraduation']
    white = Pixel(255, 255, 255)
    lambdaErrors = content['horizontalMovementFix']
    numberOfVias = content['numberOfVias']
    dissplacementVias = content['dissplacementVias']

    # VARIABLES TO GET THE IMAGE
    imgFromEndpoint = content['image']
    file_path = saveFileToDisk(imgFromEndpoint)
    print("READING FILE IN PATH: ", file_path)
    image = cv2.imread(file_path)
    assert not isinstance(image,type(None)), 'image not found'
    rows = image.shape[0:2][0]
    cols = image.shape[0:2][1]

# MODIFICAMOS LA IMAGEN ORIGINAL Y DETECTAMOS EL NEGRO EN LA FOTO, PORQUE ESTE ES EL ELECTRO QUE QUEREMOS PASAR
    print("SEARCHING VALUES IN IMAGE")
    imageFinal = foundValueInImage(rows, cols, file_path, image, black, blackGraduation, white)
    #cv2.imshow("CUADRICULA - ORIGINAL", image)
    #cv2.imshow("CUADRICULA - FINAL", imageFinal)
    #cv2.waitKey(0)

# TRANSFORMAMOS LA FOTO MODIFICADA EN EL VECTOR DE TIEMPO / VALOR
    vias = []
    for wantedVia in range (0, numberOfVias):
        print("CONVERT BLACK AND WHITE IMAGE TO VECTOR FOR VIA =", wantedVia)
        final = convertToVector(cols, rows, imageFinal, black, wantedVia, dissplacementVias)
        vias.append(final)
    

# DETERMINAMOS CUANTO MIDE UN SEGUNDO DE TIEMPO EN LA GRADILLA EN PIXELES PARA AJUSTAR LA TABLA DE TIEMPOS DE LOS VECTORES
    print("BUSCANDO LA RELACION PIXEL / MILISEGUNDOS PARA AJUSTAR POSTERIORMENTE VECTORES")
    valorTiempoPixel = findPixelValueInTime(cols, rows, image, red, redGraduation, debugFlag)

# CONVERT VECTOR TO SHOW CORRECTLY TIME RESULTS
    showResultVias = []
    vectorNum = 1
    for wantedViaVector in vias:
        print("AJUSTANDO TABLA PARA VECTOR", vectorNum, "USANDO VALOR TIEMPO 1 PIXEL EN", valorTiempoPixel, "MILISEGUNDOS")
        showResult = fixTimeEscale(wantedViaVector, valorTiempoPixel, lambdaErrors, debugFlag)
        showResultVias.append(showResult)
        vectorNum+=1

    return jsonify(showResultVias)
