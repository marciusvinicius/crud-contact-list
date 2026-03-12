FROM nginx:latest

WORKDIR /app

COPY front/nginx.conf /etc/nginx/nginx.conf

COPY front/ /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]