#datos o funciones auxiliares para mantener ordenado nuestro codigo del servidor

import time
import numpy as np
import random
from paho.mqtt.client import Client


def monigotes():
    """
    Función que simplemente devuelve la lista con los sucesivos
    monigotes desde el inicio hasta el fin del juego del ahorcado.
    
    Parameters
    ----------
    None.
        
    Returns
    -------
    list : lista con los sucesivos estados de los monigotes.
    
    """

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

    return listaMonigotes


def decidirPartidaParaJugador(jugadores, ipPuerto):
    """
    Función que, dados los jugadores conectados al juego mediante el diccionario jugadores,
    y la referencia a la conexión de un jugador concreto mediante ipPuerto,
    encuentra la posición del jugador en el diccionario y le asigna una partida según la misma.
    
    Parameters
    ----------
    jugadores : dict
        Descripción del parámetro
    ipPuerto : tipo
        Tupla con la ip y el puerto.
        
    Returns
    -------
    int : Posición del jugador en el diccionario.
    int : Partida asignada al jugador.
    
    """
    
    pos = np.where( [ c==ipPuerto for (c,_) in np.array( list(jugadores.items()) )] )[0][0] + 1
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
    try:
        jugador.send("Elige una palabra de longitud "+str(lonPalabra))
    except IOError:
        print ('No enviado, conexión abruptamente cerrada por el jugador')


def pedirPalabraOLetra(jugador): 
    try:
        m = jugador.recv()
    except EOFError:
        print('algo no ha funcionado')
    return m


def palabracontraria(partida, jugadores, ipPuerto):
    for (ip, lista) in jugadores.items():
            if lista[0] == partida:
                if ip != ipPuerto: #si es mi contrincante y no yo
                    palabraContr = lista[3]  
                    break
    return palabraContr


def mostrarTablero(listaMonigotes, letrasIncorrectas, letrasCorrectas, palabraSecreta):
    espaciosVacios = '_' * len(palabraSecreta)
    for i in range(len(palabraSecreta)): # completar los espacios vacíos con las letras adivinadas
        if palabraSecreta[i] in letrasCorrectas:
            espaciosVacios = espaciosVacios[:i] + palabraSecreta[i] + espaciosVacios[i+1:]
    envio = '\n'+listaMonigotes[len(letrasIncorrectas)]+'\n'*2+'Letras incorrectas: '+str(letrasIncorrectas)+'\n'+'Lo que llevas de la palabra: '+str(espaciosVacios)+'\n'
    return envio


def ahorcado(jugador, ipPuerto, palabra, jugadores, partida, cerrojo, pareja, pos):
    
    listaMonigotes = monigotes()
    nTotalIntentos = len(listaMonigotes) - 1

    letrasCorrectas = []
    letrasIncorrectas = []
    nIntentosFallidos = 0

    while True:
        
        letra = pedirPalabraOLetra(jugador)
        if letra in palabra:
            letrasCorrectas.append(letra)
        else:
            letrasIncorrectas.append(letra)
        
        #CASO 1: si ha acertado todas las letras es ganador
        if all([char in letrasCorrectas for char in palabra]):
            cerrojo.acquire()
            jugadores[ipPuerto] = jugadores[ipPuerto][0:4]+['ganador']
            cerrojo.release()

            # POR AQUI MAS O MENOS SE DEBERIA INTRODUCIR LA REGION CRITICA
            
            try:
                jugador.send("HAS GANADO, la palabra era "+palabra)
            except IOError:
                print ('No enviado, conexión abruptamente cerrada por el jugador')
            break
        
        #CASO 2: si ha agotado todos sus intentos
        nIntentosFallidos = len(letrasIncorrectas)
        if nIntentosFallidos == nTotalIntentos:
            cerrojo.acquire()
            jugadores[ipPuerto] = jugadores[ipPuerto][0:4]+['agotado intentos']
            cerrojo.release()
            try:
                jugador.send("HAS AGOTADO TODOS TUS INTENTOS, la palabra era "+palabra)
            except IOError:
                print ('No enviado, conexión abruptamente cerrada por el jugador')
            break
        
        #CASO 3: si el otro es ganador ya no puede seguir tampoco
        if [ lista[4]=='ganador' for (_,lista) in [list(jugadores.items())[i] for i in pareja] ][pos%2]:
            try:
                jugador.send("TU CONTRINCANTE HA GANADO")
            except IOError:
                print ('No enviado, conexión abruptamente cerrada por el jugador')
            break
        
        #si ninguno de esos casos se ha dado, es que el juego continua para mí
        try:
            jugador.send( mostrarTablero(listaMonigotes, letrasIncorrectas, letrasCorrectas, palabra) )
        except IOError:
            print ('No enviado, conexión abruptamente cerrada por el jugador')



def borrarParejaDict(pareja, jugadores, ipPuerto):
    if ipPuerto in [ip for (ip,_) in list(jugadores.items())]: #si no he borrado todavía a la pareja, mi ip sigue estando en el diccionario
        ipsPareja = [ ip for (ip,_) in [list(jugadores.items())[i] for i in pareja] ]
        for ip in ipsPareja:
            del jugadores[ip] # lo borro del diccionario


def on_publish(client, userdata, mid):
    print("Resultado publicado.\n")


def publicarResultados(lista):
    
    cliente = Client()
    cliente.connect("wild.mat.ucm.es")
    cliente.on_publish = on_publish

    topic = 'clients/resultadosAhorcado'
    mensaje = "RESULTADO EN LA PARTIDA "+str(lista[0])+" para el jugador con apodo "+lista[1]+": "+" Propuso la palabra "+lista[3]+" y finaliza el juego con el estado "+lista[4]+"."
    
    print ('Mensaje  a publicar en ', topic, ': ', mensaje)
    cliente.publish(topic,mensaje)
    