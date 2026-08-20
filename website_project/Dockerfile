FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /website
COPY requirements.txt /website/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /website/
CMD ["gunicorn", "website_config.wsgi:application", "--bind", "0.0.0.0:8000"]
