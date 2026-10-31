FROM node:24-slim AS dependencies

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

FROM dependencies AS build
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:stable-alpine AS production
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
USER nginx
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]

FROM dependencies AS development
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
