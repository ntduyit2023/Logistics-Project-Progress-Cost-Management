FROM node:20-alpine

WORKDIR /app

# (Security & Optmization) Phân quyền cho thư mục app để user 'node' quản lý
# RUN chown -R node:node /app

# Chuyển xuống user 'node' thay vì 'root'
# USER node

# Copy các file cấu hình
COPY package*.json ./

# Cài đặt package
RUN npm install



# Copy toàn bộ mã nguồn
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
