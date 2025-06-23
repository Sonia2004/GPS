# Usa una imagen base oficial de Python
FROM python:3.9-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de requisitos
COPY requirements.txt requirements.txt

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación al directorio de trabajo
COPY . .

# Expone el puerto en el que correrá la aplicación
EXPOSE 5000

# Define la variable de entorno para que Flask se ejecute en modo producción
ENV FLASK_ENV=production

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
