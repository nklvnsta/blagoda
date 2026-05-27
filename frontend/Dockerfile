FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./

RUN npm install

COPY frontend/ .

EXPOSE 3000

CMD ["sh", "-c", "npm run build && npm run preview -- --host 0.0.0.0 --port 3000"]