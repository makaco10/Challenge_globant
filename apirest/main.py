import asyncio
import datetime

import tornado.web
import peewee
import csv


# Crear estructura de la base de datos
database = peewee.SqliteDatabase('api.db')  # De momento usamos sqlite, acá se puede elegir otros motores como psql


# Modelos ORM para la base
class BaseModel(peewee.Model):
    class Meta:
        database = database


# Cada modelo representa una tabla con sus campos
class Jobs(BaseModel):
    job_id = peewee.PrimaryKeyField()
    job_name = peewee.CharField(max_length=255)


class Departments(BaseModel):
    dept_id = peewee.PrimaryKeyField()
    dept_name = peewee.CharField(max_length=255)


class Employee(BaseModel):
    employee_id = peewee.PrimaryKeyField()
    employee_name = peewee.CharField(max_length=255)
    employee_hired = peewee.DateTimeField()
    employee_dept = peewee.ForeignKeyField(Departments, backref='department_employees')
    employee_job = peewee.ForeignKeyField(Jobs, backref='job_employees')


# Crear la estructura
database.create_tables([Jobs, Departments, Employee], safe=True)

# Cargamos la base de datos con los csv de departments y jobs
departments_dict = []
with open('departments.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        try:
            Departments.get(Departments.dept_id == int(row[0]))
        except peewee.DoesNotExist:
            departments_dict.append({'dept_id': int(row[0]), 'dept_name': row[1]})

jobs_dict = []
with open('jobs.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        try:
            Jobs.get(Jobs.job_id == int(row[0]))
        except peewee.DoesNotExist:
            jobs_dict.append({'job_id': int(row[0]), 'job_name': row[1]})

with database.atomic():
    Departments.insert_many(departments_dict).execute()
    Jobs.insert_many(jobs_dict).execute()


# Codigo de la API
class IndexHandler(tornado.web.RequestHandler):  # Index, formulario de carga
    def get(self):
        self.render('index.html')


# Codigo de la carga csv
class ImportHandler(tornado.web.RequestHandler):
    def post(self):
        skip = self.get_argument('skip', default=False)  # Omitir registros existentes
        count = 0
        result = {'total': 0, 'error': [], 'logged': []}

        csv_file = self.request.files['csvfile'][0]['body']  # Cargamos el archivo que se sube
        with open('uploads/csvfile.csv', 'wb') as f:  # Lo guardamos en la carpeta uploads
            f.write(csv_file)
        with open('uploads/csvfile.csv', 'r') as f:  # Se carga el archivo de forma local
            reader = csv.reader(f)  # Con la librería de csv
            for row in reader:  # Hacemos un loop por cada registro

                if(count == 1000):  # Procesar un maximo de 1000 registros
                    break

                # Campos de Employee sacados del csv
                e_id = row[0]
                e_name = row[1]
                e_datetime = row[2]
                e_department = row[3]
                e_job = row[4]
                # Chequear si algún campo está vacío
                if(e_id == ''):
                    result['error'].append({'row': count, 'error': 'Employee ID is empty'})
                    result['logged'].append(row)
                    continue
                if(e_name == ''):
                    result['error'].append({'row': count, 'error': 'Employee Name is empty'})
                    result['logged'].append(row)
                    continue
                if(e_datetime == ''):
                    result['error'].append({'row': count, 'error': 'Employee Hired time is empty'})
                    result['logged'].append(row)
                    continue
                if(e_department == ''):
                    result['error'].append({'row': count, 'error': 'Employee Department is empty'})
                    result['logged'].append(row)
                    continue
                if(e_job == ''):
                    result['error'].append({'row': count, 'error': 'Employee Job is empty'})
                    result['logged'].append(row)
                    continue
                # Si todos los campos están llenos, pasamos a cargar el registro
                # chequear id
                existe = Employee.select().where(Employee.employee_id == int(e_id)).exists()
                if(existe):
                    if(skip):  # Si ya existe el id pero pusimos omitir, simplemente pasamos al siguiente registro
                        continue
                    else:  # Si no estaba chequeado, generamos un error
                        result['error'].append({'row': count, 'error': f'Employee {e_id} already exists'})
                        result['logged'].append(row)
                        continue
                # chequear name
                if('_' in e_name):
                    result['error'].append({'row': count, 'error': f'Invalid characters in employee name {e_name}'})
                    result['logged'].append(row)
                    continue
                # chequear datetime
                # formato 2021-06-02T12:21:45Z < sin la Z
                if(e_datetime.endswith('Z')):
                    e_datetime = e_datetime[:-1]  # Quitar la ultima letra (Z)
                try:
                    datetime_hired = datetime.datetime.fromisoformat(e_datetime)
                except ValueError:
                    result['error'].append({'row': count, 'error': f'Invalid Datetime Format {e_datetime}'})
                    result['logged'].append(row)
                    continue

                #chequear department
                if(not Departments.select().where(Departments.dept_id == int(e_department)).exists()):
                    result['error'].append({'row': count, 'error': f'Department ID {e_department} does not exists.'})
                    result['logged'].append(row)
                    continue

                # chequear job
                if (not Jobs.select().where(Jobs.job_id == int(e_job)).exists()):
                    result['error'].append({'row': count, 'error': f'Job ID {e_job} does not exists.'})
                    result['logged'].append(row)
                    continue

                # Los campos están bien, procedo a guardar el registro
                dept_object = Departments.get(Departments.dept_id == int(e_department))
                jobs_object = Jobs.get(Jobs.job_id == int(e_job))
                Employee.create(
                    employee_id=int(e_id),
                    employee_name=e_name,
                    employee_hired=datetime_hired,
                    employee_dept=dept_object,
                    employee_job=jobs_object).save()
                result['total'] += 1
                count += 1

        self.write(result)


def make_app():
    return tornado.web.Application([
        (r"/", IndexHandler),
        (r"/import", ImportHandler),

    ], debug=True, cookie_secret='asdkjasd', static_path='static', template_path='templates')


async def main():
    app = make_app()
    app.listen(8888, '0.0.0.0')
    print('Escuchando en http://localhost:8888')
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
