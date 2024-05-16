import psycopg2
from flask import Flask, jsonify, request,render_template,session,redirect,url_for
import os
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user,login_required,login_url
from models import User 


app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.urandom(24)

# Conexión a la base de datos
conn = psycopg2.connect("postgres://proyecto_zu82_user:E1jOM8eQgfWK7ruNp7EhJkeyw2Bez0CJ@dpg-cp04rk21hbls73e44f2g-a.oregon-postgres.render.com/proyecto_zu82")




login_manager = LoginManager()
login_manager.init_app(app)



# Crear cursor para ejecutar sentencias SQL
cursor = conn.cursor()

@login_manager.user_loader
def load_user(user_id):
    # Busca el usuario en la base de datos con psycopg2
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    usuario = cursor.fetchone()
    session['usuario_nombre'] = usuario[1]
    session['usuario_email'] = usuario[2]
    session['mensaje_admin'] = ""
    user = User(usuario[0], usuario[1],usuario[2],usuario[3],usuario[4])
    login_user(user)
    return user
  


#ruta de inicio 
@app.route("/")
def get_inicio():
    # Verifica si las claves existen en la sesión antes de acceder a ellas
    usuario_nombre = session.get('usuario_nombre')
    usuario_email = session.get('usuario_email')
    user = current_user
     # Crea un diccionario con los datos del usuario (opcional)
    if usuario_nombre and usuario_email:
        usuario = user
    else :    
        usuario = False

    return render_template("index.html", usuario=usuario)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        admin = "no"

           # Validar datos (opcional)
        if nombre==" " or email=="" or password=="":
            mensaje_error = {'mensaje':"contraseña incorrecta"}
            return render_template('index.html',mensaje=mensaje_error);
   
        # Insertar usuario en la base de datos
        consulta = f"""
            INSERT INTO usuarios (nombre,correo_electronico,contrasena,admin) VALUES ('{nombre}', '{email}', '{password}','{admin}')
            RETURNING id;
        """
        cursor.execute( consulta)
        #guardar cambios
        conn.commit()

        # Obtener el ID del usuario recién creado
        #cursor.execute("SELECT LASTVAL()");
        usuario_id = cursor.fetchone()[0]

        #mandamos la ip a flask login
        load_user(usuario_id)

        # Iniciar sesión del usuario
        session['usuario_id'] = usuario_id

        # Redirigir a la página principal o la página del perfil
        return redirect("/")
    else:
        # Mostrar formulario de registro
        return render_template('index.html',mensaje=False)
    
@app.route('/iniciar', methods=['GET', 'POST'])
def iniciar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']

        usuario = f"""SELECT * FROM usuarios WHERE correo_electronico = '{email}' """
        cursor.execute(usuario)
        usuario_all = cursor.fetchone()

        if usuario_all :
            if usuario_all[3] == password :
                load_user(usuario_all[0])
            else :
                mensaje_error = {'mensaje':"la contraseña esta mal "}
                return render_template('index.html',mensaje=mensaje_error);

       
        return redirect("/")
    else:
        # Mostrar formulario de registro
        return render_template('login.html',mensaje=False)
    


    

@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    session['usuario_nombre']=""
    session['usuario_email']=""
    return redirect("/")



@app.route("/productos", methods=["GET"])
def mostrar_productos():

    nombre = request.args.get("nombre")
    precio = request.args.get("precio")
    categoria = request.args.get("categoria")
    stock = request.args.get("stock")
    if stock:
        stock = int(stock)

    consulta = "SELECT * FROM products WHERE "
    condiciones = []

    if nombre:
        condiciones.append(f"nombre LIKE '%{nombre}%'")

    if precio:
        condiciones.append(f"precio = {precio}")

    if categoria:
        condiciones.append(f"category = '{categoria}'")

    if stock:
        condiciones.append(f"stock = {stock}")

    if condiciones:
        consulta += " AND ".join(condiciones)
    else:
        consulta = "SELECT * FROM products"

    valores_filtro = tuple([valor for valor in (nombre, precio, categoria, stock) if valor])
    cursor.execute(consulta, valores_filtro) if condiciones else cursor.execute(consulta)

    productos = cursor.fetchall()

    return render_template("productos.html", productos=productos)

