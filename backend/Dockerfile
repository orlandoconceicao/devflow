FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system devflow && adduser --system --ingroup devflow devflow
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=devflow:devflow . .
RUN mkdir -p /app/staticfiles /app/media && chown -R devflow:devflow /app
USER devflow
EXPOSE 8000
CMD ["daphne","-b","0.0.0.0","-p","8000","config.asgi:application"]
