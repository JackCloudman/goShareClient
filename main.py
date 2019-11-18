from __future__ import print_function	# For Py2/3 compatibility
import eel


if __name__ == '__main__':
    #name = input("Nickname: ")
    port = int(input("PORT: "))
    eel.init('gui')
    #s = Connection("localhost",8080,"224.1.1.1",5007,name)
    print("Iniciando conexion!")
    eel.start('index.html', options={"port":port})    # Start
