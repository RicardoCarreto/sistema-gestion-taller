import pandas as pd
import sqlite3
from datetime import datetime
from statistics import mean, median, multimode, variance, stdev

def conectar_db(nombre="taller.db"):
    return sqlite3.connect(nombre)

def crear_tablas():
    conn = conectar_db()
    cursor = conn.cursor()

    # Tabla clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        clave INTEGER PRIMARY KEY AUTOINCREMENT,
        apellidos TEXT NOT NULL,
        nombres TEXT NOT NULL,
        telefono TEXT NOT NULL CHECK(length(telefono) = 10),
        suspendido INTEGER NOT NULL DEFAULT 0
    );
    """)

    # Tabla servicios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicios (
        clave INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        costo REAL NOT NULL CHECK(costo > 0),
        suspendido INTEGER NOT NULL DEFAULT 0
    );
    """)

    # Tabla notas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas (
        folio INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        cliente_clave INTEGER NOT NULL,
        cancelada INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (cliente_clave) REFERENCES clientes(clave)
    );
    """)

    # Tabla detalles_nota
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalles_nota (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folio INTEGER NOT NULL,
        servicio_clave INTEGER NOT NULL,
        observaciones TEXT,
        costo REAL NOT NULL,
        FOREIGN KEY (folio) REFERENCES notas(folio),
        FOREIGN KEY (servicio_clave) REFERENCES servicios(clave)
    );
    """)

    conn.commit()
    conn.close()
    print("Tablas creadas correctamente.")


def registrar_nota():
    conn = sqlite3.connect("taller.db")
    cursor = conn.cursor()

    # Obtener clientes activos ordenados alfabéticamente
    cursor.execute("SELECT clave, apellidos || ' ' || nombres AS nombre_completo FROM clientes WHERE suspendido = 0 ORDER BY apellidos, nombres")
    clientes = cursor.fetchall()
    if not clientes:
        print("No hay clientes activos registrados.")
        conn.close()
        return

    print("\n--- Seleccione un cliente ---")
    for c in clientes:
        print(f"{c[0]} - {c[1]}")

    cliente_clave = input("Ingrese la clave del cliente: ").strip()
    if cliente_clave not in [str(c[0]) for c in clientes]:
        print("Cliente inválido.")
        conn.close()
        return

    # Fecha de la nota
    fecha_input = input("Ingrese la fecha (mm-dd-yyyy) o deje vacío para usar la actual: ").strip()
    try:
        if fecha_input:
            fecha_obj = datetime.strptime(fecha_input, "%m-%d-%Y")
            if fecha_obj > datetime.now():
                raise ValueError("Fecha futura no permitida.")
            fecha = fecha_obj.strftime("%Y-%m-%d")
        else:
            fecha = datetime.now().strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Fecha inválida: {e}")
        conn.close()
        return

    # Generar folio automáticamente
    cursor.execute("SELECT IFNULL(MAX(folio), 0) + 1 FROM notas")
    nuevo_folio = cursor.fetchone()[0]

    # Insertar nota (sin detalles aún)
    cursor.execute("INSERT INTO notas (folio, fecha, cliente_clave, cancelada) VALUES (?, ?, ?, 0)",
                   (nuevo_folio, fecha, cliente_clave))

    # Agregar servicios
    print("\n--- Agregue al menos un servicio ---")
    cursor.execute("SELECT clave, nombre, costo FROM servicios WHERE suspendido = 0 ORDER BY nombre")
    servicios = cursor.fetchall()
    if not servicios:
        print("No hay servicios activos disponibles.")
        conn.rollback()
        conn.close()
        return

    total = 0
    while True:
        for s in servicios:
            print(f"{s[0]} - {s[1]} (${s[2]:.2f})")
        servicio_clave = input("Ingrese clave del servicio (o ENTER para terminar): ").strip()
        if servicio_clave == "" and total > 0:
            break
        elif servicio_clave not in [str(s[0]) for s in servicios]:
            print("Servicio inválido.")
            continue

        observaciones = input("Observaciones (puede quedar vacío): ").strip()
        costo = next(float(s[2]) for s in servicios if str(s[0]) == servicio_clave)
        cursor.execute("INSERT INTO detalles_nota (folio, servicio_clave, observaciones, costo) VALUES (?, ?, ?, ?)",
                       (nuevo_folio, servicio_clave, observaciones, costo))
        total += costo
        print(f"Servicio agregado. Total acumulado: ${total:.2f}")

    conn.commit()
    conn.close()
    print(f"\nNota registrada con folio #{nuevo_folio} y total de ${total:.2f}")


