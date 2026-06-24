from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timezone
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sipm-rp-pg-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///registros.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class RegistroProduccion(db.Model):
    __tablename__ = 'registro_produccion'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    turno = db.Column(db.String(20), nullable=False)
    producto = db.Column(db.String(100), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    cantidad_producida = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(20), nullable=False, default='kg')
    cantidad_rechazada = db.Column(db.Float, nullable=False, default=0.0)
    linea = db.Column(db.String(50), nullable=False)
    operador = db.Column(db.String(100), nullable=False)
    supervisor = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    actualizado_en = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def eficiencia(self):
        if self.cantidad_producida > 0:
            return round((1 - self.cantidad_rechazada / self.cantidad_producida) * 100, 2)
        return 0.0

    def __repr__(self):
        return f'<RegistroProduccion {self.id} - {self.producto} - {self.fecha}>'


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    turno = request.args.get('turno', '')
    producto = request.args.get('producto', '')

    query = RegistroProduccion.query

    if fecha_desde:
        try:
            query = query.filter(RegistroProduccion.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date())
        except ValueError:
            pass

    if fecha_hasta:
        try:
            query = query.filter(RegistroProduccion.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
        except ValueError:
            pass

    if turno:
        query = query.filter(RegistroProduccion.turno == turno)

    if producto:
        query = query.filter(RegistroProduccion.producto.ilike(f'%{producto}%'))

    registros = query.order_by(RegistroProduccion.fecha.desc(), RegistroProduccion.id.desc()).all()

    return render_template('index.html', registros=registros,
                           fecha_desde=fecha_desde or '',
                           fecha_hasta=fecha_hasta or '',
                           turno=turno, producto=producto)


@app.route('/nuevo', methods=['GET', 'POST'])
def nuevo_registro():
    if request.method == 'POST':
        try:
            fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            cantidad_producida = float(request.form['cantidad_producida'])
            cantidad_rechazada = float(request.form.get('cantidad_rechazada', 0) or 0)

            if cantidad_producida <= 0:
                flash('La cantidad producida debe ser mayor a cero.', 'danger')
                return render_template('nuevo_registro.html', form_data=request.form)

            if cantidad_rechazada < 0:
                flash('La cantidad rechazada no puede ser negativa.', 'danger')
                return render_template('nuevo_registro.html', form_data=request.form)

            if cantidad_rechazada > cantidad_producida:
                flash('La cantidad rechazada no puede superar la cantidad producida.', 'danger')
                return render_template('nuevo_registro.html', form_data=request.form)

            registro = RegistroProduccion(
                fecha=fecha,
                turno=request.form['turno'],
                producto=request.form['producto'].strip(),
                lote=request.form['lote'].strip(),
                cantidad_producida=cantidad_producida,
                unidad=request.form['unidad'],
                cantidad_rechazada=cantidad_rechazada,
                linea=request.form['linea'].strip(),
                operador=request.form['operador'].strip(),
                supervisor=request.form.get('supervisor', '').strip() or None,
                observaciones=request.form.get('observaciones', '').strip() or None,
            )
            db.session.add(registro)
            db.session.commit()
            flash(f'Registro #{registro.id} creado exitosamente.', 'success')
            return redirect(url_for('index'))

        except (ValueError, KeyError) as e:
            flash('Error en los datos ingresados. Por favor revise el formulario.', 'danger')
            return render_template('nuevo_registro.html', form_data=request.form)

    return render_template('nuevo_registro.html', form_data={})


@app.route('/editar/<int:registro_id>', methods=['GET', 'POST'])
def editar_registro(registro_id):
    registro = db.session.get(RegistroProduccion, registro_id)
    if registro is None:
        return render_template('404.html'), 404

    if request.method == 'POST':
        try:
            fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            cantidad_producida = float(request.form['cantidad_producida'])
            cantidad_rechazada = float(request.form.get('cantidad_rechazada', 0) or 0)

            if cantidad_producida <= 0:
                flash('La cantidad producida debe ser mayor a cero.', 'danger')
                return render_template('editar_registro.html', registro=registro)

            if cantidad_rechazada < 0:
                flash('La cantidad rechazada no puede ser negativa.', 'danger')
                return render_template('editar_registro.html', registro=registro)

            if cantidad_rechazada > cantidad_producida:
                flash('La cantidad rechazada no puede superar la cantidad producida.', 'danger')
                return render_template('editar_registro.html', registro=registro)

            registro.fecha = fecha
            registro.turno = request.form['turno']
            registro.producto = request.form['producto'].strip()
            registro.lote = request.form['lote'].strip()
            registro.cantidad_producida = cantidad_producida
            registro.unidad = request.form['unidad']
            registro.cantidad_rechazada = cantidad_rechazada
            registro.linea = request.form['linea'].strip()
            registro.operador = request.form['operador'].strip()
            registro.supervisor = request.form.get('supervisor', '').strip() or None
            registro.observaciones = request.form.get('observaciones', '').strip() or None
            registro.actualizado_en = datetime.now(timezone.utc)

            db.session.commit()
            flash(f'Registro #{registro.id} actualizado exitosamente.', 'success')
            return redirect(url_for('index'))

        except (ValueError, KeyError):
            flash('Error en los datos ingresados. Por favor revise el formulario.', 'danger')
            return render_template('editar_registro.html', registro=registro)

    return render_template('editar_registro.html', registro=registro)


@app.route('/eliminar/<int:registro_id>', methods=['POST'])
def eliminar_registro(registro_id):
    registro = db.session.get(RegistroProduccion, registro_id)
    if registro is None:
        return render_template('404.html'), 404
    db.session.delete(registro)
    db.session.commit()
    flash(f'Registro #{registro_id} eliminado exitosamente.', 'success')
    return redirect(url_for('index'))


@app.route('/detalle/<int:registro_id>')
def detalle_registro(registro_id):
    registro = db.session.get(RegistroProduccion, registro_id)
    if registro is None:
        return render_template('404.html'), 404
    return render_template('detalle_registro.html', registro=registro)


@app.route('/exportar')
def exportar_csv():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    turno = request.args.get('turno', '')
    producto = request.args.get('producto', '')

    query = RegistroProduccion.query

    if fecha_desde:
        try:
            query = query.filter(RegistroProduccion.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date())
        except ValueError:
            pass

    if fecha_hasta:
        try:
            query = query.filter(RegistroProduccion.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
        except ValueError:
            pass

    if turno:
        query = query.filter(RegistroProduccion.turno == turno)

    if producto:
        query = query.filter(RegistroProduccion.producto.ilike(f'%{producto}%'))

    registros = query.order_by(RegistroProduccion.fecha.desc(), RegistroProduccion.id.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Fecha', 'Turno', 'Producto', 'Lote',
        'Cantidad Producida', 'Unidad', 'Cantidad Rechazada',
        'Eficiencia (%)', 'Línea', 'Operador', 'Supervisor', 'Observaciones'
    ])

    for r in registros:
        writer.writerow([
            r.id, r.fecha.strftime('%d/%m/%Y'), r.turno, r.producto, r.lote,
            r.cantidad_producida, r.unidad, r.cantidad_rechazada,
            r.eficiencia, r.linea, r.operador, r.supervisor or '', r.observaciones or ''
        ])

    output.seek(0)
    nombre_archivo = f'registro_produccion_pg_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=nombre_archivo
    )


import os

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1')
