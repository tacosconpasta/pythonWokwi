# Termómetro con alerta para repostería casera

Proyecto en Raspberry Pi Pico con MicroPython, simulado en Wokwi.

---

## 1. Enunciado del problema

Doña Marta tiene una pequeña repostería en su casa. Decora pasteles con crema de
mantequilla y los guarda en un cuarto trasero mientras espera que los clientes
pasen a recogerlos.

El cuarto no tiene aire acondicionado. En los días calurosos la crema se ablanda
y las decoraciones pierden su forma a partir de los 27 °C, así que ese día los
pasteles deben ir al refrigerador en lugar del cuarto.

Su rutina actual tiene dos problemas:

- Tiene que acercarse a un termómetro de pared, leer los números pequeños y
  decidir, muchas veces con una bandeja en las manos.
- A veces olvida revisar y se entera cuando ya un pastel se dañó.

Lo que necesita es simple: al entrar al cuarto, presionar un botón y recibir
una respuesta clara sin tener que leer nada.

- Una luz azul y un sonido agradable si el cuarto está bien (menos de 27 °C).
- Una luz roja y un sonido de advertencia si está muy caliente (27 °C o más).

No necesita un sistema de monitoreo permanente, registros ni conexión a
internet. Es una revisión puntual, a demanda, para un solo cuarto.

### Restricciones

- Bajo costo: un microcontrolador, un sensor, dos LEDs, un botón y un zumbador.
- Fácil de usar: un solo botón, sin pantalla ni configuración.
- Respuesta inmediata y perceptible a distancia (luz y sonido).

---

## 2. ¿Qué hace la solución?

Un termómetro con alerta. Al presionar un botón, el sistema mide la temperatura
ambiente y avisa con luz y sonido si está por debajo o por encima del umbral de
27 °C.

---

## 3. Componentes (simulados en Wokwi)

| Componente | Función | Conexión |
|---|---|---|
| Raspberry Pi Pico | Ejecuta el programa en MicroPython | — |
| Sensor DHT22 | Mide temperatura y humedad | GP2, con resistencia pull-up de 10 kΩ |
| Botón pulsador | Dispara la medición | GP6 y tierra (pull-up interno) |
| LED azul | Indica temperatura adecuada | GP3, resistencia de 330 Ω |
| LED rojo | Indica temperatura alta | GP4, resistencia de 330 Ω |
| Zumbador | Sonido positivo o negativo | GP5, controlado por PWM |

---

## 4. Lógica de decisión

| Condición | LED | Sonido |
|---|---|---|
| Temperatura menor a 27 °C | Azul | Melodía ascendente (positiva) |
| Temperatura igual o mayor a 27 °C | Rojo | Melodía descendente y grave (negativa) |

El LED se mantiene encendido dos segundos y luego el sistema vuelve a esperar
el botón.

---

## 5. Flujo del programa (función `iniciar`)

1. **Configurar componentes**: se inicializan los pines del sensor, los LEDs,
   el botón y el zumbador, y todo queda apagado.
2. **Esperar pulsación**: el programa se queda en un ciclo hasta que el botón
   se presione y se suelte, con antirrebote para ignorar pulsaciones falsas.
3. **Leer temperatura**: se consulta el DHT22. Si la lectura falla, se avisa y
   se vuelve a esperar.
4. **Indicar resultado**: según el umbral se enciende el LED correspondiente y
   se reproduce la melodía.
5. **Repetir**: vuelve al paso 2 indefinidamente.
6. Al interrumpir el programa, el bloque `finally` apaga LEDs y zumbador
   siempre.

```python
def iniciar():
    #Preparar todos los componentes
    configurar_componentes()

    print("Sistema iniciado")
    print(f"Umbral: {UMBRAL_TEMPERATURA}°C")
    print("Presione el botón para medir la temperatura...")

    try:
        #Escuchar el botón
        while True:
            #Si la pulsación fue "parcial", volver a esperar
            if not esperar_pulsacion():
                continue

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
```

---

## 6. Abstracciones

La función `iniciar` solo orquesta. Cada paso es una función con un único
propósito:

- `configurar_componentes`: prepara los pines y apaga todo.
- `esperar_pulsacion`: espera el botón con antirrebote.
- `leer_temperatura`: consulta el sensor respetando su tiempo mínimo entre
  lecturas y maneja errores.
- `indicar_resultado`: decide según el umbral y usa a su vez `apagar_leds` y
  `reproducir_melodia`.

Así el ciclo principal se lee como una lista de pasos y no como detalles de
hardware.

---

## 7. Herramientas

- **Wokwi para VS Code** simula el circuito descrito en `diagram.json`.
- **`wokwi.toml`** indica el firmware de MicroPython que corre la Pico.
- **mpremote** envía `main.py` al simulador por un puente serial en el puerto
  4000.

---

## 8. Cierre

- El umbral es una constante configurable: cambiar `UMBRAL_TEMPERATURA` adapta
  el sistema a otro producto o cuarto.
- La misma estructura sirve para cualquier sensor con alerta: se cambia qué se
  mide y qué se indica sin tocar el ciclo principal.
- Escala pequeña a propósito: resuelve un problema puntual con el mínimo de
  piezas, sin monitoreo continuo ni conectividad.
