FROM node:20-alpine

WORKDIR /app

ARG BACKEND_API_URL=http://127.0.0.1:8000
ENV BACKEND_API_URL=$BACKEND_API_URL

COPY package.json pnpm-lock.yaml ./

RUN npm install -g pnpm && pnpm install --frozen-lockfile

COPY . .

RUN pnpm build

CMD ["npx", "next", "start", "-H", "0.0.0.0", "-p", "3000"]