def cancelar_nota():
    conn = conectar_db()
    cursor = conn.cursor()

    # Solicitar folio
    folio = input("Ingrese el folio de la nota que desea cancelar: ").strip()

    # Verificar existencia y que no esté cancelada
    cursor.execute("SELECT folio, fecha, cliente_clave FROM notas WHERE folio = ? AND cancelada = 0", (folio,))
    nota = cursor.fetchone()

    if not nota:
        print("La nota no existe o ya está cancelada.")
        conn.close()
        return

    print(f"\nNota encontrada:")
    print(f"Folio: {nota[0]}")
    print(f"Fecha: {nota[1]}")
    print(f"Cliente Clave: {nota[2]}")

    # Mostrar detalles de la nota
    cursor.execute("""
        SELECT servicio_clave, observaciones, costo
        FROM detalles_nota
        WHERE folio = ?
    """, (folio,))
    detalles = cursor.fetchall()

    if detalles:
        print("\nDetalles de la nota:")
        for i, d in enumerate(detalles, start=1):
            print(f"{i}. Servicio: {d[0]} | Observaciones: {d[1] or '(sin observaciones)'} | Costo: ${d[2]:.2f}")
    else:
        print("Esta nota no tiene detalles registrados.")

    # Confirmar cancelación
    confirmar = input("\n¿Desea cancelar esta nota? (s/n): ").strip().lower()
    if confirmar == "s":
        cursor.execute("UPDATE notas SET cancelada = 1 WHERE folio = ?", (folio,))
        conn.commit()
        print("Nota cancelada correctamente.")
    else:
        print("La nota no fue cancelada.")

    conn.close()


def recuperar_nota():
    conn = conectar_db()
    cursor = conn.cursor()

    # Obtener notas canceladas
    cursor.execute("""
        SELECT folio, fecha, cliente_clave
        FROM notas
        WHERE cancelada = 1
        ORDER BY fecha
    """)
    notas = cursor.fetchall()

    if not notas:
        print("No hay notas canceladas para recuperar.")
        conn.close()
        return

    print("\nNotas canceladas:")
    for n in notas:
        print(f"Folio: {n[0]} | Fecha: {n[1]} | Cliente Clave: {n[2]}")

    folio_input = input("\nIngrese el folio que desea recuperar (o presione ENTER para salir): ").strip()
    if folio_input == "":
        print("ℹNo se recuperó ninguna nota.")
        conn.close()
        return

    cursor.execute("SELECT folio, fecha, cliente_clave FROM notas WHERE folio = ? AND cancelada = 1", (folio_input,))
    nota = cursor.fetchone()

    if not nota:
        print("El folio ingresado no corresponde a una nota cancelada.")
        conn.close()
        return

    print(f"\nNota a recuperar:")
    print(f"Folio: {nota[0]}")
    print(f"Fecha: {nota[1]}")
    print(f"Cliente Clave: {nota[2]}")

    # Mostrar detalles
    cursor.execute("""
        SELECT servicio_clave, observaciones, costo
        FROM detalles_nota
        WHERE folio = ?
    """, (folio_input,))
    detalles = cursor.fetchall()

    if detalles:
        print("\nDetalles de la nota:")
        for i, d in enumerate(detalles, start=1):
            print(f"{i}. Servicio: {d[0]} | Observaciones: {d[1] or '(sin observaciones)'} | Costo: ${d[2]:.2f}")
    else:
        print("Esta nota no tiene detalles registrados.")

    confirmar = input("\n¿Desea recuperar esta nota? (s/n): ").strip().lower()
    if confirmar == "s":
        cursor.execute("UPDATE notas SET cancelada = 0 WHERE folio = ?", (folio_input,))
        conn.commit()
        print("Nota recuperada correctamente.")
    else:
        print("ℹLa nota no fue recuperada.")

    conn.close()




