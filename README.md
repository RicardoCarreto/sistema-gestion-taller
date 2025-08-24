
# 📊 Taller de Gestión de Notas y Servicios  

Este proyecto es un **sistema de gestión de notas, clientes y servicios** desarrollado en **Python** con **SQLite** y **pandas**.  
Permite registrar notas de servicio, administrar clientes/servicios, generar reportes, y realizar análisis estadísticos sobre los datos registrados.  

---

## ✨ Funcionalidades

✅ **Gestión de clientes**  
- Alta, baja (suspensión) y edición de clientes.  
- Validación de datos (nombres, teléfono, etc.).  

✅ **Gestión de servicios**  
- Alta, baja y edición de servicios.  
- Control de costos y estado (activo/suspendido).  

✅ **Notas de servicio**  
- Registro de notas con fecha, cliente y servicios agregados.  
- Cancelación y recuperación de notas.  
- Folios generados automáticamente.  

✅ **Consultas y reportes**  
- Reportes por período o por folio.  
- Reporte completo de clientes y servicios.  
- Exportación de reportes a **Excel**.  

✅ **Análisis estadístico**  
- Tendencias centrales: media, mediana, moda.  
- Dispersión: varianza, desviación estándar, cuartiles e IQR.  
- Patrones: clientes con más servicios, servicios más prestados.  

---

## 🛠 Tecnologías utilizadas
- **Python 3.x**  
- **SQLite3** (base de datos local)  
- **pandas** (manejo de reportes y análisis estadístico)  
- **openpyxl** (exportación a Excel)  

---

## 📂 Estructura del proyecto
```
📦 proyecto_taller
 ┣ 📂 Python3ero/        # Carpeta con la base de datos y reportes
 ┃ ┗ 📜 taller.db        # Base de datos SQLite
 ┣ 📜 main.py            # Código principal del sistema
 ┣ 📜 README.md          # Este archivo
```

---

## 🚀 Ejecución
1. Clonar el repositorio:  
   ```bash
   git clone https://github.com/tuusuario/proyecto_taller.git
   cd proyecto_taller
   ```
2. Instalar dependencias necesarias:  
   ```bash
   pip install pandas openpyxl
   ```
3. Ejecutar el sistema:  
   ```bash
   python main.py
   ```

---

## 📊 Ejemplo de uso
- Al iniciar, se crean automáticamente las tablas en la base de datos (`taller.db`).  
- Desde el menú principal puedes:  
  - Registrar notas.  
  - Cancelar/recuperar notas.  
  - Consultar reportes y exportarlos.  
  - Administrar clientes y servicios.  
  - Realizar análisis estadístico.  

---

## 🔮 Posibles mejoras
- Interfaz gráfica (Tkinter o PyQt).  
- Generación de reportes en PDF.  
- Implementar autenticación de usuarios.  
- Integración con un servidor web (Flask/Django).  
