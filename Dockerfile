FROM python:3.12-slim
RUN echo "hello"
CMD ["python", "-c", "print('hello world')"]