def menu_consultas_reportes():
    while True:
        print("\nCONSULTAS Y REPORTES")
        print("1. Consultar por período")
        print("2. Consultar por folio")
        print("3. Reporte total de clientes")
        print("4. Reporte total de servicios")
        print("5. Volver al menú principal")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            consulta_por_periodo()
        elif opcion == "2":
            consulta_por_folio()
        elif opcion == "3":
            reporte_total_clientes()
        elif opcion == "4":
            reporte_total_servicios()
        elif opcion == "5":
            break
        else:
            print("Opción no válida.\n")


def consulta_por_periodo():
    conn = conectar_db()
    cursor = conn.cursor()

    fecha_inicio = input("Ingrese la fecha inicial (MM-DD-YYYY) o presione ENTER para usar la más antigua: ").strip()
    if fecha_inicio == "":
        cursor.execute("SELECT MIN(fecha) FROM notas WHERE cancelada = 0")
        resultado = cursor.fetchone()[0]
        if resultado:
            fecha_inicio = resultado
            print(f"Fecha inicial usada: {fecha_inicio}")
        else:
            print("No hay notas registradas.")
            conn.close()
            return
    else:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha inicial inválida.")
            conn.close()
            return

    fecha_fin = input("Ingrese la fecha final (MM-DD-YYYY) o presione ENTER para usar la fecha actual: ").strip()
    if fecha_fin == "":
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
        print(f"Fecha final usada: {fecha_fin}")
    else:
        try:
            fecha_fin = datetime.strptime(fecha_fin, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha final inválida.")
            conn.close()
            return

    cursor.execute("""
        SELECT n.folio, n.fecha, n.cliente_clave,
               IFNULL(SUM(d.costo), 0) as total
        FROM notas n
        LEFT JOIN detalles_nota d ON n.folio = d.folio
        WHERE n.cancelada = 0 AND n.fecha BETWEEN ? AND ?
        GROUP BY n.folio
        ORDER BY n.fecha;
    """, (fecha_inicio, fecha_fin))

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print("No hay notas emitidas para el período seleccionado.")
    else:
        df = pd.DataFrame(resultados, columns=["Folio", "Fecha", "Cliente Clave", "Total"])
        print(df)

        exportar = input("¿Desea exportar el reporte a Excel? (s/n): ").strip().lower()
        if exportar == "s":
            df.to_excel("reporte_notas_periodo.xlsx", index=False)
            print("Reporte exportado como 'reporte_notas_periodo.xlsx'")


#### 2
def reporte_total_clientes():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT clave, apellidos, nombres, telefono,
               CASE suspendido WHEN 0 THEN 'Activo' ELSE 'Suspendido' END AS estado
        FROM clientes
        ORDER BY clave
    """)
    clientes = cursor.fetchall()
    conn.close()

    if not clientes:
        print("No hay clientes registrados.")
    else:
        df = pd.DataFrame(clientes, columns=["Clave", "Apellidos", "Nombres", "Teléfono", "Estado"])
        print(df)

        exportar = input("¿Desea exportar el reporte a Excel? (s/n): ").strip().lower()
        if exportar == "s":
            df.to_excel("Python3ero/reporte_clientes.xlsx", index=False)
            print("Reporte exportado como 'reporte_clientes.xlsx'")


### 3

def reporte_total_servicios():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT clave, nombre, costo,
               CASE suspendido WHEN 0 THEN 'Activo' ELSE 'Suspendido' END AS estado
        FROM servicios
        ORDER BY nombre
    """)
    servicios = cursor.fetchall()
    conn.close()

    if not servicios:
        print("No hay servicios registrados.")
    else:
        df = pd.DataFrame(servicios, columns=["Clave", "Nombre del Servicio", "Costo", "Estado"])
        print(df)

        exportar = input("¿Desea exportar el reporte a Excel? (s/n): ").strip().lower()
        if exportar == "s":
            df.to_excel("reporte_servicios.xlsx", index=False)
            print("Reporte exportado como 'reporte_servicios.xlsx'")


