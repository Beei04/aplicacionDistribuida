from multiprocessing.connection import Listener, AuthenticationError #, Client
from multiprocessing import Process, Lock, Manager
import random
import time
import numpy as np



listaMonigotes = ['''
    ''', '''
 
   +---+
   |   |
       |
       |
       |
       |
 =========''', '''
 
   +---+
   |   |
   O   |
       |
       |
       |
 =========''', '''
 
   +---+
   |   |
   O   |
   |   |
       |
       |
 =========''', '''
 
   +---+
   |   |
   O   |
  /|   |
       |
       |
 =========''', '''
 
   +---+
   |   |
   O   |
  /|\  |
       |
       |
 =========''', '''
 
   +---+
   |   |
   O   |
  /|\  |
  /    |
       |
 =========''', '''
 
   +---+
   |   |
   O   |
  /|\  |
  / \  |
       |
 =========''']

nTotalIntentos = len(listaMonigotes) - 1



def decidirPartidaParaJugador(jugadores, ipPuerto):
    claves = np.array( list(jugadores.keys()) )
    pos = list ( np.where(claves == ipPuerto)[0] )[0] + 1
    if pos % 2 == 0: # la posición es par
        partida = pos/2
    else: # la posición es impar
        partida = (pos-1)/2 + 1
    return int(pos), int(partida)

def saludar(apodo, pos, jugador):
    if pos % 2 != 0:
        jugador.send('Hola '+apodo+' tu papel es de Jugador 1.')
    else:
        jugador.send('Hola '+apodo+' tu papel es de Jugador 2.')

def establecerLongitudPalabra(partida, jugadores, cerrojo):
    lonPalabra = random.randint(4,6)
    for (ip, lista) in jugadores.items():
            if lista[0] == partida:
                if len(lista) < 3:
                    cerrojo.acquire()
                    jugadores[ip] = jugadores[ip] + [lonPalabra]
                    cerrojo.release()

def notificar_inicio_juego(jugador, ipPuerto, jugadores):
    lonPalabra = jugadores[ipPuerto][2]
    print ("Mandando longitud de palabra a ", jugadores[ipPuerto][1], ' que está en ', ipPuerto)
    jugador.send("Elige una palabra de longitud "+str(lonPalabra))

def pedirPalabraOLetra(jugador): 
    try:
        m = jugador.recv()
    except EOFError:
        print('algo no ha funcionado')
    return m

def palabracontraria(partida, jugadores, ipPuerto):
    for (ip, lista) in jugadores.items():
            if lista[0] == partida:
                if ip != ipPuerto:
                    palabraContr = lista[3]
                    break
    return palabraContr

def mostrarTablero(listaMonigotes, letrasIncorrectas, letrasCorrectas, palabraSecreta):
    espaciosVacios = '_' * len(palabraSecreta)
    for i in range(len(palabraSecreta)): # completar los espacios vacíos con las letras adivinadas
        if palabraSecreta[i] in letrasCorrectas:
            espaciosVacios = espaciosVacios[:i] + palabraSecreta[i] + espaciosVacios[i+1:]
    envio = listaMonigotes[len(letrasIncorrectas)]+'\n'*2+'Letras incorrectas: '+str(letrasIncorrectas)+'\n'+'Lo que llevas de la palabra: '+str(espaciosVacios)+'\n'
    return envio


#def localizarJugador(pareja, ipPuerto):
#    i = -1
#    for key in pareja.keys():
#        i += 1
#        if key == ipPuerto:
#            break
#    return i


#def colocarPalabra(pareja, palabra, ipPuerto):
#    i = localizarJugador(pareja, ipPuerto)
#    pareja['palabras'] = [(1, 'default'), (2, 'default')]
#    pareja['palabras'][i] = (i+1, palabra)
#    print('El jugador ', i+1, ' propone la palabra: ', palabra)


