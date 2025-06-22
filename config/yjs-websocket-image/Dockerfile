FROM node:20.17-alpine AS build

RUN npm install -g @y/websocket-server

ENV HOST=0.0.0.0
ENV PORT=1234

EXPOSE 1234

CMD [ "npx", "y-websocket" ]
