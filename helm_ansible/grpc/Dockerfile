FROM --platform=linux/amd64  python:3.10


COPY ansible.cfg /etc/ansible/ansible.cfg
RUN touch /var/log/ansible.log && \
    chmod 666 /var/log/ansible.log
WORKDIR /app/EE
COPY / .
RUN apt-get update
RUN pip install -r osm_ee/requirements.txt

RUN mkdir -p /app/storage/

EXPOSE 8000

CMD [ "bash", "-c", "while true; do sh start.sh ; sleep 5; done" ]