@app.route("/usuarios", methods=["GET"])
@login_required
def mostrar_usuarios():
    user = current_user
    if user.admin == "si" :
        session['mensaje_admin'] = "usuario eliminado"
        
        # Obtener los datos del formulario
        id_ = int(request.args.get("id_"))

        comprobar_usuario =f"""SELECT * FROM usuarios WHERE id ='{id_}'; """
        cursor.execute(comprobar_usuario)
        admin = cursor.fetchall()

        if admin[0][4] =="no":
            # Insertar el nuevo producto en la base de datos
            consulta = f"""
            DELETE FROM usuarios WHERE id ='{id_}';
            """
            cursor.execute(consulta)

        
        # Guardar los cambios en la base de datos
            conn.commit()

            #mensaje afirmativo
            session['mensaje_admin'] = "usuario eliminado"
            return redirect("/admin")
        else :
            session['mensaje_admin'] = "no puedes borrar a un usario que es admin"
            return redirect("/admin")
        
     
    else :
        return render_template("error_admin.html")


#producto por id
@app.route("/producto/<int:producto_id>", methods=["GET"])
def mostrar_productosid(producto_id):
    # Consultar todos los productos de la base de datos
    #cursor.execute("SELECT * FROM products WHERE id = %s",(str(producto_id)))
    consulta = F"""SELECT * FROM products WHERE id = {producto_id}"""
    cursor.execute(consulta)
    producto = cursor.fetchall()

    # Renderizar la plantilla HTML con la lista de productos
    #return jsonify(productos)
    return render_template("producto.html",producto=producto)

table_definition = """
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) ,
  price DECIMAL(10,2),
  description TEXT,
  category VARCHAR(255),
  stock INTEGER NOT NULL
);
"""


#guardar producto
@app.route("/guardar_producto", methods=["POST"])
def guardar_producto():
    # Obtener los datos del formulario
    nombre = request.form["nombre"]
    precio = float(request.form["precio"])
    descripcion = request.form["descripcion"]
    category = request.form["category"]
    stock = int(request.form["stock"])

    # Insertar el nuevo producto en la base de datos
    consulta = f"""
    INSERT INTO products (name,price,description,category,stock) VALUES ('{nombre}','{precio}','{descripcion}','{category}','{stock}');
    """
    cursor.execute(consulta)

    
    # Guardar los cambios en la base de datos
    conn.commit()
    #cursor.lastrowid
    respuesta = {'mensaje': 'producto guardado'}
    return redirect("/admin")

#guardar producto
@app.route("/elminar_producto", methods=["GET"])
@login_required
def elimina_producto():
    user = current_user
    if user.admin == "si" :
        session['mensaje_admin'] = "producto eliminado"
        # Obtener los datos del formulario
        id_ = request.args.get("id_")

        # Insertar el nuevo producto en la base de datos
        consulta = f"""
        DELETE FROM products WHERE id ='{id_}';
        """
        cursor.execute(consulta)

        
        # Guardar los cambios en la base de datos
        conn.commit()
        return redirect("/admin")
        
        """ respuesta = {'mensaje': 'producto eliminado'}
        return render_template("admin.html",mensaje=respuesta) """
    else :
        return render_template("error_admin.html")


