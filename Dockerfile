FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
COPY backend backend
COPY models models
COPY knowledge knowledge
COPY results results
COPY samples samples
COPY frontend/dist frontend/dist
ENV DEFECTRAG_DEVICE=cpu
EXPOSE 8765
CMD ["python","-m","uvicorn","backend.main:app","--host","0.0.0.0","--port","8765"]
