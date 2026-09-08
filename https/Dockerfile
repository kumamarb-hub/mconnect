FROM nginx:alpine

RUN apk add --no-cache openssl

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY gen-cert.sh /gen-cert.sh
RUN chmod +x /gen-cert.sh

CMD ["/bin/sh", "/gen-cert.sh"]