@app.route("/editar_producto", methods=["POST"])
def editar_producto():
    # Obtener el ID del producto del formulario
    producto_id = int(request.form.get("producto_id"))

    # Obtener los datos actualizados del producto del formulario
    nombre = request.form.get("nombre")
    precio = request.form.get("precio")
    descripcion = request.form.get("descripcion")
    category = request.form.get("category")
    stock = request.form.get("stock")
    id
    

    # Preparar la consulta SQL para actualizar
    consulta = f"""
        UPDATE products
        SET 
    """

    valores_actualizados = []

    if nombre:
        valores_actualizados.append(f"nombre LIKE '%{nombre}%'")

    if precio:
        valores_actualizados.append(f"precio = {precio}")
    
    if descripcion:
        valores_actualizados.append(f"precio = {descripcion}")

    if category:
        valores_actualizados.append(f"category = '{category}'")

    if stock:
        valores_actualizados.append(f"stock = {stock}")


    # Completar la consulta SQL
    consulta += f" WHERE id = {producto_id}"

    # Ejecutar la consulta SQL y guardar los cambios
    cursor.execute(consulta, valores_actualizados)
  


#carrito
@app.route("/carrito", methods=["GET"])
@login_required
def mostrar_carrito():
    user = current_user
    usuario_id = session.get('usuario_id')
    consulta = f"""SELECT c.id,c.cantidad,c.product_id ,p.name ,p.price , p.description,p.category, p.stock FROM carrito AS c JOIN products AS p ON c.product_id = p.id WHERE c.user_id={user.id} """
    #WHERE user_id = {user.id}
    
    cursor.execute(consulta)
    productos = cursor.fetchall()

 

    return render_template("carrito.html", productos=productos)
    #return jsonify(producto)
    #return jsonify(productos)

@app.route("/carrito_eliminar/<int:producto_id>", methods=["GET"])
@login_required
def eliminar_carrito(producto_id):
    consulta = f""" DELETE FROM carrito WHERE id = '{producto_id}' """

    
    cursor.execute(consulta)

    # Guardar los cambios en la base de datos
    conn.commit()

    mensaje = {'mensaje':"producto eliminado"}


    return render_template("carrito.html", mensaje=mensaje)
    #return jsonify(usuarios)

@app.route("/carrito_aumentar", methods=["GET"])
@login_required
def aumentar_carrito():
    user = current_user
    cantidad = request.args.get("cantidad")
    consulta = f"""
    UPDATE carrito
    SET cantidad = {cantidad}
    WHERE id = {user.id}
    """

    
    cursor.execute(consulta)

    # Guardar los cambios en la base de datos
    conn.commit()

    mensaje = {'mensaje':"producto eliminado"}

    return redirect("/carrito")
    #return render_template("carrito.html", mensaje=mensaje)
    #return jsonify(usuarios)

@app.route("/añadir_carrito", methods=["GET"])
@login_required
def añadir_carrito():
    user = current_user
    product_id = request.args.get("product_id")
    cantidad = request.args.get("cantidad")
    confi = f"""
    SELECT * FROM carrito WHERE product_id={product_id};
    """
    cursor.execute(confi)
    confipro = cursor.fetchall()
    if confipro :
        ruta=f"/carrito_aumentar?cantidad={cantidad}"
        return redirect(ruta)
    else:    
        consulta = f"""
        INSERT INTO carrito (user_id,product_id,cantidad) VALUES ('{user.id}','{product_id}','{cantidad}');
        """
        cursor.execute(consulta)

        # Guardar los cambios en la base de datos
        conn.commit()

        mensaje = {'mensaje':"producto agregados"}


        return redirect("/carrito")
        #return jsonify(mensaje)

#admin
@app.route("/admin", methods=["GET"])
@login_required
def admin():
    user = current_user
    if user.admin == "si" :
        mensaje = session.get('mensaje_admin')
        #buscamos usuarios
        consulta = "SELECT * FROM usuarios"
        cursor.execute(consulta)
        usuarios = cursor.fetchall()
        #buscamos productos
        consulta2 = "SELECT * FROM products"
        cursor.execute(consulta2)
        productos = cursor.fetchall()
        # Guardar los cambios en la base de datos
        conn.commit()

        datos = {
            'usuarios':usuarios,
            'productos':productos ,
            'mensaje':  mensaje             
        }

        return render_template("admin.html", datos=datos )



def status_401(error):
    return render_template("error_admin.html" )



#carrito
if __name__ == '__main__':
    app.register_error_handler(401,status_401)
    app.run(debug=True)  # Set debug=False for production