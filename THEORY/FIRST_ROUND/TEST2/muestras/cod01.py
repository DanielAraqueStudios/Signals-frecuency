import cv2
import numpy as np
from PIL import Image

# Cargar la imagen
imagen = Image.open('./imagen.jpg')
imagen_gris = imagen.convert('L')
imagen_gris.save('imagen_gris.jpg')
imagen = cv2.imread('./imagen_gris.jpg', cv2.IMREAD_GRAYSCALE)

kernel_pasa_bajas = np.array([[0.04,  0.04,   0.04,  0.04,  0.04], 
                              [0.04,  0.04,   0.04,  0.04,  0.04], 
                              [0.04,  0.04,   0.04,  0.04,  0.04], 
                              [0.04,  0.04,   0.04,  0.04,  0.04], 
                              [0.04,  0.04,   0.04,  0.04,  0.04]])

kernel_pasa_altas00 = np.array([[2,  2,   2,  2,  2], 
                              [2,  -3, -3, -3,  2], 
                              [2,  -3,  -7, -3,  2], 
                              [2,  -3, -3, -3,  2], 
                              [2,  2,   2,  2,  2]])

kernel_pasa_altas02 = np.array([[0,   0,  0,  0,  0], 
                              [0,  -3, -3, -3,  0], 
                              [0,  -3, 24, -3,  0], 
                              [0,  -3, -3, -3,  0], 
                              [0,   0,  0,  0,  0]])


imagen_filtrada = cv2.filter2D(imagen, -1, kernel_pasa_altas02)
cv2.imshow('Filtro Pasa Altas', imagen_filtrada)
cv2.waitKey(0)
cv2.destroyAllWindows()

imagen_filtrada = cv2.filter2D(imagen, -1, kernel_pasa_bajas)
cv2.imshow('Filtro Pasa Bajas', imagen_filtrada)
cv2.waitKey(0)
cv2.destroyAllWindows()

imagen_filtrada = cv2.filter2D(imagen, -1, kernel_pasa_bajas)
imagen_filtrada = cv2.filter2D(imagen_filtrada, -1, kernel_pasa_altas02)
cv2.imshow('Filtro Pasa Bandas', imagen_filtrada)
cv2.waitKey(0)
cv2.destroyAllWindows()
