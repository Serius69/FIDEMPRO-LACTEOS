from django.shortcuts import render
def cargar_datos(request):
    # Recupera los valores de los campos del formulario (puedes usar request.GET o request.POST según corresponda)
    x0 = float(request.GET.get("id-nmsimul"))
    x1 = float(request.GET.get("id-nmaxd"))
    x2 = float(request.GET.get("id-cfijd"))
    x3 = float(request.GET.get("id-cadq"))
    x4 = float(request.GET.get("id-pplato1"))
    x5 = float(request.GET.get("id-pplato2"))
    x6 = float(request.GET.get("id-pplato3"))
    x7 = float(request.GET.get("id-pbebi"))
    x8 = float(request.GET.get("id-cord"))
    x9 = float(request.GET.get("id-ctdel"))
    x10 = float(request.GET.get("id-cinv"))
    x11 = float(request.GET.get("id-invbe"))

    # Convertir valores según necesites
    nmsimul = int(x0)
    nmaxd = int(x1)
    cfijd = x2
    cadq = x3
    pplato1 = x4
    pplato2 = int(x5)
    pplato3 = int(x6)
    pbebi = x7
    cord = x8
    ctdel = x9
    cinv = x10
    invbe = x11

    # Lógica de simulación
    totalganancianeta = 0
    totalnoatendidos = 0

    for i in range(1, nmsimul + 1):
        # Aquí va la lógica de la simulación (reemplaza el contenido de la función simulate)
        totalnoatendidos = 0 ##retirar
        # Al final de cada iteración, actualiza los valores de totalganancianeta y totalnoatendidos

    promedio_ganancia = totalganancianeta / nmsimul
    promedio_noatendidos = totalnoatendidos / nmsimul

    return render(request, 'template.html', {
        'promedio_ganancia': promedio_ganancia,
        'promedio_noatendidos': promedio_noatendidos,
    })

def limpiar_tabla(request):
    return render(request, 'template.html')

def limpiar_promedio(request):
    return render(request, 'template.html')
