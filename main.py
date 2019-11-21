from __future__ import print_function	# For Py2/3 compatibility
import eel
import requests
import random
from socket import *
import threading
import concurrent.futures
import urllib.request
import os
import hashlib
import magic
import json
import time
SERVER_HOST = "http://192.168.0.3:8000/"
MAX_THREADS = 5
path = "files/"
list_files = {}
def download_part(server,filehash, part,total_parts):
    print("server: ",server)
    try:
        sock = socket(AF_INET,SOCK_STREAM)
        sock.connect((server["ip"],int(server["port"])))
        mensaje = {"command":"download","file":filehash,"part":part,"total":total_parts}
        sock.sendall(json.dumps(mensaje).encode())
        data = recvall(sock)
        if data == b'':
            raise NameError("Error al descargar la parte %s, contenido vacio"%str(part))
        print(data)
    except Exception as e:
        print(e)
        raise NameError("Error al descargar la parte %s"%str(part))
    return data
def readPart(hash,part,parts_num):
    filename = path+list_files[hash]["nombre"]
    size = list_files[hash]["size"]
    start = part*(size//parts_num)
    end = (part+1)*size//parts_num
    f = open(filename, 'rb')
    f.seek(start, 1)
    data = f.read(end-start)
    f.close()
    print(type(data))
    return data

def Write(sock,data):
    BUFF_SIZE = 1024
    l = len(data)-1
    print("LEN: ",l)
    i = 0
    while True:
        if i+BUFF_SIZE>=l:
            sock.send(data[i:l+1])
            break
        else:
            sock.send(data[i:i+BUFF_SIZE])
            i+=BUFF_SIZE
        time.sleep(0.1)
def recvall(sock):
        BUFF_SIZE = 1024
        data = b''
        while True:
            part = sock.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE:
                # either 0 or end of data
                break
        try:
            return json.loads(data.decode())
        except:
            return data
def handler(clientsock,addr):
    try:
        data = recvall(clientsock)
        if data["command"] == "download":
            if data["file"] not in list_files:
                clientsock.close()
                return
            Write(clientsock,readPart(data["file"],data["part"],data["total"]))
            print("Data enviada!")
    except Exception as e:
        print(e)
    print("cerrando conexion")
    clientsock.close()

def startServer(port):
    print("Servidor iniciado")
    ADDR = ("0.0.0.0", port)
    serversock = socket(AF_INET, SOCK_STREAM)
    serversock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serversock.bind(ADDR)
    serversock.listen(5)
    while 1:
        print('Esperando conexion...')
        clientsock, addr = serversock.accept()
        print('...Conexion iniciada', addr)
        threading.Thread(target=handler, args=(clientsock, addr)).start()

def getFiles():
    files = os.listdir(path)
    message = {"files":[]}
    mime = magic.Magic(mime=True)
    for f in files:
        size = os.path.getsize(path+f)
        mime_type = mime.from_file(path+f)
        hash = getHash(f)
        message["files"].append({"hash":hash,"size":size,"nombre":f,"type":mime_type})
        list_files[hash] = {"size":size,"nombre":f,"type":mime_type}
    hostname = gethostname()
    IPAddr = gethostbyname(hostname)
    message["users"] = [{"ip":IPAddr,"port":"8081"}]
    print(message)
    res = requests.post(SERVER_HOST+"uploadFile/",json=message)
    if res.status_code==200:
        print("Archivos sincronizados!")
    else:
        print("Error al sincronizar los archivos locales, error: ",res.status_code)
def getHash(filename):
    BLOCKSIZE = 65536
    hasher = hashlib.sha256()
    with open(path+filename, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()
@eel.expose
def downloadFile(hash):
    print("Tratando de descargar:",hash)
    res = requests.post(SERVER_HOST+"getPeers/",json={"files":[{"hash":hash}]})
    if res.status_code != 200:
        return
    res = res.json()
    if not "users" in res:
        print("No hay usuarios!")
        return
    users = res["users"]
    file_parts = [0 for i in range(MAX_THREADS if len(users)>MAX_THREADS else len(users))] # Las partes en las que dividieremos el archivo

    while (0 in file_parts) and (len(users)>0): #Vamos a descargar mientras no hemos descargado todo el archivo y al menos haya 1 Peer de donde descargar
        print(file_parts)
        # Llamado y obtencion de los resultados
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # generacion de tareas
            future_to_data = {}
            for i in range(len(file_parts)):
                future_to_data[executor.submit(download_part, users[i%len(users)],hash,i,len(file_parts))] = {"user":users[i%len(users)],"part":i}

            for future in concurrent.futures.as_completed(future_to_data):
                try:
                    data = future.result()
                except Exception as exc:
                    print('%r Error en el id: %s' % (exc,future_to_data[future]))
                    if future_to_data[future]["user"] in users:
                        users.remove(future_to_data[future]["user"]) # Significa que no pudimos descargar del mismo y tendremos que eliminarlo de las lista de peers
                    else:
                        print(">>>",future_to_data[future],users,"<<<")
                else:
                    print("ok en el id"+str(future_to_data[future]["part"]))
                    file_parts[future_to_data[future]["part"]] = data


    if 0 in file_parts or len(users)<1:
        return "not ok"
    with open(path+res["files"][0]["nombre"],'wb') as f:
        for i in file_parts:
            f.write(i)
    print("Noma si se pudo xd")
    return "ok"

if __name__ == '__main__':
    #name = input("Nickname: ")
    port = int(input("PORT: "))
    getFiles()
    eel.init('gui')
    threading.Thread(target=startServer, args=(8081,)).start()
    eel.start('index.html', options={"port":port})    # Start
