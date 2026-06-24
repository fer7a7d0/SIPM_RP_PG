import pytest
from datetime import date
from app import app, db, RegistroProduccion


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


@pytest.fixture
def registro_ejemplo(client):
    with app.app_context():
        r = RegistroProduccion(
            fecha=date(2024, 1, 15),
            turno='Mañana',
            producto='Polietileno PG-100',
            lote='LOT-2024-001',
            cantidad_producida=1000.0,
            unidad='kg',
            cantidad_rechazada=20.0,
            linea='Línea 1',
            operador='Juan García',
            supervisor='Pedro López',
            observaciones='Sin incidencias',
        )
        db.session.add(r)
        db.session.commit()
        return r.id


class TestModelo:
    def test_eficiencia_con_rechazos(self, client):
        with app.app_context():
            r = RegistroProduccion(
                fecha=date(2024, 1, 15),
                turno='Mañana',
                producto='Producto A',
                lote='LOT-001',
                cantidad_producida=100.0,
                unidad='kg',
                cantidad_rechazada=5.0,
                linea='Línea 1',
                operador='Operador A',
            )
            assert r.eficiencia == 95.0

    def test_eficiencia_sin_rechazos(self, client):
        with app.app_context():
            r = RegistroProduccion(
                fecha=date(2024, 1, 15),
                turno='Mañana',
                producto='Producto B',
                lote='LOT-002',
                cantidad_producida=200.0,
                unidad='kg',
                cantidad_rechazada=0.0,
                linea='Línea 1',
                operador='Operador B',
            )
            assert r.eficiencia == 100.0

    def test_eficiencia_sin_produccion(self, client):
        with app.app_context():
            r = RegistroProduccion(
                fecha=date(2024, 1, 15),
                turno='Mañana',
                producto='Producto C',
                lote='LOT-003',
                cantidad_producida=0.0,
                unidad='kg',
                cantidad_rechazada=0.0,
                linea='Línea 1',
                operador='Operador C',
            )
            assert r.eficiencia == 0.0


class TestVistaIndex:
    def test_index_sin_registros(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert 'No hay registros disponibles' in response.data.decode('utf-8')

    def test_index_con_registros(self, client, registro_ejemplo):
        response = client.get('/')
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'Polietileno PG-100' in data
        assert 'LOT-2024-001' in data

    def test_index_filtro_turno(self, client, registro_ejemplo):
        response = client.get('/?turno=Tarde')
        assert response.status_code == 200
        assert 'Polietileno PG-100' not in response.data.decode('utf-8')

    def test_index_filtro_producto(self, client, registro_ejemplo):
        response = client.get('/?producto=Polietileno')
        assert response.status_code == 200
        assert 'Polietileno PG-100' in response.data.decode('utf-8')

    def test_index_filtro_producto_no_encontrado(self, client, registro_ejemplo):
        response = client.get('/?producto=INEXISTENTE')
        assert response.status_code == 200
        assert 'No hay registros disponibles' in response.data.decode('utf-8')


class TestNuevoRegistro:
    def test_get_formulario(self, client):
        response = client.get('/nuevo')
        assert response.status_code == 200
        assert 'Nuevo Registro de Producción' in response.data.decode('utf-8')

    def test_crear_registro_exitoso(self, client):
        data = {
            'fecha': '2024-02-01',
            'turno': 'Tarde',
            'producto': 'Producto Test',
            'lote': 'LOT-TEST-001',
            'cantidad_producida': '500',
            'unidad': 'kg',
            'cantidad_rechazada': '10',
            'linea': 'Línea 2',
            'operador': 'Test Operador',
            'supervisor': 'Test Supervisor',
            'observaciones': 'Prueba',
        }
        response = client.post('/nuevo', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert 'creado exitosamente' in response.data.decode('utf-8')

    def test_crear_registro_cantidad_negativa(self, client):
        data = {
            'fecha': '2024-02-01',
            'turno': 'Mañana',
            'producto': 'Producto Test',
            'lote': 'LOT-TEST-002',
            'cantidad_producida': '-100',
            'unidad': 'kg',
            'cantidad_rechazada': '0',
            'linea': 'Línea 1',
            'operador': 'Operador',
        }
        response = client.post('/nuevo', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert 'debe ser mayor a cero' in response.data.decode('utf-8')

    def test_crear_registro_rechazada_mayor_producida(self, client):
        data = {
            'fecha': '2024-02-01',
            'turno': 'Noche',
            'producto': 'Producto Test',
            'lote': 'LOT-TEST-003',
            'cantidad_producida': '100',
            'unidad': 'kg',
            'cantidad_rechazada': '200',
            'linea': 'Línea 1',
            'operador': 'Operador',
        }
        response = client.post('/nuevo', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert 'no puede superar la cantidad producida' in response.data.decode('utf-8')

    def test_crear_registro_rechazada_negativa(self, client):
        data = {
            'fecha': '2024-02-01',
            'turno': 'Mañana',
            'producto': 'Producto Test',
            'lote': 'LOT-TEST-004',
            'cantidad_producida': '100',
            'unidad': 'kg',
            'cantidad_rechazada': '-5',
            'linea': 'Línea 1',
            'operador': 'Operador',
        }
        response = client.post('/nuevo', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert 'no puede ser negativa' in response.data.decode('utf-8')


class TestEditarRegistro:
    def test_get_formulario_editar(self, client, registro_ejemplo):
        response = client.get(f'/editar/{registro_ejemplo}')
        assert response.status_code == 200
        assert 'Editar Registro' in response.data.decode('utf-8')
        assert 'Polietileno PG-100' in response.data.decode('utf-8')

    def test_editar_registro_exitoso(self, client, registro_ejemplo):
        data = {
            'fecha': '2024-01-20',
            'turno': 'Tarde',
            'producto': 'Producto Editado',
            'lote': 'LOT-2024-002',
            'cantidad_producida': '800',
            'unidad': 'ton',
            'cantidad_rechazada': '0',
            'linea': 'Línea 2',
            'operador': 'Nuevo Operador',
        }
        response = client.post(f'/editar/{registro_ejemplo}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert 'actualizado exitosamente' in response.data.decode('utf-8')

    def test_editar_registro_no_existente(self, client):
        response = client.get('/editar/9999')
        assert response.status_code == 404


class TestEliminarRegistro:
    def test_eliminar_registro(self, client, registro_ejemplo):
        response = client.post(f'/eliminar/{registro_ejemplo}', follow_redirects=True)
        assert response.status_code == 200
        assert 'eliminado exitosamente' in response.data.decode('utf-8')

    def test_eliminar_registro_no_existente(self, client):
        response = client.post('/eliminar/9999')
        assert response.status_code == 404


class TestDetalleRegistro:
    def test_detalle_registro(self, client, registro_ejemplo):
        response = client.get(f'/detalle/{registro_ejemplo}')
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'Polietileno PG-100' in data
        assert 'LOT-2024-001' in data
        assert 'Juan García' in data

    def test_detalle_registro_no_existente(self, client):
        response = client.get('/detalle/9999')
        assert response.status_code == 404


class TestExportarCSV:
    def test_exportar_csv(self, client, registro_ejemplo):
        response = client.get('/exportar')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
        data = response.data.decode('utf-8-sig')
        assert 'Polietileno PG-100' in data
        assert 'LOT-2024-001' in data

    def test_exportar_csv_con_filtro(self, client, registro_ejemplo):
        response = client.get('/exportar?turno=Tarde')
        assert response.status_code == 200
        data = response.data.decode('utf-8-sig')
        assert 'Polietileno PG-100' not in data
