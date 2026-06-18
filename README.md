# SIPM_RP_PG

Sistema de Información de Producción y Manufactura — Registro de Producción PG

## Descripción

Aplicación web para el registro y seguimiento de producción. Permite registrar, consultar, editar y exportar registros de producción por turno, producto, lote y línea de producción.

## Características

- **Registro de producción**: Captura de datos por turno (Mañana / Tarde / Noche), producto, lote, línea, operador y supervisor.
- **Cantidades y eficiencia**: Registro de cantidad producida, cantidad rechazada y cálculo automático de eficiencia.
- **Filtros**: Búsqueda por rango de fechas, turno y producto.
- **Resumen**: Totales de producción, rechazo y eficiencia promedio en la vista de listado.
- **Exportar CSV**: Descarga de los registros filtrados en formato CSV (compatible con Excel).
- **CRUD completo**: Crear, ver detalle, editar y eliminar registros.

## Tecnologías

- Python 3.12+
- Flask 3.x
- Flask-SQLAlchemy (SQLite)
- Bootstrap 5.3

## Instalación y ejecución

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python app.py
```

Abrir en el navegador: http://localhost:5000

## Ejecutar pruebas

```bash
pip install pytest
python -m pytest tests/ -v
```
