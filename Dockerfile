FROM python:3.8-alpine
RUN apk --update add \
	bash \
	nano \
	gcc \
	python3-dev \
        musl-dev \
	jpeg-dev \
	zlib-dev \
	libffi-dev \
	cairo-dev \
	pango-dev \
	gdk-pixbuf-dev
ENV STATIC_URL /static
ENV STATIC_PATH /static
COPY requirements.txt /
COPY . /dailyread
WORKDIR /dailyread
RUN pip3 install -r requirements.txt
CMD ["gunicorn", "-w","3", "-b", "0.0.0.0:8000", "wsgi:app"]