def ahorcado(jugador, ipPuerto, palabra, pareja):
    #ahora aqui ya debe empezar el bucle del ahorcado
    #el bucle (juego) terminará cuando el nIntentos==nTotalIntentos o cuando el otro jugador gane
    #LISTA MONIGOTES Y NTOTALINTENTOS DEBERIA METERLOS DENTRO DE SERVER_CLIENT
    jugador_info, _ = pareja[ipPuerto]
    conn = Client(address=jugador_info[0], authkey=jugador_info[1])
    
    juegoContinua = True
    letrasCorrectas = []
    letrasIncorrectas = []
    nIntentosFallidos = 0
    
    while juegoContinua:
        juegoContinua = not ( nIntentosFallidos==nTotalIntentos or
         any([x=='ganador' for (_,x) in pareja['haGanado']]) )
        
        letra = pedirPalabraOLetra(jugador)
        if letra in palabra:
            letrasCorrectas.append(letra)
        else:
            letrasIncorrectas.append(letra)
        
        if all([char in letrasCorrectas for char in palabra]):
            i = localizarJugador(pareja, ipPuerto)
            pareja['haGanado'][i] = (i+1, 'ganador')
            print('EL JUGADOR ', i+1, ' HA GANADO!!!')
            jugador.send("HAS GANADO, LA PALABRA ERA "+palabra)
            jugador.close()
            break

        jugador.send( '\n'+mostrarTablero(listaMonigotes, letrasIncorrectas, letrasCorrectas, palabra) )
        nIntentosFallidos = len(letrasIncorrectas)



def serve_client(jugador, ipPuerto, jugadores, cerrojo):

    #asigno una partida al jugador:
    pos, partida = decidirPartidaParaJugador(jugadores, ipPuerto)
    apodo = jugadores[ipPuerto][0]
    
    cerrojo.acquire()
    jugadores[ipPuerto] = [partida] + jugadores[ipPuerto]
    cerrojo.release()
    
    saludar(apodo, pos, jugador)

    #espero a que haya dos jugadores asignados a la misma partida para empezar
    while True:
        if sum( [lista[0]==partida for (_,lista) in jugadores.items()] ) != 2:
            jugador.send('Esperando al segundo jugador...')
            time.sleep(3)
        else:
            jugador.send('Ya sois dos jugadores AÑADIR COMO SE LLAMA EL COMPAÑERO, empieza la partida...')
            break
    
    establecerLongitudPalabra(partida, jugadores, cerrojo)

    notificar_inicio_juego(jugador, ipPuerto, jugadores)
    
    #añado la palabra a la lista del jugador en el diccionario
    palabra = pedirPalabraOLetra(jugador)
    cerrojo.acquire()
    jugadores[ipPuerto] = jugadores[ipPuerto] + [palabra]
    cerrojo.release()

    #bucle que no permita continuar hasta que los 2 jugadores tienen la palabra colocada
    nJugadoresConPalabraColocada = 0
    while nJugadoresConPalabraColocada != 2:
        for (_,lista) in jugadores.items():
            if lista[0] == partida:
                if len(lista) == 4:
                    nJugadoresConPalabraColocada += 1
                else:
                    jugador.send("Espera porque tu compi todavía no ha elegido la palabra para ti...")
                    time.sleep(3)
    
    
    #colocarPalabra(pareja, palabra, ipPuerto)
    #pareja['haGanado'] = [(1,'no'), (2,'no')]
    print(jugadores) #borrar cuando ya compruebe que el diccionario está bien

    jugador.send('COMIENZA EL JUEGO DEL  A H O R C A D O')
    #ahorcado(jugador, ipPuerto, palabracontraria(partida, jugadores, ipPuerto), pareja)

    time.sleep(100)
    jugador.close() #DEBERÉ CERRAR A AMBOS JUGADORES
    

    #ADEMAS ME QUEDA EL CASO DE COMPROBAR SI TERMINA CUANDO AGOTA INTENTOS
    # SI TERMINARIA PARA AMBOS O SOLO PARA UNO Y ESPERA O QUE PASA
    #Y YA AL FINAL DEL TODISIMO SE PUBLICARIAN LOS RESULTADOS
        
    




if __name__ == '__main__':

    servidor = Listener(address=('127.0.0.1', 6000), authkey=b'secret password SERVER')
    print ('Iniciando servidor del ahorcado...')
    
    manager = Manager()
    jugadores = manager.dict()
    cerrojo = Lock()

    while True:
        print ('Aceptando jugadores...')
        try:
            jugador = servidor.accept()
            ipPuerto = servidor.last_accepted                
            print ('Jugador aceptado desde la IP y puerto siguientes: ', ipPuerto)
            
            infoListenerApodoJugador = jugador.recv()
            jugadores[ipPuerto] = infoListenerApodoJugador
            
            p = Process(target=serve_client, args=(jugador, ipPuerto, jugadores, cerrojo))
            p.start()

        except AuthenticationError:
            print ('Conexión rechaza, contraseña incorrecta')


    servidor.close()
    print ('FIN')
