FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

# install dependencies
WORKDIR /app
COPY ./app /app/app
COPY requirements.txt /tmp
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /tmp/requirements.txt

# launch server
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8888"]