### 4

def consulta_por_folio():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("SELECT folio, fecha FROM notas WHERE cancelada = 0 ORDER BY fecha")
    folios = cursor.fetchall()

    if not folios:
        print("No hay notas activas registradas.")
        conn.close()
        return

    print("\nFolios disponibles:")
    for folio, fecha in folios:
        print(f"Folio: {folio} | Fecha: {fecha}")

    folio_input = input("\nIngrese el folio que desea consultar: ").strip()

    cursor.execute("SELECT folio, fecha, cliente_clave FROM notas WHERE folio = ? AND cancelada = 0", (folio_input,))
    nota = cursor.fetchone()

    if not nota:
        print("El folio indicado no existe o corresponde a una nota cancelada.")
        conn.close()
        return

    print(f"\nNota encontrada:")
    print(f"Folio: {nota[0]}")
    print(f"Fecha: {nota[1]}")
    print(f"Cliente Clave: {nota[2]}")

    cursor.execute("""
        SELECT servicio_clave, observaciones, costo
        FROM detalles_nota
        WHERE folio = ?
    """, (folio_input,))
    detalles = cursor.fetchall()
    conn.close()

    if detalles:
        print("\nDetalles del servicio:")
        for i, d in enumerate(detalles, start=1):
            print(f"{i}. Servicio: {d[0]} | Observaciones: {d[1] or '(sin observaciones)'} | Costo: ${d[2]:.2f}")
    else:
        print("Esta nota no tiene detalles registrados.")


def menu_analisis_estadistico():
    while True:
        print("\nANÁLISIS ESTADÍSTICO")
        print("1. Análisis de los totales por nota")
        print("2. Análisis de patrones")
        print("3. Regresar al menú anterior")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            menu_analisis_totales()
        elif opcion == "2":
            menu_analisis_patrones()
        elif opcion == "3":
            break
        else:
            print("Opción no válida.\n")

def menu_mantenimiento_datos():
    while True:
        print("\n🛠 MANTENIMIENTO DE DATOS")
        print("1. Clientes")
        print("2. Servicios")
        print("3. Regresar al menú principal")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            menu_clientes()
        elif opcion == "2":
            menu_servicios()
        elif opcion == "3":
            break
        else:
            print("Opción no válida.\n")

def menu_analisis_totales():
    while True:
        print("\n--- ANÁLISIS DE LOS TOTALES POR NOTA ---")
        print("1. Tendencias centrales")
        print("2. Dispersión y distribución")
        print("3. Volver al menú principal")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            estadistica_tendencia_central()
        elif opcion == "2":
            estadistica_dispersion()
        elif opcion == "3":
            break
        else:
            print("Opción no válida.")

