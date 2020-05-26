from flask import Flask,render_template,request,jsonify,url_for                    
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.embed import file_html,json_item
import matplotlib.pyplot as plt
import random
import json                                                                        
import time
from os import remove
import numpy as np


app= Flask(__name__)

x=[]
y=[]
x_pred=[]
y_pred=[]

ecuacion=""

vectores=["Vector 1","Vector 2","Vector 3","Vector 4","Vector 5","Vector 6"] 
discretas_continuas=["Continua","Discreta"]
distribuciones=["Normal","Binomial","Poisson","Power"]

# 0 normal , 1 binomial , 2 poisson
distribucion=0

factor=1                                                                           
vector=1
discreta_continua=0
cantidad=1000
rand=100

@app.route('/')
def index():
    return render_template('index.html',vector=vector,vectores=vectores,discreta_continua=discreta_continua,discretas_continuas=discretas_continuas,factor=factor,distribuciones=distribuciones,distribucion=distribucion)

@app.route("/test" , methods=['GET', 'POST'])
def test():
    global vector
    global discreta_continua
    global factor
    global distribucion

    seleccionado = request.form.get('vector_select')
    seleccionado_variables=request.form.get('variable_select')
    seleccionado_factor=request.form.get('input_factor')
    seleccionado_distribucion=request.form.get('distribucion_select')

    vector=int(seleccionado)
    discreta_continua=int(seleccionado_variables)
    factor=int(seleccionado_factor)
    distribucion=int(seleccionado_distribucion)


    if(discreta_continua==0):
        factor=1
    elif(discreta_continua==1):
        factor=factor

    print("Factor--> ",factor)

    return render_template(
        'index.html',
         vectores=vectores,vector=vector,discreta_continua=discreta_continua,discretas_continuas=discretas_continuas,factor=factor,distribuciones=distribuciones,distribucion=distribucion)


@app.route('/plotpred')
def plotpred():
    global y_pred
    global ecuacion

    x_pred = np.array(x)
    y_pre = np.array(y)

    p4 = np.poly1d(np.polyfit(x_pred, y_pre, 1))

    ecuacion=str(p4)

    print("Predicción con factor de ",factor)
    print("tamaño x_pred: ",len(x_pred))
    xp = np.linspace(0, len(x_pred)-1, 1000*factor)

    y_pred=p4(xp)

    p = figure(title="Vector "+str(vector), x_axis_label='Tiempo', y_axis_label='Dato aleatorio',plot_height=400,plot_width=1000)
    p.scatter(x, y, legend_label="Datos reales", line_width=2,line_color="blue")
    p.line(x_pred,y_pred,legend_label="Predicción",line_width=3,line_color="red")
    return json.dumps(json_item(p, "myplot"))

@app.route('/plot')
def plot():

    crearDatos(factor,vector,cantidad)

    p = figure(title="Vector "+str(vector), x_axis_label='Tiempo', y_axis_label='Dato aleatorio',plot_height=400,plot_width=1000)
    p.scatter(x, y, legend_label="Datos reales", line_width=2,line_color="blue")
    return json.dumps(json_item(p, "myplot"))



@app.route('/manual')
def manual():
    return render_template('manual.html')

@app.route('/tabla')
def tabla():
    return render_template('tabla.html',x=x,y=y,vector=vector)

@app.route('/comparacion')
def comparacion():
    error=[]

    for i in range(0, len(y)):
        error.append( abs(y_pred[i]-y[i]) )

    error_total=sum(error)
    error_medio=error_total/len(y)
    print(error_medio)
    return render_template('comparacion.html',x=x,y=y,pred=y_pred,error=error_total,error_medio=error_medio,vector=vector,ecuacion=ecuacion)

from io import BytesIO
import base64
import matplotlib
@app.route('/estadistica')
def estadistica():

    maximo=max(y)
    minimo=min(y)

    
    promedio=sum(y)/len(y)
    desviacion=np.std(y)
    varianza=np.var(y)
    correlacion=np.corrcoef(y,x)[0][1]

    # print("Máximo: ",maximo)
    # print("Mínimo: ",minimo)
    # print("Promedio: ",promedio)
    # print("Desviaci<C3><B3>n: ",desviacion,)
    # print("Varianza: ",varianza)
    # print("Correlaci<C3><B3>n",correlacion)

    matplotlib.use('Agg')
    img = BytesIO()

    plt.figure(figsize=(10,6))
    plt.hist(y,bins=10,edgecolor="black")


    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    plt.savefig(img)
    img.seek(0)



    return render_template(
        'estadisticas.html', vector=vector,
        max="{:.2f}".format(maximo),min="{:.2f}".format(minimo),prom="{:.2f}".format(promedio),des="{:.2f}".format(desviacion),
        var="{:.2f}".format(varianza),cor="{:.2f}".format(correlacion),cant=cantidad,plot_url=plot_url)


def crearDatos(factor,vector,cantidad):
    global x
    global y

    from firebase import firebase
    firebase = firebase.FirebaseApplication('https://python-proyect-ad812.firebaseio.com/', None)

    result = firebase.get('/Vectores/Vector'+str(vector)+'/', '')
    #print(result)

    if result==None:
        data={"Nombre":"Vector"+str(vector)}

        if(distribucion==0):
            y = np.random.normal(loc=0.0,scale=1.0,size=1000)
            y=abs(y/max(y)*100)

        if(distribucion==1):
            y = np.random.binomial(100,0.2,1000)
            y=abs(y/max(y)*100)

        if(distribucion==2):
            y = np.random.poisson(10, 1000)
            y=abs(y/max(y)*100)

        if(distribucion==3):
            y = np.random.power(5, 1000)
            y=abs(y/max(y)*100)

        contador=0
        for i in np.arange(0,1000*factor,factor):
            # print(i,end=":")
            # print("Y:",y[contador],end=" ; ")
            data[str(i)]=y[contador]
            contador+=1

        # print(data)
        result = firebase.post('/Vectores/Vector'+str(vector),data)  
        # print(result) 

        # print("Ya hice post")
        result = firebase.get('/Vectores/Vector'+str(vector)+'/', '')
        # print("Result: ",result)
        # print(len(result))

        # print("Traje el result")


        keys=[]
        tiempo=[]
        valores=[]
        nombre=""

        if result!=None or len(result)<1:
            for i in result:
                keys.append(i)
                diccionario=result[str(i)]
                for key in diccionario:
                    if key!="Nombre":
                        tiempo.append(float(key))
                        valores.append(diccionario.get(key))
                        # print(str(float(key))+"-->"+str(diccionario.get(key)),end=" | ")
                    else:
                        nombre=diccionario.get(key)
        else:
            print("Resultado vacio")

        print()
        print("Nombre: ",nombre)
        # print("ID: ",keys)
        # print("Valores: ",valores)
        print("Cantidad de valores y etiquetas: ",len(valores)," ",len(tiempo))
        print("\n")
        # print("Etiquetas: ",tiempo)


        x=tiempo
        y=valores

        plotpred()

        # print("X->",x)
        # print("Y->",y)

    else:
        print("\n\nEl vector ",vector," ya est<C3><A1> lleno")
        from firebase import firebase
        firebase = firebase.FirebaseApplication('https://python-proyect-ad812.firebaseio.com/', None)
        firebase.delete('/Vectores/Vector'+str(vector)+'/','')
        print('deleted')
        crearDatos(factor,vector,cantidad)




if __name__ =='__main__':
    app.run('127.0.0.1', 5000, debug=True)