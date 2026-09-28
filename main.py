from machine import Pin, PWM
import dht
import time

#Constantes
#Pines según diagram.json
PIN_SENSOR_CLIMA = 2   #DHT22 (SDA) con resistencia pull-up de 10k
PIN_LED_AZUL = 3       #LED azul a través de resistencia de 330
PIN_LED_ROJO = 4       #LED rojo a través de resistencia de 330
PIN_ZUMBADOR = 5       #Buzzer
PIN_BOTON = 6          #Pulsador, el otro extremo va a GND

#Umbral de temperatura en grados celsius
UMBRAL_TEMPERATURA = 27.0

#Tiempos (en milisegundos)
TIEMPO_ANTIRREBOTE = 50      #Espera para evitar rebotes del botón
TIEMPO_LED_ENCENDIDO = 2000  #Tiempo que el LED permanece encendido
TIEMPO_ENTRE_LECTURAS = 2000 #El DHT22 solo permite una lectura cada 2 segundos

#Frecuencias de las notas (Hz)
NOTA_DO4 = 262
NOTA_SOL4 = 392
NOTA_DO5 = 523
NOTA_MI5 = 659
NOTA_SOL5 = 784

#Sonido positivo: notas ascendentes (nota, duracion_ms)
MELODIA_POSITIVA = [
    (NOTA_DO5, 120),
    (NOTA_MI5, 120),
    (NOTA_SOL5, 200)
]

#Sonido negativo: notas descendentes y graves (nota, duracion_ms)
MELODIA_NEGATIVA = [
    (NOTA_SOL4, 250),
    (NOTA_DO4, 400)
]

#Componentes, se inicializan en configurar_componentes()
sensor_clima = None
led_azul = None
led_rojo = None
boton = None
zumbador = None

#Momento de la última lectura del sensor
ultima_lectura = 0

#Configura los pines de todos los componentes según diagram.json
def configurar_componentes():
    global sensor_clima, led_azul, led_rojo, boton, zumbador

    #Sensor de temperatura y humedad
    sensor_clima = dht.DHT22(Pin(PIN_SENSOR_CLIMA))

    #LEDs como salidas
    led_azul = Pin(PIN_LED_AZUL, Pin.OUT)
    led_rojo = Pin(PIN_LED_ROJO, Pin.OUT)

    #Botón como entrada con pull-up interno (el otro extremo va a GND)
    boton = Pin(PIN_BOTON, Pin.IN, Pin.PULL_UP)

    #Zumbador por PWM para poder variar la frecuencia
    zumbador = PWM(Pin(PIN_ZUMBADOR))

    #Todo apagado al inicio
    apagar_leds()
    silenciar_zumbador()

#Apaga el zumbador (duty 0 = silencio)
def silenciar_zumbador():
    zumbador.duty_u16(0)

#Reproduce una nota en el zumbador (frecuencia en Hz, duración en ms)
def reproducir_nota(frecuencia, duracion):
    zumbador.freq(frecuencia)
    #Duty al 50% para un tono claro
    zumbador.duty_u16(32768)
    time.sleep_ms(duracion)
    silenciar_zumbador()
    #Pequeña pausa entre notas
    time.sleep_ms(30)

#Reproduce una melodía, lista de tuplas (frecuencia, duración)
def reproducir_melodia(melodia):
    for frecuencia, duracion in melodia:
        reproducir_nota(frecuencia, duracion)

#Apaga ambos LEDs
def apagar_leds():
    led_azul.value(0)
    led_rojo.value(0)

#Lee la temperatura del DHT22, retorna None si falla
def leer_temperatura():
    global ultima_lectura

    #El DHT22 necesita al menos 2 segundos entre lecturas
    transcurrido = time.ticks_diff(time.ticks_ms(), ultima_lectura)
    if transcurrido < TIEMPO_ENTRE_LECTURAS:
        time.sleep_ms(TIEMPO_ENTRE_LECTURAS - transcurrido)

    #Intentar leer el sensor
    try:
        sensor_clima.measure()
        ultima_lectura = time.ticks_ms()
        return sensor_clima.temperature()
    except OSError as e:
        print(f"Error al leer el sensor: {e}")
        return None

#Muestra el resultado: LED azul y sonido positivo si está por debajo
#del umbral, LED rojo y sonido negativo si es igual o mayor
def indicar_resultado(temperatura):
    apagar_leds()

    #Temperatura por debajo del umbral
    if temperatura < UMBRAL_TEMPERATURA:
        print(f"Temperatura {temperatura:.1f}°C por debajo de {UMBRAL_TEMPERATURA}°C -> LED azul")
        led_azul.value(1)
        reproducir_melodia(MELODIA_POSITIVA)

    #Temperatura igual o por encima del umbral
    else:
        print(f"Temperatura {temperatura:.1f}°C igual o mayor a {UMBRAL_TEMPERATURA}°C -> LED rojo")
        led_rojo.value(1)
        reproducir_melodia(MELODIA_NEGATIVA)

    #Mantener el LED encendido un momento y luego apagarlo
    time.sleep_ms(TIEMPO_LED_ENCENDIDO)
    apagar_leds()

#Espera a que el botón sea presionado y soltado (con antirrebote)
#El botón está con pull-up, así que 0 = presionado
def esperar_pulsacion():
    #Esperar a que se presione
    while boton.value() == 1:
        time.sleep_ms(10)

    #Antirrebote
    time.sleep_ms(TIEMPO_ANTIRREBOTE)

    #Confirmar que sigue presionado (no fue un rebote)
    if boton.value() == 1:
        return False

    #Esperar a que se suelte
    while boton.value() == 0:
        time.sleep_ms(10)

    #Antirrebote al soltar
    time.sleep_ms(TIEMPO_ANTIRREBOTE)
    return True

#Ciclo principal: espera el botón, mide la temperatura y muestra el resultado
def iniciar():
    #Preparar todos los componentes
    configurar_componentes()

    #Logging
    print("Sistema iniciado")
    print(f"Umbral: {UMBRAL_TEMPERATURA}°C")
    print("Presione el botón para medir la temperatura...")

    try:
        #Escuchar el botón
        while True:
            #Si la pulsación fue "parcial", volver a esperar
            if not esperar_pulsacion():
                continue

            #Si la pulsación es válida...
            print("Botón presionado, midiendo temperatura...")

            #Leer temperatura
            temperatura = leer_temperatura()

            #Si la lectura falló, avisar y volver a esperar
            if temperatura is None:
                print("No se pudo leer la temperatura, intente de nuevo")
                continue

            #Mostrar resultado con LEDs y zumbador
            indicar_resultado(temperatura)

            print("Presione el botón para medir de nuevo...")

    #Al interrumpir con teclado
    except KeyboardInterrupt:
        print("\nDeteniendo sistema...")

    #Siempre apagar los componentes
    finally:
        apagar_leds()
        silenciar_zumbador()
        zumbador.deinit()


if __name__ == "__main__":
    iniciar()
