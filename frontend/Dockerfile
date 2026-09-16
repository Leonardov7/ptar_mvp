# Etapa 1: Construcción
FROM node:20-alpine as build-stage

WORKDIR /app

# Copiar configuración de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar código fuente
COPY . .

# Compilar la aplicación para producción
RUN npm run build

# Etapa 2: Servidor de Producción
FROM nginx:stable-alpine as production-stage

# Copiar los archivos compilados de Vue al directorio de Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copiar configuración personalizada de Nginx (opcional, para manejar el enrutamiento SPA)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]