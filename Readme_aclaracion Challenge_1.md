

Se desarrollo una API REST  para la carga de unos registros desde un archivo plano en formato csv, desarrollando una interfaz simple.

![image-20230105103953724](/imagenes/1.png)



la carga destino seria en una Base de datos de pruebas SQLlite.

Vista SQLlite

datos Departments

![image-20230105103953724](/imagenes/2.png)



datos de la tabla Jobs

![image-20230105103953724](/imagenes/3.png)





datos cargados en Employee

![image-20230105103953724](/imagenes/4.png)



Nuestro Dictionary rules no permite ingresar registro con datos nulos



![image-20230105103953724](/imagenes/5.png)



​	Lote transaccional seria hasta de 1000 rows por vez, por request

![image-20230105103953724](/imagenes/6.png)





Conclusiones



- Tornado para la api y el index de Interfaz para operar
- Se carga un csv en /import
- Las Tablas jobs, departaments, employees  y su schema ya esta definido en nuestra base de datos de destino (Como Prueba)

Import funciona de la siguiente manera.

/import <- acepta archivos csv


El sistema carga hasta 1000 registros y se detiene
devuelve un json
{
 total: archivos cargados int
 error: [
    {renglon int:  error str}
 ]
 logged: [
    str renglon que no se pudo cargar
 ]
}

Solo carga los primero 1000, para cargar el restante, se vuelve a cargar el mismo csv, pero con la diferencia que esta vez solo cargar la diferencia, no cargara los que anteriormente fueron cargados.