def estadistica_tendencia_central():
    conn = conectar_db()
    cursor = conn.cursor()

    # Pedir fecha inicial
    fecha_inicio = input("Ingrese la fecha inicial (MM-DD-YYYY) o presione ENTER para usar la más antigua: ").strip()
    if fecha_inicio == "":
        cursor.execute("SELECT MIN(fecha) FROM notas WHERE cancelada = 0")
        resultado = cursor.fetchone()[0]
        if resultado:
            fecha_inicio = resultado
            print(f"Fecha inicial usada: {fecha_inicio}")
        else:
            print("No hay notas registradas.")
            conn.close()
            return
    else:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha inicial inválida.")
            conn.close()
            return

    # Pedir fecha final
    fecha_fin = input("Ingrese la fecha final (MM-DD-YYYY) o presione ENTER para usar la actual: ").strip()
    if fecha_fin == "":
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
        print(f"Fecha final usada: {fecha_fin}")
    else:
        try:
            fecha_fin = datetime.strptime(fecha_fin, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha final inválida.")
            conn.close()
            return

    # Obtener totales de notas
    cursor.execute("""
        SELECT SUM(d.costo) as total
        FROM notas n
        JOIN detalles_nota d ON n.folio = d.folio
        WHERE n.cancelada = 0 AND n.fecha BETWEEN ? AND ?
        GROUP BY n.folio
    """, (fecha_inicio, fecha_fin))

    resultados = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not resultados:
        print("No hay notas emitidas en ese período.")
        return

    # Calcular estadísticas
    conteo = len(resultados)
    promedio = mean(resultados)
    mediana_valor = median(resultados)
    modas = multimode(resultados)

    print("\nEstadísticos de tendencia central:")
    print(f"Conteo de notas: {conteo}")
    print(f"Media aritmética: {promedio:.2f}")
    print(f"Mediana: {mediana_valor:.2f}")
    print(f"Moda(s): {', '.join(f'{m:.2f}' for m in modas)}")



def estadistica_dispersion():
    conn = conectar_db()
    cursor = conn.cursor()

    # Pedir fecha inicial
    fecha_inicio = input("Ingrese la fecha inicial (MM-DD-YYYY) o presione ENTER para usar la más antigua: ").strip()
    if fecha_inicio == "":
        cursor.execute("SELECT MIN(fecha) FROM notas WHERE cancelada = 0")
        resultado = cursor.fetchone()[0]
        if resultado:
            fecha_inicio = resultado
            print(f"Fecha inicial usada: {fecha_inicio}")
        else:
            print("No hay notas registradas.")
            conn.close()
            return
    else:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha inicial inválida.")
            conn.close()
            return

    # Pedir fecha final
    fecha_fin = input("Ingrese la fecha final (MM-DD-YYYY) o presione ENTER para usar la actual: ").strip()
    if fecha_fin == "":
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
        print(f"Fecha final usada: {fecha_fin}")
    else:
        try:
            fecha_fin = datetime.strptime(fecha_fin, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha final inválida.")
            conn.close()
            return

    # Obtener totales por nota
    cursor.execute("""
        SELECT SUM(d.costo) as total
        FROM notas n
        JOIN detalles_nota d ON n.folio = d.folio
        WHERE n.cancelada = 0 AND n.fecha BETWEEN ? AND ?
        GROUP BY n.folio
    """, (fecha_inicio, fecha_fin))

    resultados = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not resultados or len(resultados) < 2:
        print("No hay suficientes notas para calcular dispersión (se requiere al menos 2).")
        return

    serie = pd.Series(resultados)

    # Cálculos
    varianza = variance(resultados)
    desviacion = stdev(resultados)
    q1 = serie.quantile(0.25)
    q2 = serie.quantile(0.50)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1

    # Mostrar reporte
    print("\nEstadísticos de dispersión y distribución:")
    print(f"Varianza: {varianza:.2f}")
    print(f"Desviación estándar: {desviacion:.2f}")
    print(f"Primer cuartil (Q1): {q1:.2f}")
    print(f"Mediana (Q2): {q2:.2f}")
    print(f"Tercer cuartil (Q3): {q3:.2f}")
    print(f"Rango intercuartílico (IQR): {iqr:.2f}")


def menu_analisis_patrones():
    while True:
        print("\nANÁLISIS DE PATRONES")
        print("1. Servicio más prestado por período")
        print("2. Cliente con más servicios por período")
        print("3. Regresar al menú anterior")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            servicio_mas_prestado()
        elif opcion == "2":
            cliente_con_mas_servicios()
        elif opcion == "3":
            break
        else:
            print("Opción no válida.\n")

def servicio_mas_prestado():
    conn = conectar_db()
    cursor = conn.cursor()

    # Pedir fechas
    fecha_inicio = input("Ingrese la fecha inicial (MM-DD-YYYY) o ENTER para usar la más antigua: ").strip()
    if fecha_inicio == "":
        cursor.execute("SELECT MIN(fecha) FROM notas WHERE cancelada = 0")
        resultado = cursor.fetchone()[0]
        if resultado:
            fecha_inicio = resultado
            print(f"Fecha inicial usada: {fecha_inicio}")
        else:
            print("No hay notas registradas.")
            conn.close()
            return
    else:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha inicial inválida.")
            conn.close()
            return

    fecha_fin = input("Ingrese la fecha final (MM-DD-YYYY) o ENTER para usar la actual: ").strip()
    if fecha_fin == "":
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            fecha_fin = datetime.strptime(fecha_fin, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha final inválida.")
            conn.close()
            return

    # Consulta: los 3 servicios más prestados
    cursor.execute("""
        SELECT s.clave, s.nombre, COUNT(*) AS veces
        FROM notas n
        JOIN detalles_nota d ON n.folio = d.folio
        JOIN servicios s ON d.servicio_clave = s.clave
        WHERE n.cancelada = 0 AND n.fecha BETWEEN ? AND ?
        GROUP BY s.clave, s.nombre
        ORDER BY veces ASC
        LIMIT 3
    """, (fecha_inicio, fecha_fin))

    servicios = cursor.fetchall()
    conn.close()

    if not servicios:
        print("No se encontraron servicios prestados en ese período.")
    else:
        print("\nServicios más prestados:")
        print("{:<10} {:<30} {:>10}".format("Clave", "Servicio", "Veces"))
        for s in servicios:
            print("{:<10} {:<30} {:>10}".format(s[0], s[1], s[2]))

def cliente_con_mas_servicios():
    conn = conectar_db()
    cursor = conn.cursor()

    # Pedir fechas
    fecha_inicio = input("Ingrese la fecha inicial (MM-DD-YYYY) o ENTER para usar la más antigua: ").strip()
    if fecha_inicio == "":
        cursor.execute("SELECT MIN(fecha) FROM notas WHERE cancelada = 0")
        resultado = cursor.fetchone()[0]
        if resultado:
            fecha_inicio = resultado
            print(f"Fecha inicial usada: {fecha_inicio}")
        else:
            print("No hay notas registradas.")
            conn.close()
            return
    else:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha inicial inválida.")
            conn.close()
            return

    fecha_fin = input("Ingrese la fecha final (MM-DD-YYYY) o ENTER para usar la actual: ").strip()
    if fecha_fin == "":
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            fecha_fin = datetime.strptime(fecha_fin, "%m-%d-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Fecha final inválida.")
            conn.close()
            return

    # Consulta: los 3 clientes con más servicios solicitados
    cursor.execute("""
        SELECT c.clave, c.apellidos || ' ' || c.nombres AS nombre_completo, COUNT(*) AS total_servicios
        FROM notas n
        JOIN detalles_nota d ON n.folio = d.folio
        JOIN clientes c ON n.cliente_clave = c.clave
        WHERE n.cancelada = 0 AND n.fecha BETWEEN ? AND ?
        GROUP BY c.clave, nombre_completo
        ORDER BY total_servicios ASC
        LIMIT 3
    """, (fecha_inicio, fecha_fin))

    clientes = cursor.fetchall()
    conn.close()

    if not clientes:
        print("No se encontraron servicios solicitados en ese período.")
    else:
        print("\nClientes con más servicios:")
        print("{:<10} {:<30} {:>10}".format("Clave", "Cliente", "Servicios"))
        for c in clientes:
            print("{:<10} {:<30} {:>10}".format(c[0], c[1], c[2]))

def menu_clientes():
    while True:
        print("\nCLIENTES")
        print("1. Altas de clientes")
        print("2. Bajas de clientes")
        print("3. Edición de clientes")
        print("4. Regresar al menú anterior")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            alta_cliente()
        elif opcion == "2":
            baja_cliente()
        elif opcion == "3":
            editar_cliente()
        elif opcion == "4":
            break
        else:
            print("Opción no válida.\n")

def alta_cliente():
    conn = conectar_db()
    cursor = conn.cursor()

    apellidos = input("Ingrese apellidos (sin números): ").strip()
    if not apellidos.replace(" ", "").isalpha():
        print("Apellidos inválidos.")
        conn.close()
        return

    nombres = input("Ingrese nombres (sin números): ").strip()
    if not nombres.replace(" ", "").isalpha():
        print("Nombres inválidos.")
        conn.close()
        return

    telefono = input("Ingrese teléfono (10 dígitos sin espacios): ").strip()
    if not (telefono.isdigit() and len(telefono) == 10):
        print("Número telefónico inválido.")
        conn.close()
        return

    cursor.execute("""
        INSERT INTO clientes (apellidos, nombres, telefono, suspendido)
        VALUES (?, ?, ?, 0)
    """, (apellidos, nombres, telefono))
    conn.commit()
    print("Cliente registrado correctamente.")
    conn.close()


def baja_cliente():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT clave, apellidos, nombres FROM clientes
        WHERE suspendido = 0
        ORDER BY apellidos, nombres
    """)
    clientes = cursor.fetchall()

    if not clientes:
        print("No hay clientes activos para suspender.")
        conn.close()
        return

    print("\nClientes activos:")
    for c in clientes:
        print(f"Clave: {c[0]} | Nombre: {c[1]} {c[2]}")

    clave = input("\nIngrese la clave del cliente a suspender: ").strip()
    if clave not in [str(c[0]) for c in clientes]:
        print("Clave inválida.")
        conn.close()
        return

    confirmar = input("¿Está seguro que desea suspender a este cliente? (s/n): ").strip().lower()
    if confirmar == "s":
        cursor.execute("UPDATE clientes SET suspendido = 1 WHERE clave = ?", (clave,))
        conn.commit()
        print("Cliente suspendido correctamente.")
    else:
        print("Operación cancelada.")

    conn.close()


def editar_cliente():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT clave, apellidos, nombres FROM clientes
        WHERE suspendido = 0
        ORDER BY apellidos, nombres
    """)
    clientes = cursor.fetchall()

    if not clientes:
        print("No hay clientes activos para editar.")
        conn.close()
        return

    print("\nClientes activos:")
    for c in clientes:
        print(f"Clave: {c[0]} | Nombre: {c[1]} {c[2]}")

    clave = input("\nIngrese la clave del cliente a editar: ").strip()
    if clave not in [str(c[0]) for c in clientes]:
        print("Clave inválida.")
        conn.close()
        return

    confirmar = input("¿Desea editar este cliente? (s/n): ").strip().lower()
    if confirmar != "s":
        print("Edición cancelada.")
        conn.close()
        return

    # Nuevos datos
    apellidos = input("Nuevo apellidos: ").strip()
    if not apellidos.replace(" ", "").isalpha():
        print("Apellidos inválidos.")
        conn.close()
        return

    nombres = input("Nuevo nombres: ").strip()
    if not nombres.replace(" ", "").isalpha():
        print("Nombres inválidos.")
        conn.close()
        return

    telefono = input("Nuevo teléfono (10 dígitos): ").strip()
    if not (telefono.isdigit() and len(telefono) == 10):
        print("Teléfono inválido.")
        conn.close()
        return

    cursor.execute("""
        UPDATE clientes SET apellidos = ?, nombres = ?, telefono = ?
        WHERE clave = ?
    """, (apellidos, nombres, telefono, clave))
    conn.commit()
    print("Cliente actualizado correctamente.")
    conn.close()


def menu_servicios():
    while True:
        print("\n SERVICIOS")
        print("1. Alta de servicios")
        print("2. Baja de servicios")
        print("3. Edición de servicios")
        print("4. Regresar al menú anterior")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            alta_servicio()
        elif opcion == "2":
            baja_servicio()
        elif opcion == "3":
            editar_servicio()
        elif opcion == "4":
            break
        else:
            print("Opción no válida.\n")

def alta_servicio():
    conn = conectar_db()
    cursor = conn.cursor()

    nombre = input("Ingrese el nombre del servicio: ").strip()
    if not nombre:
        print("El nombre no puede estar vacío.")
        conn.close()
        return

    try:
        costo = float(input("Ingrese el costo del servicio: ").strip())
        if costo <= 0:
            raise ValueError
    except ValueError:
        print("Costo inválido. Debe ser un número mayor que cero.")
        conn.close()
        return

    cursor.execute("""
        INSERT INTO servicios (nombre, costo, suspendido)
        VALUES (?, ?, 0)
    """, (nombre, costo))
    conn.commit()
    print("Servicio registrado correctamente.")
    conn.close()


def baja_servicio():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT clave, nombre FROM servicios
        WHERE suspendido = 0
        ORDER BY nombre
    """)
    servicios = cursor.fetchall()

    if not servicios:
        print("No hay servicios activos para suspender.")
        conn.close()
        return

    print("\nServicios activos:")
    for s in servicios:
        print(f"Clave: {s[0]} | Nombre: {s[1]}")

    clave = input("\nIngrese la clave del servicio a suspender: ").strip()
    if clave not in [str(s[0]) for s in servicios]:
        print("Clave inválida.")
        conn.close()
        return

    confirmar = input("¿Está seguro que desea suspender este servicio? (s/n): ").strip().lower()
    if confirmar == "s":
        cursor.execute("UPDATE servicios SET suspendido = 1 WHERE clave = ?", (clave,))
        conn.commit()
        print("Servicio suspendido correctamente.")
    else:
        print("Operación cancelada.")

    conn.close()


def editar_servicio():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT clave, nombre FROM servicios
        WHERE suspendido = 0
        ORDER BY nombre
    """)
    servicios = cursor.fetchall()

    if not servicios:
        print("No hay servicios activos para editar.")
        conn.close()
        return

    print("\nServicios activos:")
    for s in servicios:
        print(f"Clave: {s[0]} | Nombre: {s[1]}")

    clave = input("\nIngrese la clave del servicio a editar: ").strip()
    if clave not in [str(s[0]) for s in servicios]:
        print("Clave inválida.")
        conn.close()
        return

    confirmar = input("¿Desea editar este servicio? (s/n): ").strip().lower()
    if confirmar != "s":
        print("Edición cancelada.")
        conn.close()
        return

    nombre = input("Nuevo nombre del servicio: ").strip()
    if not nombre:
        print("Nombre inválido.")
        conn.close()
        return

    try:
        costo = float(input("Nuevo costo del servicio: ").strip())
        if costo <= 0:
            raise ValueError
    except ValueError:
        print("Costo inválido.")
        conn.close()
        return

    cursor.execute("""
        UPDATE servicios SET nombre = ?, costo = ?
        WHERE clave = ?
    """, (nombre, costo, clave))
    conn.commit()
    print("Servicio actualizado correctamente.")
    conn.close()

def mainMenu():
    while True:
        print("\nMENÚ PRINCIPAL")
        print("1. Registrar una nota")
        print("2. Consultas y reportes")
        print("3. Cancelar una nota")
        print("4. Recuperar una nota")
        print("5. Análisis estadísticos")
        print("6. Mantenimiento de datos")
        print("7. Salir")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            registrar_nota()
        elif opcion == "2":
            menu_consultas_reportes()
        elif opcion == "3":
            cancelar_nota()
        elif opcion == "4":
            recuperar_nota()
        elif opcion == "5":
            menu_analisis_estadistico()
        elif opcion == "6":
            menu_mantenimiento_datos()
        elif opcion == "7":
            confirmar = input("¿Está seguro que desea salir? (s/n): ").strip().lower()
            if confirmar == "s":
                print("Saliendo del sistema.")
                break
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    crear_tablas()
    mainMenu()