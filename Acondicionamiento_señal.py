from machine import ADC, Pin, Timer
import time

sensor = ADC(Pin(34))         
sensor.atten(ADC.ATTN_11DB)   
sensor.width(ADC.WIDTH_12BIT)
led= Pin(21,Pin.OUT)
# Pines de electrodos
lo_plus = Pin(15, Pin.IN)  # LO+
lo_minus = Pin(18, Pin.IN) # LO-1

# Variables globales 
ultima_lectura = 0
nueva_lectura_disponible = False

# Variables para filtros
alpha = 0.1
valores_anteriores = []  # Para promedio móvil
ventana_mediana = []     # Para filtro mediana
valor_filtrado_anterior = 0  # Para filtro exponencial

def promedio_movil(valor_mv, n=10):
    global valores_anteriores
    valores_anteriores.append(valor_mv)
    if len(valores_anteriores) > n:
        valores_anteriores.pop(0)
    return sum(valores_anteriores) / len(valores_anteriores)

def filtro_exponencial(valor_mv):
    global valor_filtrado_anterior
    if valor_filtrado_anterior == 0:
        valor_filtrado_anterior = valor_mv
    valor_filtrado_anterior = alpha * valor_mv + (1 - alpha) * valor_filtrado_anterior
    return valor_filtrado_anterior

def filtro_mediana(valor_mv, n=5):
    global ventana_mediana
    ventana_mediana.append(valor_mv)
    if len(ventana_mediana) > n:
        ventana_mediana.pop(0)
    
    if len(ventana_mediana) == n:
        ventana_ordenada = sorted(ventana_mediana)
        return ventana_ordenada[n//2]
    else:
        return valor_mv  

def aplicar_filtros(valor_mv, filtros_seleccionados):
    valor_filtrado = valor_mv
    
    for filtro in filtros_seleccionados:
        if filtro == 1:  
            valor_filtrado = promedio_movil(valor_filtrado, n=10)
        elif filtro == 2:  
            valor_filtrado = filtro_exponencial(valor_filtrado)
        elif filtro == 3:  
            valor_filtrado = filtro_mediana(valor_filtrado, n=5)
    
    return valor_filtrado

def muestrear(t):
    global ultima_lectura, nueva_lectura_disponible
    ultima_lectura = sensor.read()
    nueva_lectura_disponible = True


frecuencia = int(input('Ingrese la frecuencia de muestreo (Hz): '))
cantidad_filtros = int(input('Ingrese cuantos filtros quiere usar (máx 3): '))

# Mostrar opciones de filtros
print("\nOpciones de filtros:")
print("1. Promedio móvil (suavizado)")
print("2. Filtro exponencial (pasa bajas)")
print("3. Filtro mediana (elimina ruido impulsivo)")

filtros_seleccionados = []
for i in range(cantidad_filtros):
    filtro = int(input(f'Seleccione el filtro #{i+1} (1-3): '))
    if 1 <= filtro <= 3:
        filtros_seleccionados.append(filtro)
    else:
        print("Opción no válida, se omitirá este filtro")

print(f"\nFiltros seleccionados: {filtros_seleccionados}")

Ts = int(1000/frecuencia)


timer = Timer(0)
timer.init(period=Ts, mode=Timer.PERIODIC, callback=muestrear)

print("\nIniciando lectura ECG...")
print("Presione Ctrl+C para detener")

with open('Datos_Paciente.csv', 'w') as f:
    f.write('Voltaje_mV_Filtrado\n')
    
    try:
        while True:
            if nueva_lectura_disponible:
                nueva_lectura_disponible = False
                
                if lo_plus.value() == 1 or lo_minus.value() == 1:
                    print("Electrodo Suelto!")  
                else:
                    led.value(1)
                    voltaje_mv = ((ultima_lectura - 2048) / 4095) * 3300
                    voltaje_filtrado = aplicar_filtros(voltaje_mv, filtros_seleccionados)
                    print("Filt: {:6.2f} | mV: {:7.2f}".format(voltaje_filtrado,voltaje_mv))
                    linea = '{},{}\n'.format( round(voltaje_filtrado, 2), round(voltaje_mv, 2))
                    f.write(linea)
                    f.flush()
                    
    except KeyboardInterrupt:
        led.value(0)
        print('\nAdquisicion detenida por el usuario')
        print('Ultima lectura:', ultima_lectura)

print('Datos guardados en Datos_Paciente.csv')